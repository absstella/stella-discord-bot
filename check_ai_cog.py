import sys
import os
import traceback
import asyncio
from unittest.mock import MagicMock

# Add current directory to path
sys.path.append(os.getcwd())

# Mock discord and other dependencies if needed
import discord
from discord.ext import commands

async def main():
    try:
        print("Attempting to import AICog...")
        from cogs.ai_cog import AICog
        print("Import successful")
        
        print("Attempting to instantiate AICog...")
        # Use MagicMock for the bot to avoid property setter issues
        bot = MagicMock()
        bot.db_manager = None
        bot.user.id = 123456789
        
        cog = AICog(bot)
        print("Instantiation successful")
        
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
