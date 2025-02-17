# cogs/youtube_audio_cog.py

import logging
import discord
import asyncio
import os

from discord.ext import commands

from utils.youtube_extractor import YouTubeExtractor
from utils.music_queue import MusicQueue, Track
from utils.audio_source import YouTubeAudioSource

logger = logging.getLogger(__name__)

FFMPEG_OPTIONS = {
    "options": "-vn"
}

class YouTubeAudioCog(commands.Cog):
    """A Discord Cog that provides YouTube audio playback by downloading files first.

    - Uses flat extraction for queue metadata.
    - Actually downloads the file when playing to avoid streaming issues.
    - Cleans up each file after playing, and also on cog unload.
    """

    def __init__(self, bot: commands.Bot) -> None:
        """Initializes the cog with a music queue and extractor.

        Args:
            bot (commands.Bot): The bot instance this cog is attached to.
        """
        self.bot = bot
        self.queue = MusicQueue()
        self.play_lock = asyncio.Lock()
        self.extractor = YouTubeExtractor()
        self.created_files = set()

    async def cog_unload(self):
        """Called automatically when this cog is unloaded.

        We use it to delete any leftover downloaded files if the bot shuts down or
        the cog is removed for any reason.
        """
        logger.info("Cog is unloading; removing any leftover downloaded files...")
        for file_path in list(self.created_files):
            try:
                os.remove(file_path)
                logger.info("Removed file on unload: %s", file_path)
            except OSError as e:
                logger.warning("Could not remove file %s: %s", file_path, e)
        self.created_files.clear()

    @commands.command(name="join", help="Joins the user's voice channel.")
    async def join_command(self, ctx: commands.Context) -> None:
        """Makes the bot join the user's current voice channel."""
        if ctx.author.voice is None:
            await ctx.send("You are not connected to a voice channel.")
            return

        channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await channel.connect()
            await ctx.send(f"Joined **{channel.name}**.")
        else:
            await ctx.voice_client.move_to(channel)
            await ctx.send(f"Moved to **{channel.name}**.")

    @commands.command(name="play", help="Queues a playlist or single video for playback.")
    async def play_command(self, ctx: commands.Context, *, url: str) -> None:
        """Queues the provided YouTube/playlist URL for playback."""
        if not ctx.author.voice:
            await ctx.send("You are not connected to a voice channel!")
            return

        if ctx.voice_client is None:
            await ctx.invoke(self.join_command)

        async with ctx.typing():
            try:
                data = await self.bot.loop.run_in_executor(
                    None, lambda: self.extractor.extract_playlist_info(url)
                )
            except Exception as e:
                logger.error("yt-dlp error: %s", e)
                await ctx.send("There was a problem extracting info from YouTube.")
                return

        entries = data.get("entries", []) or [data]
        valid_entries = [e for e in entries if e and e.get("title") != "[Deleted video]"]

        tracks = []
        for entry in valid_entries:
            webpage_url = entry.get("webpage_url") or f"https://www.youtube.com/watch?v={entry.get('id', '')}"
            track = Track(
                title=entry.get("title", "Unknown Title"),
                webpage_url=webpage_url,
                raw_data=entry
            )
            tracks.append(track)

        self.queue.add_multiple(tracks)
        count = len(tracks)
        if count == 1:
            await ctx.send(f"Added **{tracks[0].title}** to the queue.")
        else:
            await ctx.send(f"Added **{count}** items to the queue.")
 
        if not ctx.voice_client.is_playing():
            await self._play_next(ctx)

    async def _play_next(self, ctx: commands.Context) -> None:
        """Pops the next track from the queue, downloads it, and plays from a local file."""
        async with self.play_lock:
            if self.queue.is_empty():
                await ctx.send("Queue is empty. Leaving the voice channel.")
                await ctx.voice_client.disconnect()
                return

            next_track = self.queue.pop_next()
            if not next_track:
                return
            try:
                file_path = await self.bot.loop.run_in_executor(
                    None, lambda: self.extractor.download_audio_file(next_track.webpage_url)
                )
                # Keep track of it for potential cleanup if needed
                self.created_files.add(file_path)
            except Exception as e:
                logger.error("Failed to download file for %s: %s", next_track.webpage_url, e)
                await ctx.send(f"Failed to download {next_track.title}. Skipping...")
                return await self._play_next(ctx)

            audio_source = YouTubeAudioSource(
                discord.FFmpegPCMAudio(file_path, **FFMPEG_OPTIONS),
                data={
                    "title": next_track.title,
                    "url": next_track.webpage_url
                },
                volume=0.5
            )

            def after_playing(error: Exception) -> None:
                """Callback after the current track finishes or errors."""
                try:
                    os.remove(file_path)
                    self.created_files.discard(file_path)
                    logger.info("Removed file after playing: %s", file_path)
                except OSError as remove_err:
                    logger.warning("Could not remove temp file %s: %s", file_path, remove_err)

                if error:
                    logger.error("Player error: %s", error)

                coro = self._play_next(ctx)
                future = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
                try:
                    future.result()
                except Exception as exc:
                    logger.error("Error scheduling _play_next: %s", exc)

            ctx.voice_client.play(audio_source, after=after_playing)
            await ctx.send(f"Now playing: **{audio_source.title}**")

    @commands.command(name="skip", help="Skips the current song.")
    async def skip_command(self, ctx: commands.Context) -> None:
        """Skips the currently playing track if any."""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("Skipped the current song.")
        else:
            await ctx.send("No song is currently playing.")

    @commands.command(name="queue", help="Shows the queued songs.")
    async def queue_info_command(self, ctx: commands.Context) -> None:
        """Displays the titles of the tracks in the queue."""
        if self.queue.is_empty():
            await ctx.send("The queue is empty.")
            return

        lines = []
        for i, track in enumerate(self.queue, start=1):
            line = f"{i}. {track.title}"
            if sum(len(l) for l in lines) + len(line) > 1900:
                lines.append(f"...and {len(self.queue) - i + 1} more.")
                break
            lines.append(line)

        message = "\n".join(lines)
        await ctx.send(f"**Queue:**\n{message}")

    @commands.command(name="clear", help="Clears the music queue.")
    async def clear_command(self, ctx: commands.Context) -> None:
        """Clears all queued tracks."""
        if self.queue.is_empty():
            await ctx.send("The queue is already empty.")
            return
        self.queue.clear()
        await ctx.send("Clearing the queue.")

    @commands.command(name="leave", help="Leaves the voice channel.")
    async def leave_command(self, ctx: commands.Context) -> None:
        """Makes the bot leave the current voice channel."""
        if not ctx.voice_client:
            await ctx.send("I'm not in a voice channel.")
            return
        channel = ctx.voice_client.channel
        await ctx.voice_client.disconnect()
        await ctx.send(f"Disconnected from {channel}")


async def setup(bot: commands.Bot) -> None:
    """Adds the YouTubeAudioCog to the bot.

    Args:
        bot (commands.Bot): The Discord bot instance.
    """
    await bot.add_cog(YouTubeAudioCog(bot))
