"""Main bot script for a Discord bot using the discord.ext.commands framework."""

import os
import discord
import logging
import asyncio
import coloredlogs
from discord.ext import commands
from dotenv import load_dotenv


# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN", "test-token")

# Set up logging
coloredlogs.install(
    level="INFO",
    fmt="%(asctime)s %(levelname)-8s %(name)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("bot")

# Bot configuration
COMMAND_PREFIX = "!"
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)


@bot.event
async def on_ready() -> None:
    """Handles the bot's ready event."""
    logger.info("Logged in as %s and ready to serve", bot.user)


async def load_cogs() -> None:
    """Asynchronously loads all cogs from the ./cogs directory."""
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and not filename.startswith("__"):
            cog_name = f"cogs.{filename[:-3]}"
            try:
                await bot.load_extension(cog_name)
                logger.info("Loaded cog: %s", cog_name)
            except Exception as e:
                logger.exception("Failed to load cog %s: %s", cog_name, e)


async def main() -> None:
    """Main entry point for running the bot."""
    await load_cogs()
    await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
