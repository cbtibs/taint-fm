"""Entry point for the Discord bot
This module intializes the bot, loads the cogs, and runs the bot.
"""

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

COMMAND_PREFIX ="!"
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

@bot.event
async def on_ready() -> None:
    """Event triggered when the bost has successfully connected to Discord."""
    print(f'Loggin in as {bot.user} and ready to serve')

def load_cogs() -> None:
    """Loads all cogs"""
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and not filename.startswith("__"):
            cog_name = f"cogs.{filename[:-3]}"
            try:
                bot.load_extension(cog_name)
                print(f"Loaded cog: {cog_name}")
            except Exception as e:
                print(f"Failed to load cog {cog_name}: {e}")

if __name__ == "__main__":
    load_cogs()
    bot.run(TOKEN)
