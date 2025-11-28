
import os
import asyncio
import logging
import signal
import time
import psutil
from typing import Set
from datetime import datetime # Added as per user's Code Edit snippet
from dotenv import load_dotenv
from keep_alive import keep_alive # Added as per user's instruction

# Load environment variables from .env file
load_dotenv()

# Keep Alive for Replit/Render # Added as per user's Code Edit snippet
keep_alive() # Added as per user's instruction

import discord
from discord.ext import commands, tasks
from database.connection import DatabaseManager
from utils.deduplication import DeduplicationManager

# Health check functionality moved to main_prod.py

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stella.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class StellaBot(commands.Bot):
    """
    S.T.E.L.L.A. - Smart Team Enhancement & Leisure Learning Assistant
    A comprehensive Discord bot with AI, music, gaming, and team management features.
    """
    
    def __init__(self):
        # Configure intents (basic setup without privileged intents)
        intents = discord.Intents.default()
        intents.message_content = True  # Required for text commands with prefix
        intents.voice_states = True
        intents.guilds = True
        intents.guild_messages = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None,  # We'll implement our own
            case_insensitive=True
        )
        
        # Database manager
        self.db_manager = None
        
        # Google Drive manager
        self.drive_manager = None
    
    def _register_slash_commands(self):
        """Register slash commands after loading cogs"""
        logger.info("Skipping duplicate slash command registration - using hybrid commands")

    async def setup_hook(self):
        """Initialize the bot components"""
        try:
            # Initialize database
            self.db_manager = DatabaseManager()
            await self.db_manager.initialize()
            logger.info("Database initialized successfully")
            
            # Initialize Google Drive manager
            from utils.google_drive_manager import GoogleDriveManager
            self.drive_manager = GoogleDriveManager()
            await self.drive_manager.initialize()
            if self.drive_manager.initialized:
                logger.info("Google Drive manager initialized successfully")
            else:
                logger.warning("Google Drive manager failed to initialize")
            
            # Load cogs
            cogs_to_load = [
                'cogs.ai_cog',
                'cogs.profile_cog',
                'cogs.knowledge_cog',
                'cogs.utility_cog',
                'cogs.voice_cog',
                'cogs.image_gen_cog',
                'cogs.minecraft_cog',
                'cogs.reaction_cog',
                'cogs.code_executor_cog',
                'cogs.admin_cog',
                'cogs.glitch_cog',
                'cogs.riddle_cog',
                # 'cogs.openai_cog',
                # 'cogs.image_cog',
                # 'cogs.entertainment_cog',
                # 'cogs.schedule_cog',
                # 'cogs.translation_cog',
                # 'cogs.summary_cog',
                # 'cogs.automation_cog',
                # 'cogs.realtime_cog',
                # 'cogs.file_sharing_cog',
                # 'cogs.speech_pattern_cog',
                # 'cogs.voice_recognition_cog',
                # 'cogs.discord_voice_integration_cog'
            ]
            
            for cog in cogs_to_load:
                try:
                    await self.load_extension(cog)
                    logger.info(f"Loaded cog: {cog}")
                    
                    # Set Google Drive manager for AI cog
                    if cog == 'cogs.ai_cog' and hasattr(self, 'drive_manager'):
                        ai_cog = self.get_cog('AICog')
                        if ai_cog:
                            ai_cog.google_drive = self.drive_manager
                            logger.info("Connected Google Drive manager to AI cog")
                            
                except Exception as e:
                    logger.error(f"Failed to load cog {cog}: {e}")
            
            # Hybrid commands automatically register with command tree
            logger.info("Hybrid commands loaded and ready for sync")
            
            logger.info("S.T.E.L.L.A. setup completed successfully")
            
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            raise

    async def on_ready(self):
        """Called when the bot is ready"""
        logger.info(f"{self.user} is now online!")
        logger.info(f"Connected to {len(self.guilds)} guilds")
        
        # Try guild-specific sync to bypass global rate limits
        synced_guilds = 0
        for guild in self.guilds:
            try:
                logger.info(f"Syncing slash commands for guild: {guild.name}")
                # Copy global commands to guild for instant availability
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                logger.info(f"Successfully synced {len(synced)} commands to {guild.name}")
                synced_guilds += 1
            except discord.HTTPException as e:
                if e.status == 429:
                    logger.warning(f"Rate limited for guild {guild.name}")
                else:
                    logger.error(f"Guild sync error for {guild.name}: {e}")
            except Exception as e:
                logger.error(f"Guild sync failed for {guild.name}: {e}")
        
        if synced_guilds == 0:
            # Fallback to global sync if no guild sync succeeded
            try:
                logger.info("Attempting global sync as fallback...")
                synced = await self.tree.sync()
                logger.info(f"Global sync successful: {len(synced)} commands")
            except discord.HTTPException as e:
                if e.status == 429:
                    logger.warning("Rate limited - slash commands will sync automatically later")
                else:
                    logger.error(f"Global sync error: {e}")
            except Exception as e:
                logger.error(f"Global sync failed: {e}")
        else:
            logger.info(f"Guild-specific sync completed for {synced_guilds} guilds")
        
        logger.info("All commands ready for use")
        
        # Set bot activity to reflect enhanced memory features
        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name="/ask | Enhanced Memory & Conversation"
        )
        await self.change_presence(activity=activity)

    async def on_message(self, message):
        """Handle incoming messages"""
        if message.author.bot:
            return
        
        # Log message for debugging
        logger.info(f"Message received from {message.author}: mentions={len(message.mentions)}, content='{message.content}'")
        
        # Process text commands starting with !
        if message.content.startswith('!'):
            await self.process_commands(message)
            return
        
        # Check if bot is mentioned
        if self.user in message.mentions:
            logger.info(f"Bot mentioned by {message.author}, content: '{message.content}'")
            
            try:
                # Check if we can read message content
                if not message.content or message.content.strip() == "":
                    logger.warning("Cannot read message content - missing intent")
                    await message.reply("メッセージ内容を読み取れません。Discord Developer Portalで「Message Content Intent」を有効にするか、スラッシュコマンド `/ask` を使用してください。")
                    return
                
                # Remove the mention and treat as AI question
                content = message.content
                for mention in message.mentions:
                    if mention == self.user:
                        content = content.replace(f'<@{mention.id}>', '').replace(f'<@!{mention.id}>', '').strip()
                
                logger.info(f"Processing mention with content: '{content}'")
                
                if content:  # If there's content after removing mentions
                    # Get the AI cog and call ask_ai directly
                    ai_cog = self.get_cog('AICog')
                    logger.info(f"AI cog found: {ai_cog is not None}")
                    if ai_cog and hasattr(ai_cog, 'ask_ai'):
                        logger.info("Calling ask_ai method")
                        # Create context for the command
                        ctx = await self.get_context(message)
                        await ai_cog.ask_ai(ctx, question=content)
                        return
                    else:
                        logger.error(f"AI cog not found or ask_ai method missing. Cog: {ai_cog}, has_ask_ai: {hasattr(ai_cog, 'ask_ai') if ai_cog else False}")
                        await message.reply("AI機能が利用できません。")
                else:
                    await message.reply("質問内容を含めてメンションしてください。例: @STELLA こんにちは")
                    
            except Exception as e:
                logger.error(f"Error handling mention: {e}", exc_info=True)
                await message.reply("エラーが発生しました。スラッシュコマンド `/ask` をお試しください。")
            
        await self.process_commands(message)

    async def on_command(self, ctx):
        """Called before command execution"""
        logger.info(f"Command executed: {ctx.command} by {ctx.author} in {ctx.guild}")

    async def on_command_error(self, ctx, error):
        """Global error handler"""
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: `{error.param}`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Invalid argument provided: {error}")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command.")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ I don't have the required permissions to execute this command.")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏰ Command is on cooldown. Try again in {error.retry_after:.2f} seconds.")
        else:
            logger.error(f"Unhandled error in command {ctx.command}: {error}")
            await ctx.send("❌ An unexpected error occurred. Please try again later.")



    async def close(self):
        """Graceful shutdown"""
        logger.info("Shutting down S.T.E.L.L.A...")
        
        # Simple shutdown for AI bot
        
        # Close database connections
        if self.db_manager:
            await self.db_manager.close()
        
        # Close bot
        await super().close()
        logger.info("S.T.E.L.L.A. shutdown complete")

def setup_signal_handlers(bot):
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}")
        asyncio.create_task(bot.close())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

async def main():
    """Main function to run the bot"""
    # Validate required environment variables
    required_vars = ['DISCORD_BOT_TOKEN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        return
    
    # Create bot instance
    bot = StellaBot()
    
    # Setup signal handlers
    setup_signal_handlers(bot)
    
    try:
        # Start the bot
        token = os.getenv('DISCORD_BOT_TOKEN')
        if not token:
            raise ValueError("DISCORD_BOT_TOKEN environment variable is required")
        await bot.start(token)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
