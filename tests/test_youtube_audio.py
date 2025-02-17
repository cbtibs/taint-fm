"""Unit tests for the YouTubeAudioCog.

This suite tests key user workflows (join, leave, skip, play, queue, clear, and cog unload)
using the __call__ pattern. External calls (extraction and download) are patched to simulate
successful operations.
"""

import asyncio
import contextlib
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from discord.ext import commands

pytestmark = pytest.mark.asyncio(loop_scope="session")

from cogs.youtube_audio import YouTubeAudioCog


class DummyContext:
    """Mocks a Discord command context for testing.

    Attributes:
        bot (commands.Bot): The bot instance.
        author (MagicMock): The command author.
        voice_client (object): The bot's voice client (may be None or a DummyVoiceClient).
        guild (MagicMock): The guild context.
        send (AsyncMock): Mock for sending messages.
        invoke (AsyncMock): Mock for invoking commands.
    """
    def __init__(self, bot=None, author=None, voice_client=None, guild=None):
        self.bot = bot or MagicMock(spec=commands.Bot)
        self.author = author or MagicMock()
        self.voice_client = voice_client  # May be None or a DummyVoiceClient.
        self.guild = guild or MagicMock()
        self.send = AsyncMock()
        self.invoke = AsyncMock()

    @contextlib.asynccontextmanager
    async def typing(self):
        """Simulates the async context manager for ctx.typing()."""
        yield


class DummyVoiceChannel:
    """Mocks a Discord voice channel for testing."""
    def __init__(self, name):
        self.name = name
        self.connect = AsyncMock()
        self.move_to = AsyncMock()


class DummyVoiceClient:
    """Mocks a Discord voice client for testing."""
    def __init__(self, channel=None):
        self.channel = channel or DummyVoiceChannel("DefaultChannel")
        self.disconnect = AsyncMock()
        self.stop = MagicMock()
        self.play = MagicMock()
        self.is_playing_mock = False

    def is_playing(self):
        return self.is_playing_mock


@pytest.fixture
def dummy_bot(event_loop):
    """Provides a mocked commands.Bot using the provided event loop.

    Args:
        event_loop (asyncio.AbstractEventLoop): The event loop provided by pytest-asyncio.

    Returns:
        MagicMock: A mocked bot with bot.loop set.
    """
    bot = MagicMock(spec=commands.Bot)
    bot.loop = event_loop
    return bot


@pytest.fixture
def dummy_context(dummy_bot):
    """Creates a DummyContext with a mocked bot and a DummyVoiceClient.

    Args:
        dummy_bot (commands.Bot): A mocked bot instance.

    Returns:
        DummyContext: The dummy command context.
    """
    vc = DummyVoiceClient(channel=DummyVoiceChannel("TestChannel"))
    return DummyContext(bot=dummy_bot, guild=MagicMock(), voice_client=vc)


# --------------------- Join Command Tests ---------------------

@pytest.mark.asyncio
async def test_join_user_not_in_voice(dummy_bot):
    """Tests that join_command reports when the user is not in a voice channel."""
    cog = YouTubeAudioCog(dummy_bot)
    ctx = DummyContext(bot=dummy_bot)
    ctx.author.voice = None
    await YouTubeAudioCog.join_command.__call__(cog, ctx)
    ctx.send.assert_awaited_once_with("You are not connected to a voice channel.")


@pytest.mark.asyncio
async def test_join_bot_not_in_voice(dummy_bot):
    """Tests that join_command connects the bot if not already in voice."""
    cog = YouTubeAudioCog(dummy_bot)
    channel = DummyVoiceChannel("UserChannel")
    ctx = DummyContext(bot=dummy_bot, voice_client=None)
    ctx.author.voice = MagicMock(channel=channel)
    channel.connect = AsyncMock()
    await YouTubeAudioCog.join_command.__call__(cog, ctx)
    channel.connect.assert_awaited_once()
    ctx.send.assert_awaited_once_with("Joined **UserChannel**.")


@pytest.mark.asyncio
async def test_join_bot_already_in_voice(dummy_bot):
    """Tests that join_command moves the bot if already connected to voice."""
    cog = YouTubeAudioCog(dummy_bot)
    new_channel = DummyVoiceChannel("NewChannel")
    ctx = DummyContext(bot=dummy_bot)
    ctx.author.voice = MagicMock(channel=new_channel)
    fake_vc = DummyVoiceClient()
    fake_vc.move_to = AsyncMock()
    ctx.voice_client = fake_vc
    await YouTubeAudioCog.join_command.__call__(cog, ctx)
    fake_vc.move_to.assert_awaited_once_with(new_channel)
    ctx.send.assert_awaited_once_with("Moved to **NewChannel**.")


