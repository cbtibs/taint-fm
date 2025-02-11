import pytest
from unittest.mock import AsyncMock, MagicMock
import discord
from cogs.guild_join import get_welcome_channel, GuildJoinCog

# Dummy classes to simulate discord objects.
class DummyPermissions:
    def __init__(self, send_messages: bool):
        self.send_messages = send_messages

class DummyTextChannel:
    def __init__(self, name: str, send_permission: bool):
        self.name = name
        self._send_permission = send_permission
        # Use AsyncMock for the send method since it's awaited in the cog.
        self.send = AsyncMock()
        # To simulate channel IDs if needed.
        self.id = 1

    def permissions_for(self, member: discord.Member) -> DummyPermissions:
        return DummyPermissions(self._send_permission)

class DummyGuild:
    def __init__(self, system_channel, text_channels, me):
        self.system_channel = system_channel
        self.text_channels = text_channels
        self.me = me
        self.name = "DummyGuild"
        self.id = 12345

class DummyMember:
    pass

# Fixtures for dummy member and dummy bot.
@pytest.fixture
def dummy_member():
    return DummyMember()

@pytest.fixture
def dummy_bot():
    # The bot passed to the cog need not do anything special.
    return MagicMock()

def test_get_welcome_channel_with_system_channel(dummy_member):
    """Test that the system channel is prioritized when available."""
    dummy_system_channel = DummyTextChannel("system-channel", send_permission=False)
    dummy_text_channel = DummyTextChannel("general", send_permission=True)
    guild = DummyGuild(system_channel=dummy_system_channel,
                       text_channels=[dummy_text_channel],
                       me=dummy_member)
    channel = get_welcome_channel(guild, dummy_member)
    assert channel == dummy_system_channel

def test_get_welcome_channel_without_system_channel(dummy_member):
    """Test that the first text channel with send permission is chosen if no system channel exists."""
    dummy_text_channel1 = DummyTextChannel("general", send_permission=False)
    dummy_text_channel2 = DummyTextChannel("chat", send_permission=True)
    guild = DummyGuild(system_channel=None,
                       text_channels=[dummy_text_channel1, dummy_text_channel2],
                       me=dummy_member)
    channel = get_welcome_channel(guild, dummy_member)
    assert channel == dummy_text_channel2

def test_get_welcome_channel_no_valid_channel(dummy_member):
    """Test that None is returned if no text channel allows sending messages."""
    dummy_text_channel = DummyTextChannel("general", send_permission=False)
    guild = DummyGuild(system_channel=None,
                       text_channels=[dummy_text_channel],
                       me=dummy_member)
    channel = get_welcome_channel(guild, dummy_member)
    assert channel is None

# Tests for the actual GuildJoinCog event listener.
@pytest.mark.asyncio
async def test_on_guild_join_with_system_channel(dummy_bot, dummy_member):
    """
    Test that on_guild_join sends a welcome message using the system channel if it exists.
    """
    system_channel = DummyTextChannel("system-channel", send_permission=True)
    # Create a dummy guild with a system channel.
    guild = DummyGuild(system_channel=system_channel,
                       text_channels=[],
                       me=dummy_member)
    # Instantiate the cog.
    cog = GuildJoinCog(dummy_bot)
    # Call the event listener.
    await cog.on_guild_join(guild)
    # Verify that the system channel's send method was called with the welcome message.
    system_channel.send.assert_awaited_once_with("Hello everyone!")

@pytest.mark.asyncio
async def test_on_guild_join_without_system_channel(dummy_bot, dummy_member):
    """
    Test that on_guild_join sends a welcome message using the fallback text channel
    if no system channel exists.
    """
    fallback_channel = DummyTextChannel("general", send_permission=True)
    guild = DummyGuild(system_channel=None,
                       text_channels=[fallback_channel],
                       me=dummy_member)
    cog = GuildJoinCog(dummy_bot)
    await cog.on_guild_join(guild)
    fallback_channel.send.assert_awaited_once_with("Hello everyone!")

@pytest.mark.asyncio
async def test_on_guild_join_no_valid_channel(dummy_bot, dummy_member):
    """
    Test that on_guild_join does not attempt to send a message if no channel is valid.
    """
    fallback_channel = DummyTextChannel("general", send_permission=False)
    guild = DummyGuild(system_channel=None,
                       text_channels=[fallback_channel],
                       me=dummy_member)
    cog = GuildJoinCog(dummy_bot)
    await cog.on_guild_join(guild)
    fallback_channel.send.assert_not_awaited()
