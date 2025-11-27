import sys
import os
import asyncio
from unittest.mock import MagicMock, AsyncMock
import discord
from discord.ext import commands

# Add current directory to path
sys.path.append(os.getcwd())

async def main():
    try:
        # Import the cog
        from cogs.utility_cog import UtilityCog
        
        # Setup mock bot using MagicMock
        bot = MagicMock()
        bot.wait_until_ready = AsyncMock()
        
        # Mock cogs and commands structure
        mock_cog = MagicMock()
        mock_command = MagicMock()
        mock_command.name = "test_command"
        mock_command.aliases = ["test"]
        mock_command.help = "Test help"
        mock_command.hidden = False
        mock_cog.get_commands.return_value = [mock_command]
        
        # Setup bot.cogs dictionary
        bot.cogs = {
            "TestCog": mock_cog,
            "AICog": mock_cog,
            "VoiceCog": mock_cog
        }
        
        # Instantiate utility cog
        cog = UtilityCog(bot)
        
        # Mock context with AsyncMock for send
        ctx = MagicMock()
        ctx.send = AsyncMock()
        
        # Run help command
        print("Running help command...")
        await cog.help_command.callback(cog, ctx)
        print("Help command executed successfully")
        
        # Check what was sent
        args, kwargs = ctx.send.call_args
        embed = kwargs.get('embed') or args[0]
        print(f"Embed title: {embed.title}")
        print(f"Embed fields: {len(embed.fields)}")
        for field in embed.fields:
            print(f"Field: {field.name}, Value length: {len(field.value)}")
            
    except Exception as e:
        print(f"Error caught: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