# --------------------- Leave Command Tests ---------------------

@pytest.mark.asyncio
async def test_leave_bot_not_in_voice(dummy_bot):
    """Tests that leave_command reports when the bot is not in a voice channel."""
    cog = YouTubeAudioCog(dummy_bot)
    ctx = DummyContext(bot=dummy_bot, voice_client=None)
    await YouTubeAudioCog.leave_command.__call__(cog, ctx)
    ctx.send.assert_awaited_once_with("I'm not in a voice channel.")


@pytest.mark.asyncio
async def test_leave_bot_in_voice(dummy_bot):
    """Tests that leave_command disconnects the bot from a voice channel."""
    cog = YouTubeAudioCog(dummy_bot)
    vc = DummyVoiceClient(channel=DummyVoiceChannel("TestChannel"))
    ctx = DummyContext(bot=dummy_bot, voice_client=vc)
    await YouTubeAudioCog.leave_command.__call__(cog, ctx)
    vc.disconnect.assert_awaited_once()
    msg = ctx.send.call_args[0][0]
    assert "Disconnected from" in msg


# --------------------- Skip Command Tests ---------------------

@pytest.mark.asyncio
async def test_skip_no_song_playing(dummy_bot):
    """Tests that skip_command does nothing if no song is playing."""
    cog = YouTubeAudioCog(dummy_bot)
    vc = DummyVoiceClient()
    vc.is_playing_mock = False
    ctx = DummyContext(bot=dummy_bot, voice_client=vc)
    await YouTubeAudioCog.skip_command.__call__(cog, ctx)
    ctx.send.assert_awaited_once_with("No song is currently playing.")
    vc.stop.assert_not_called()


@pytest.mark.asyncio
async def test_skip_song_playing(dummy_bot):
    """Tests that skip_command stops playback if a song is playing."""
    cog = YouTubeAudioCog(dummy_bot)
    vc = DummyVoiceClient()
    vc.is_playing_mock = True
    ctx = DummyContext(bot=dummy_bot, voice_client=vc)
    await YouTubeAudioCog.skip_command.__call__(cog, ctx)
    ctx.send.assert_awaited_once_with("Skipped the current song.")
    vc.stop.assert_called_once()


# --------------------- Play Command Tests ---------------------

@pytest.mark.asyncio
async def test_play_user_not_in_voice(dummy_bot):
    """Tests that play_command reports when the user is not in a voice channel."""
    cog = YouTubeAudioCog(dummy_bot)
    ctx = DummyContext(bot=dummy_bot)
    ctx.author.voice = None
    await YouTubeAudioCog.play_command.__call__(cog, ctx, url="some_url")
    ctx.send.assert_awaited_once_with("You are not connected to a voice channel!")


@pytest.mark.asyncio
async def test_play_single_track(dummy_bot):
    """Tests that play_command queues a single track successfully."""
    cog = YouTubeAudioCog(dummy_bot)
    channel = DummyVoiceChannel("UserChannel")
    vc = DummyVoiceClient(channel=DummyVoiceChannel("TestChannel"))
    ctx = DummyContext(bot=dummy_bot, voice_client=vc)
    ctx.author.voice = MagicMock(channel=channel)
    with patch.object(
        cog.extractor, 'extract_playlist_info',
        return_value={"title": "SongTitle"}
    ):
        with patch.object(
            cog.extractor, 'download_audio_file',
            return_value="/tmp/fakepath-SongTitle.webm"
        ):
            await YouTubeAudioCog.play_command.__call__(cog, ctx, url="some_url")
    ctx.send.assert_any_await("Added **SongTitle** to the queue.")


@pytest.mark.asyncio
async def test_play_multiple_tracks(dummy_bot):
    """Tests that play_command queues multiple tracks from a playlist."""
    cog = YouTubeAudioCog(dummy_bot)
    channel = DummyVoiceChannel("UserChannel")
    vc = DummyVoiceClient(channel=DummyVoiceChannel("TestChannel"))
    ctx = DummyContext(bot=dummy_bot, voice_client=vc)
    ctx.author.voice = MagicMock(channel=channel)
    mock_data = {
        "entries": [
            {"title": "Song1", "webpage_url": "https://example.com/1"},
            {"title": "Song2", "webpage_url": "https://example.com/2"},
        ]
    }
    with patch.object(
        cog.extractor, 'extract_playlist_info',
        return_value=mock_data
    ):
        with patch.object(
            cog.extractor, 'download_audio_file',
            return_value="/tmp/fakepath-song.webm"
        ):
            await YouTubeAudioCog.play_command.__call__(cog, ctx, url="playlist_url")
    ctx.send.assert_any_await("Added **2** items to the queue.")


