import os
import discord
import logging
import asyncio
from discord.ext import commands
from dotenv import load_dotenv
from logging_config import setup_logging

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
setup_logging()
logger = logging.getLogger("bot")

COMMAND_PREFIX = "!"
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

@bot.event
async def on_ready() -> None:
    logger.info(f"Logged in as {bot.user} and ready to serve")

async def load_cogs() -> None:
    """Asynchronously load all cogs from the ./cogs directory."""
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and not filename.startswith("__"):
            cog_name = f"cogs.{filename[:-3]}"
            try:
                await bot.load_extension(cog_name)
                logger.info(f"Loaded cog: {cog_name}")
            except Exception as e:
                logger.exception(f"Failed to load cog {cog_name}: {e}")

async def main():
    await load_cogs()
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
