"""Custom audio source wrapper classes for the bot."""

import discord


class YouTubeAudioSource(discord.PCMVolumeTransformer):
    """Wraps an FFmpegPCMAudio source with metadata for a YouTube track."""

    def __init__(self, source: discord.FFmpegPCMAudio, *, data: dict, volume: float = 0.5):
        """Initializes a YouTubeAudioSource.

        Args:
            source (discord.FFmpegPCMAudio): The underlying PCM audio source.
            data (dict): The metadata dictionary from yt-dlp, containing the 'url' key.
            volume (float): Playback volume from 0.0 to 1.0. Defaults to 0.5.
        """
        super().__init__(source, volume)
        self.data = data
        self.title = data.get("title")
        self.url = data.get("url")