@pytest.mark.asyncio
async def test_play_extractor_failure(dummy_bot):
    """Tests that play_command handles extractor errors gracefully."""
    cog = YouTubeAudioCog(dummy_bot)
    channel = DummyVoiceChannel("UserChannel")
    vc = DummyVoiceClient(channel=DummyVoiceChannel("TestChannel"))
    ctx = DummyContext(bot=dummy_bot, voice_client=vc)
    ctx.author.voice = MagicMock(channel=channel)
    with patch.object(
        cog.extractor, 'extract_playlist_info',
        side_effect=Exception("Extraction error")
    ):
        await YouTubeAudioCog.play_command.__call__(cog, ctx, url="some_url")
    ctx.send.assert_awaited_once_with("There was a problem extracting info from YouTube.")


# --------------------- Queue and Clear Command Tests ---------------------

@pytest.mark.asyncio
async def test_queue_info_command_empty(dummy_bot):
    """Tests that queue_info_command reports an empty queue."""
    cog = YouTubeAudioCog(dummy_bot)
    ctx = DummyContext(bot=dummy_bot)
    await YouTubeAudioCog.queue_info_command.__call__(cog, ctx)
    ctx.send.assert_awaited_once_with("The queue is empty.")


@pytest.mark.asyncio
async def test_queue_info_command_nonempty(dummy_bot):
    """Tests that queue_info_command lists the queued track titles."""
    cog = YouTubeAudioCog(dummy_bot)
    cog.queue.add_multiple([MagicMock(title="Song1"), MagicMock(title="Song2")])
    ctx = DummyContext(bot=dummy_bot)
    await YouTubeAudioCog.queue_info_command.__call__(cog, ctx)
    sent_msgs = [args[0][0] for args in ctx.send.call_args_list]
    assert any("Song1" in msg for msg in sent_msgs)
    assert any("Song2" in msg for msg in sent_msgs)


@pytest.mark.asyncio
async def test_clear_command_empty(dummy_bot):
    """Tests that clear_command reports when the queue is already empty."""
    cog = YouTubeAudioCog(dummy_bot)
    ctx = DummyContext(bot=dummy_bot)
    await YouTubeAudioCog.clear_command.__call__(cog, ctx)
    ctx.send.assert_awaited_once_with("The queue is already empty.")


@pytest.mark.asyncio
async def test_clear_command_nonempty(dummy_bot):
    """Tests that clear_command clears a nonempty queue."""
    cog = YouTubeAudioCog(dummy_bot)
    cog.queue.add_multiple([MagicMock(title="Song1"), MagicMock(title="Song2")])
    ctx = DummyContext(bot=dummy_bot)
    await YouTubeAudioCog.clear_command.__call__(cog, ctx)
    ctx.send.assert_awaited_once_with("Clearing the queue.")
    assert cog.queue.is_empty()


# --------------------- _play_next and Cog Unload Tests ---------------------

@pytest.mark.asyncio
async def test_play_next_leaves_if_empty(dummy_bot):
    """Tests that _play_next disconnects if the queue is empty."""
    cog = YouTubeAudioCog(dummy_bot)
    ctx = DummyContext(bot=dummy_bot, voice_client=DummyVoiceClient(channel=DummyVoiceChannel("TestChannel")))
    await cog._play_next(ctx)
    ctx.send.assert_awaited_once_with("Queue is empty. Leaving the voice channel.")
    ctx.voice_client.disconnect.assert_awaited_once()


@pytest.mark.asyncio
async def test_cog_unload_cleanup(dummy_bot):
    """Tests that cog_unload removes leftover downloaded files."""
    cog = YouTubeAudioCog(dummy_bot)
    # Simulate leftover file paths.
    cog.created_files.update({"/tmp/taint-fm-file1.webm", "/tmp/taint-fm-file2.webm"})
    with patch("os.remove") as mock_remove:
        await cog.cog_unload()
        assert mock_remove.call_count == 2
        assert len(cog.created_files) == 0
