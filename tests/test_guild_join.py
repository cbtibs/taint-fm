"""Unit tests for the GuildJoinCog."""

import pytest
from unittest.mock import AsyncMock, MagicMock
import discord
from cogs.guild_join import get_welcome_channel, GuildJoinCog


class DummyPermissions:
    """Mocks Discord permissions for sending messages."""

    def __init__(self, send_messages: bool) -> None:
        """
        Initializes the DummyPermissions instance.

        Args:
            send_messages (bool): Whether the user can send messages.
        """
        self.send_messages = send_messages


class DummyTextChannel:
    """Mocks a Discord text channel."""

    def __init__(self, name: str, send_permission: bool) -> None:
        """
        Initializes the DummyTextChannel instance.

        Args:
            name (str): The name of the text channel.
            send_permission (bool): Whether the bot can send messages.
        """
        self.name = name
        self._send_permission = send_permission
        self.send = AsyncMock()
        self.id = 1  # Simulating a channel ID.

    def permissions_for(self, member: discord.Member) -> DummyPermissions:
        """
        Returns the permissions for the given member.

        Args:
            member (discord.Member): The Discord member.

        Returns:
            DummyPermissions: Permissions for the member.
        """
        return DummyPermissions(self._send_permission)


class DummyGuild:
    """Mocks a Discord guild (server)."""

    def __init__(self, system_channel, text_channels, me) -> None:
        """
        Initializes the DummyGuild instance.

        Args:
            system_channel (DummyTextChannel or None): The system channel.
            text_channels (list): A list of text channels in the guild.
            me (DummyMember): The bot's member representation.
        """
        self.system_channel = system_channel
        self.text_channels = text_channels
        self.me = me
        self.name = "DummyGuild"
        self.id = 12345


class DummyMember:
    """Mocks a Discord member."""
    pass


@pytest.fixture
def dummy_member() -> DummyMember:
    """Provides a dummy member instance."""
    return DummyMember()


@pytest.fixture
def dummy_bot() -> MagicMock:
    """Provides a mocked bot instance."""
    return MagicMock()


def test_get_welcome_channel_with_system_channel(dummy_member: DummyMember) -> None:
    """Tests that the system channel is prioritized when available."""
    dummy_system_channel = DummyTextChannel("system-channel", send_permission=False)
    dummy_text_channel = DummyTextChannel("general", send_permission=True)
    guild = DummyGuild(
        system_channel=dummy_system_channel,
        text_channels=[dummy_text_channel],
        me=dummy_member
    )

    channel = get_welcome_channel(guild, dummy_member)

    assert channel == dummy_system_channel


def test_get_welcome_channel_without_system_channel(dummy_member: DummyMember) -> None:
    """Tests that the first text channel with send permission is chosen
    if no system channel exists.
    """
    dummy_text_channel1 = DummyTextChannel("general", send_permission=False)
    dummy_text_channel2 = DummyTextChannel("chat", send_permission=True)
    guild = DummyGuild(
        system_channel=None,
        text_channels=[dummy_text_channel1, dummy_text_channel2],
        me=dummy_member
    )

    channel = get_welcome_channel(guild, dummy_member)

    assert channel == dummy_text_channel2


def test_get_welcome_channel_no_valid_channel(dummy_member: DummyMember) -> None:
    """Tests that None is returned if no text channel allows sending messages."""
    dummy_text_channel = DummyTextChannel("general", send_permission=False)
    guild = DummyGuild(
        system_channel=None,
        text_channels=[dummy_text_channel],
        me=dummy_member
    )

    channel = get_welcome_channel(guild, dummy_member)

    assert channel is None


@pytest.mark.asyncio
async def test_on_guild_join_with_system_channel(
    dummy_bot: MagicMock, dummy_member: DummyMember
) -> None:
    """Tests that on_guild_join sends a welcome message using the system
    channel if it exists.
    """
    system_channel = DummyTextChannel("system-channel", send_permission=True)
    guild = DummyGuild(
        system_channel=system_channel,
        text_channels=[],
        me=dummy_member
    )
    cog = GuildJoinCog(dummy_bot)

    await cog.on_guild_join(guild)

    system_channel.send.assert_awaited_once_with("Hello everyone!")


@pytest.mark.asyncio
async def test_on_guild_join_without_system_channel(
    dummy_bot: MagicMock, dummy_member: DummyMember
) -> None:
    """Tests that on_guild_join sends a welcome message using the fallback
    text channel if no system channel exists.
    """
    fallback_channel = DummyTextChannel("general", send_permission=True)
    guild = DummyGuild(
        system_channel=None,
        text_channels=[fallback_channel],
        me=dummy_member
    )
    cog = GuildJoinCog(dummy_bot)

    await cog.on_guild_join(guild)

    fallback_channel.send.assert_awaited_once_with("Hello everyone!")


@pytest.mark.asyncio
async def test_on_guild_join_no_valid_channel(
    dummy_bot: MagicMock, dummy_member: DummyMember
) -> None:
    """Tests that on_guild_join does not attempt to send a message
    if no channel is valid.
    """
    fallback_channel = DummyTextChannel("general", send_permission=False)
    guild = DummyGuild(
        system_channel=None,
        text_channels=[fallback_channel],
        me=dummy_member
    )
    cog = GuildJoinCog(dummy_bot)

    await cog.on_guild_join(guild)

    fallback_channel.send.assert_not_awaited()
