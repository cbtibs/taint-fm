"""Tests for the guild_join cog."""

import pytest
from unittest.mock import MagicMock
import discord
from cogs.guild_join import get_welcome_channel

class DummyPermissions:
    def __init__(self, send_messages: bool):
        self.send_messages = send_messages

class DummyTextChannel:
    def __init__(self, name: str, send_permission: bool):
        self.name = name
        self._send_permission = send_permission

    def permissions_for(self, member: discord.Member) -> DummyPermissions:
        return DummyPermissions(self._send_permission)

class DummyGuild:
    def __init__(self, system_channel, text_channels, me):
        self.system_channel = system_channel
        self.text_channels = text_channels
        self.me = me

class DummyMember:
    pass

def test_get_welcome_channel_with_system_channel():
    """Test that the system channel is prioritized when available."""
    dummy_member = DummyMember()
    dummy_system_channel = DummyTextChannel("system-channel", send_permission=False)
    # Even if the system channel doesn't have send permission, it should be used if defined.
    dummy_text_channel = DummyTextChannel("general", send_permission=True)
    guild = DummyGuild(system_channel=dummy_system_channel,
                       text_channels=[dummy_text_channel],
                       me=dummy_member)
    channel = get_welcome_channel(guild, dummy_member)
    assert channel == dummy_system_channel

def test_get_welcome_channel_without_system_channel():
    """Test that the first text channel with send permission is chosen if no system channel exists."""
    dummy_member = DummyMember()
    dummy_text_channel1 = DummyTextChannel("general", send_permission=False)
    dummy_text_channel2 = DummyTextChannel("chat", send_permission=True)
    guild = DummyGuild(system_channel=None,
                       text_channels=[dummy_text_channel1, dummy_text_channel2],
                       me=dummy_member)
    channel = get_welcome_channel(guild, dummy_member)
    assert channel == dummy_text_channel2

def test_get_welcome_channel_no_valid_channel():
    """Test that None is returned if no text channel allows sending messages."""
    dummy_member = DummyMember()
    dummy_text_channel = DummyTextChannel("general", send_permission=False)
    guild = DummyGuild(system_channel=None,
                       text_channels=[dummy_text_channel],
                       me=dummy_member)
    channel = get_welcome_channel(guild, dummy_member)
    assert channel is None
