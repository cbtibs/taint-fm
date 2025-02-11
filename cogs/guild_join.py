"""Cog for handling actions when the bot joins a new guild."""

import discord
import logging
from discord.ext import commands
from typing import Optional

logger = logging.getLogger(__name__)

def get_welcome_channel(guild: discord.Guild, bot_member: discord.Member) -> Optional[discord.TextChannel]:
    logger.debug(f"Searching for welcome channel in guild: {guild.name} (ID: {guild.id})")
    channel = guild.system_channel
    if channel:
        logger.debug(f"Using system channel: {channel.name} (ID: {channel.id})")
    else:
        for text_channel in guild.text_channels:
            if text_channel.permissions_for(bot_member).send_messages:
                channel = text_channel
                logger.debug(f"Found text channel: {channel.name} (ID: {channel.id})")
                break
    if channel is None:
        logger.debug(f"No suitable channel found in guild: {guild.name} (ID: {guild.id})")
    return channel

class GuildJoinCog(commands.Cog):
    """Cog that listens for the on_guild_join event and sends a welcome message."""
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        logger.info("GuildJoinCog has been loaded.")

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        logger.info(f"Joined new guild: {guild.name} (ID: {guild.id})")
        channel = get_welcome_channel(guild, guild.me)
        if channel is not None:
            try:
                await channel.send("Hello everyone!")
                logger.info(
                    f"Sent welcome message in channel: {channel.name} (ID: {channel.id}) "
                    f"in guild: {guild.name} (ID: {guild.id})"
                )
            except Exception as e:
                logger.exception(
                    f"Failed to send welcome message in channel: {channel.name} (ID: {channel.id}) "
                    f"in guild: {guild.name} (ID: {guild.id}): {e}"
                )
        else:
            logger.warning(f"Could not find a channel to send a message in guild: {guild.name} (ID: {guild.id})")

async def setup(bot: commands.Bot) -> None:
    logger.info("Setting up GuildJoinCog.")
    await bot.add_cog(GuildJoinCog(bot))
