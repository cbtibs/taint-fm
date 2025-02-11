import logging
import yt_dlp
import discord
import asyncio
from discord.ext import commands

logger = logging.getLogger(__name__)

flat_extractor_options = {
    'format': 'bestaudio/best',
    'extract_flat': 'in_playlist',  # Only retrieve basic info for playlist entries
    'ignoreerrors': True,           # Skip over bad/unavailable videos
    'nocheckcertificate': True,
    'restrictfilenames': True,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'noplaylist': False,            # Allows playlist extraction
}
flat_ytdl = yt_dlp.YoutubeDL(flat_extractor_options)

stream_extractor_options = {
    'format': 'bestaudio/best',
    'ignoreerrors': True,
    'nocheckcertificate': True,
    'restrictfilenames': True,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}
stream_ytdl = yt_dlp.YoutubeDL(stream_extractor_options)

ffmpeg_options = {
    'options': '-vn'
}

class YouTubeAudioSource(discord.PCMVolumeTransformer):
    """
    A helper class that wraps an FFMpeg audio source with YouTube data.
    """
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source,volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
    
class YouTubeAudioCog(commands.Cog):
    """A cog that provides YouTube audio playback functionality"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.music_queue = [] # A list to hold queued YouTubeAudioSource objects.
        self.play_lock = asyncio.Lock() # Prevents conrrucent play_next calls.

    @commands.command(name='join', help='Joins your voice channel.')
    async def join(self, ctx: commands.Context):
        logger.info(f"{ctx.author} requested join in {ctx.guild.name}.")
        if ctx.author.voice is None:
            return await ctx.send("You are not connected to a voice channel.")
        channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await channel.connect()
            await ctx.send(f"Joined **{channel.name}**.")
        else:
            await ctx.voice_client.move_to(channel)
            await ctx.send(f"Moved to **{channel.name}**.")

    @commands.command(name='leave', help='Leaves the voice channel')
    async def leave(self, ctx: commands.Context):
        logger.info(f"{ctx.author} requested leave in {ctx.guild.name}.")
        if ctx.voice_client.channel:
            channel = ctx.voice_client.channel
            await ctx.voice_client.disconnect()
            await ctx.send(f"Disconnected from {channel}")
        else:
            await ctx.send("I'm not in a voice channel.")

    @commands.command(name='play', help='Loads a playlist or single video (flat) and queues it for incremental playing.')
    async def play(self, ctx: commands.Context, *, url: str):
        if not ctx.author.voice:
            return await ctx.send("You are not connected to a voice channel!")
        if ctx.voice_client is None:
            await ctx.invoke(self.join)

        async with ctx.typing():
            # Use the "flat" extractor to quickly gather video entries from the playlist
            data = await ctx.bot.loop.run_in_executor(None, lambda: flat_ytdl.extract_info(url, download=False))

        # If it's a single video, we won't have 'entries', so wrap data in a list
        entries = data.get('entries')
        if not entries:
            entries = [data]

        # Filter out None entries in case some items failed extraction
        entries = [e for e in entries if e is not None]

        count = 0
        for entry in entries:
            # Each entry is minimal info like 'id', 'title', 'webpage_url'
            self.music_queue.append(entry)
            count += 1

        if count == 1:
            title = entries[0].get('title', 'Unknown Title')
            await ctx.send(f"Added **{title}** to the queue.")
        else:
            await ctx.send(f"Added **{count}** items to the queue.")

        # If nothing is playing, start the next item
        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)

    async def play_next(self, ctx: commands.Context):
        """Plays the next item in the queue by doing a full extraction on demand."""
        async with self.play_lock:
            if not self.music_queue:
                await ctx.send("Queue is empty. Leaving the voice channel.")
                return await ctx.voice_client.disconnect()

            next_entry = self.music_queue.pop(0)

            # Try to get the watch page URL; if missing, construct it from 'id'
            webpage_url = next_entry.get('webpage_url')
            if not webpage_url:
                video_id = next_entry.get('id')
                if video_id:
                    webpage_url = f"https://www.youtube.com/watch?v={video_id}"
                else:
                    logger.error("No webpage_url or id found for next_entry. Skipping.")
                    return await self.play_next(ctx)

            # Extract full info to get the actual streaming URL
            full_info = await ctx.bot.loop.run_in_executor(
                None, lambda: stream_ytdl.extract_info(webpage_url, download=False)
            )

            if not full_info or 'url' not in full_info:
                logger.error(f"Failed to retrieve streaming URL for {webpage_url}. Skipping.")
                return await self.play_next(ctx)

            # Create the playable source
            source = discord.FFmpegPCMAudio(full_info['url'], **ffmpeg_options)
            yt_source = YouTubeAudioSource(source, data=full_info)

            # Play it
            ctx.voice_client.play(
                yt_source,
                after=lambda e: self.bot.loop.create_task(self.play_next(ctx))
                if e is None else logger.error(f"Player error: {e}")
            )
            await ctx.send(f"Now playing: **{yt_source.title}**")


    @commands.command(name='skip', help='Skips the current song.')
    async def skip(self, ctx: commands.Context):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("Skipped the current song.")
        else:
            await ctx.send("No song is currently playing.")

    @commands.command(name='queue', help='Shows the current music queue.')
    async def queue_info(self, ctx: commands.Context):
        if not self.music_queue:
            return await ctx.send("The queue is empty.")

        lines = []
        for i, entry in enumerate(self.music_queue, start=1):
            title = entry.get('title', 'Unknown Title')
            line = f"{i}. {title}"
            if sum(len(l) for l in lines) + len(line) > 1900:
                lines.append(f"...and {len(self.music_queue) - i + 1} more.")
                break
            lines.append(line)

        message = "\n".join(lines)
        await ctx.send(f"**Queue:**\n{message}")

    @commands.command(name='clear', help='Clears the current music queue.')
    async def clear(self, ctx: commands.Context):
        if not self.music_queue:
            return await ctx.send("The queue is already empty.")
        else:
            self.music_queue.clear
            await ctx.send("Clearing the queue.")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(YouTubeAudioCog(bot))
