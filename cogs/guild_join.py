"""Cog for handling actions when the bot joins a new guild."""

import discord
from discord.ext import commands
from typing import Optional

def get_welcome_channel(guild: discord.Guild, bot_member: discord.Member) -> Optional[discord.TextChannel]:
    """
    Determines the best channel to send a welcome message when the bot joins a guild.
    
    The function tries the guild's system channel. If that's not available,
    it falls back to the first text channel where the bot has permission to send messsages.
    
    Args:
        guild (discord.Guild): The guild the bot has joined
        bot_member (discord.Member): The bot's member instance in the guild.

    Returns:
        Optional[discord.TextChannel]: A channel where the welcome message can be sent,
        or None if no suitabel channel is found.
    """
    channel = guild.system_channel
    if channel is None:
        for text_channel in guild.text_channels:
            if text_channel.permissions_for(bot_member).send_messages:
                channel = text_channel
                break
    return channel

class GuildJoinCog(commands.Cog):
    """
    Cog that listens for the on_guild_join event and sends a welcome message.
    """

    def __init__(self, bot: commands.Bot) -> None:
        """
        Initializes the cog with the bot instance.

        Args:
            bot (commands.Bot): The bot instance.
        """
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        """
        Event listener that triggers when the bot joins a new guild.

        It attempts to send a welcome message in an appropriate channel.
        """
        channel = get_welcome_channel(guild, guild.me)
        if channel is not None:
            await channel.send("Hello everyone!")
        else:
            print(f"Could not find a channel to send a message in {guild.name}")

def setup(bot: commands.Bot) -> None:
    """
    Sets up the cog.

    This function is used by discord.py to load the cog.

    Args:
        bot (commands.Bot): The bot instance.
    """

    bot.add_cog(GuildJoinCog(bot))
