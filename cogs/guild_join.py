"""Cog for handling actions when the bot joins a new guild."""

import discord
import logging
from discord.ext import commands
from typing import Optional

logger = logging.getLogger(__name__)

def get_welcome_channel(
    guild: discord.Guild, bot_member: discord.Member
) -> Optional[discord.TextChannel]:
    """Finds a suitable welcome channel in the given guild.

    Args:
        guild (discord.Guild): The guild to search for a welcome channel.
        bot_member (discord.Member): The bot's member representation.

    Returns:
        Optional[discord.TextChannel]: The best available text channel.
    """
    logger.debug(
        "Searching for welcome channel in guild: %s (ID: %d)", guild.name, guild.id
    )
    channel = guild.system_channel
    if channel:
        logger.debug("Using system channel: %s (ID: %d)", channel.name, channel.id)
    else:
        for text_channel in guild.text_channels:
            if text_channel.permissions_for(bot_member).send_messages:
                channel = text_channel
                logger.debug(
                    "Found text channel: %s (ID: %d)", channel.name, channel.id
                )
                break
    if channel is None:
        logger.debug("No suitable channel found in guild: %s (ID: %d)", guild.name, guild.id)
    return channel

class GuildJoinCog(commands.Cog):
    """Cog that listens for the on_guild_join event and sends a welcome message."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initializes the GuildJoinCog instance.

        Args:
            bot (commands.Bot): The Discord bot instance.
        """
        self.bot = bot
        logger.info("GuildJoinCog has been loaded.")

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Handles the event when the bot joins a new guild.

        Args:
            guild (discord.Guild): The guild the bot has joined.
        """
        logger.info("Joined new guild: %s (ID: %d)", guild.name, guild.id)
        channel = get_welcome_channel(guild, guild.me)
        if channel is not None:
            try:
                await channel.send("Hello everyone!")
                logger.info(
                    "Sent welcome message in channel: %s (ID: %d) in guild: %s (ID: %d)",
                    channel.name, channel.id, guild.name, guild.id
                )
            except Exception as e:
                logger.exception(
                    "Failed to send welcome message in channel: %s (ID: %d) in guild: %s (ID: %d): %s",
                    channel.name, channel.id, guild.name, guild.id, e
                )
        else:
            logger.warning(
                "Could not find a channel to send a message in guild: %s (ID: %d)",
                guild.name, guild.id
            )

async def setup(bot: commands.Bot) -> None:
    """Sets up the GuildJoinCog by adding it to the bot.

    Args:
        bot (commands.Bot): The Discord bot instance.
    """
    logger.info("Setting up GuildJoinCog.")
    await bot.add_cog(GuildJoinCog(bot))
