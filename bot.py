"""
Battle Buddies Budget League Discord Bot

A Discord bot for managing MTG Budget League information stored in Google Sheets.
"""

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Create bot instance with required intents
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)


@bot.event
async def on_ready():
    """Event handler for when the bot is ready and connected."""
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guild(s)')
    
    # Sync slash commands with Discord
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Failed to sync commands: {e}')


async def load_extensions():
    """Load all cog extensions."""
    await bot.load_extension('cogs.standings')
    await bot.load_extension('cogs.players')
    await bot.load_extension('cogs.games')


async def main():
    """Main entry point for the bot."""
    async with bot:
        await load_extensions()
        await bot.start(DISCORD_TOKEN)


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
