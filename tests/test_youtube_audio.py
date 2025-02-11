"""Unit tests for the YouTubeAudioCog."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from discord.ext import commands
from cogs.youtube_audio import YouTubeAudioCog

class DummyContext:
    """Mocks a Discord command context object."""

    def __init__(self, bot=None, author=None, voice_client=None, guild=None):
        """Initializes a dummy Discord context.

        Args:
            bot (commands.Bot, optional): The bot instance.
            author (MagicMock, optional): The user invoking the command.
            voice_client (MagicMock, optional): The bot's voice connection.
            guild (MagicMock, optional): The guild where the command runs.
        """
        self.bot = bot or MagicMock(spec=commands.Bot)
        self.author = author or MagicMock()
        self.voice_client = voice_client or None
        self.guild = guild or MagicMock()
        self.send = AsyncMock()
        self.invoke = AsyncMock()

    async def typing(self):
        """Simulates `ctx.typing()` as an async context manager."""

        class AsyncContextManager:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_value, traceback):
                pass

        return AsyncContextManager()

class DummyVoiceChannel:
    """Mocks a Discord voice channel."""

    def __init__(self, name):
        """Initializes a dummy voice channel.

        Args:
            name (str): The name of the voice channel.
        """
        self.name = name
        self.connect = AsyncMock()
        self.move_to = AsyncMock()

class DummyVoiceClient:
    """Mocks the bot's voice client."""

    def __init__(self, channel=None):
        """Initializes a dummy voice client.

        Args:
            channel (MagicMock, optional): The voice channel the bot is in.
        """
        self.channel = channel or MagicMock()
        self.disconnect = AsyncMock()
        self.stop = MagicMock()
        self.play = MagicMock()
        self.is_playing_mock = False

    def is_playing(self):
        """Returns whether the bot is currently playing audio."""
        return self.is_playing_mock

@pytest.fixture
def dummy_bot():
    """Provides a mocked bot instance."""
    return MagicMock(spec=commands.Bot)

@pytest.fixture
def youtube_audio_cog(dummy_bot):
    """Creates an instance of YouTubeAudioCog with a mocked bot."""
    return YouTubeAudioCog(dummy_bot)

@pytest.fixture
def dummy_context(dummy_bot):
    """Creates a mocked Discord command context."""
    return DummyContext(bot=dummy_bot, guild=MagicMock())

@pytest.mark.asyncio
async def test_join_user_not_in_voice(youtube_audio_cog, dummy_context):
    """Tests that the bot does not join when the user is not in a voice channel."""
    dummy_context.author.voice = None
    await YouTubeAudioCog.join.__call__(youtube_audio_cog, dummy_context)
    dummy_context.send.assert_awaited_once_with(
        "You are not connected to a voice channel."
    )

@pytest.mark.asyncio
async def test_join_bot_not_in_voice(youtube_audio_cog, dummy_context):
    """Tests that the bot joins the correct voice channel when not already in one."""
    dummy_context.author.voice = MagicMock(channel=DummyVoiceChannel("UserChannel"))
    dummy_context.voice_client = None
    await YouTubeAudioCog.join.__call__(youtube_audio_cog, dummy_context)
    dummy_context.send.assert_awaited_once_with("Joined **UserChannel**.")

@pytest.mark.asyncio
async def test_join_bot_already_in_voice(youtube_audio_cog, dummy_context):
    """Tests that the bot moves to a new voice channel if already in another one."""
    new_channel = DummyVoiceChannel("NewChannel")
    dummy_context.author.voice = MagicMock(channel=new_channel)
    fake_vc = DummyVoiceClient()
    fake_vc.move_to = AsyncMock()
    dummy_context.voice_client = fake_vc
    await YouTubeAudioCog.join.__call__(youtube_audio_cog, dummy_context)
    fake_vc.move_to.assert_awaited_once_with(new_channel)
    dummy_context.send.assert_awaited_once_with("Moved to **NewChannel**.")

@pytest.mark.asyncio
async def test_leave_bot_not_in_voice(youtube_audio_cog, dummy_context):
    """Tests that the bot does not leave if it is not in a voice channel."""
    dummy_context.voice_client = None
    await YouTubeAudioCog.leave.__call__(youtube_audio_cog, dummy_context)
    dummy_context.send.assert_awaited_once_with("I'm not in a voice channel.")

@pytest.mark.asyncio
async def test_leave_bot_in_voice(youtube_audio_cog, dummy_context):
    """Tests that the bot successfully disconnects from a voice channel."""
    fake_vc = DummyVoiceClient(channel=MagicMock())
    dummy_context.voice_client = fake_vc
    await YouTubeAudioCog.leave.__call__(youtube_audio_cog, dummy_context)
    fake_vc.disconnect.assert_awaited_once()
    msg = dummy_context.send.call_args[0][0]
    assert "Disconnected from" in msg

@pytest.mark.asyncio
async def test_skip_no_song_playing(youtube_audio_cog, dummy_context):
    """Tests that the bot does not skip if no song is playing."""
    fake_vc = DummyVoiceClient()
    fake_vc.is_playing_mock = False
    dummy_context.voice_client = fake_vc
    await YouTubeAudioCog.skip.__call__(youtube_audio_cog, dummy_context)
    dummy_context.send.assert_awaited_once_with("No song is currently playing.")
    fake_vc.stop.assert_not_called()

@pytest.mark.asyncio
async def test_skip_song_playing(youtube_audio_cog, dummy_context):
    """Tests that the bot successfully skips a currently playing song."""
    fake_vc = DummyVoiceClient()
    fake_vc.is_playing_mock = True
    dummy_context.voice_client = fake_vc
    await YouTubeAudioCog.skip.__call__(youtube_audio_cog, dummy_context)
    dummy_context.send.assert_awaited_once_with("Skipped the current song.")
    fake_vc.stop.assert_called_once()
