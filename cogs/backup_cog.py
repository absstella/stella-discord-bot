import discord
from discord.ext import commands, tasks
import asyncio
import logging
import subprocess
import os
from datetime import datetime
from config import *

logger = logging.getLogger(__name__)

class BackupCog(commands.Cog):
    """
    Automated and manual backup of user data to GitHub.
    """
    def __init__(self, bot):
        self.bot = bot
        self.backup_task.start()

    def cog_unload(self):
        self.backup_task.cancel()

    @commands.hybrid_command(name='backup')
    @commands.has_permissions(administrator=True)
    async def backup_command(self, ctx):
        """Manually trigger a backup to GitHub"""
        await ctx.defer()
        
        try:
            success, message = await self.perform_backup()
            
            if success:
                embed = discord.Embed(
                    title="✅ Backup Successful",
                    description=f"Data has been pushed to GitHub.\n\n`{message}`",
                    color=SUCCESS_COLOR,
                    timestamp=datetime.utcnow()
                )
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="❌ Backup Failed",
                    description=f"Error during backup:\n```\n{message}\n```",
                    color=ERROR_COLOR,
                    timestamp=datetime.utcnow()
                )
                await ctx.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Backup command error: {e}")
            await ctx.send(f"❌ An unexpected error occurred: {e}")

    @tasks.loop(hours=6)
    async def backup_task(self):
        """Automated backup task"""
        logger.info("Starting automated backup...")
        success, message = await self.perform_backup()
        if success:
            logger.info(f"Automated backup successful: {message}")
        else:
            logger.error(f"Automated backup failed: {message}")

    @backup_task.before_loop
    async def before_backup_task(self):
        await self.bot.wait_until_ready()

    async def perform_backup(self):
        """
        Executes git commands to backup data.
        Returns (success: bool, message: str)
        """
        try:
            # Define paths to backup
            paths_to_backup = ["data", "database"]
            
            # Check if git is initialized
            if not os.path.exists(".git"):
                return False, "Git is not initialized in the bot directory."

            # Run git add
            process = await asyncio.create_subprocess_exec(
                "git", "add", "-f", *paths_to_backup,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                return False, f"Git add failed: {stderr.decode()}"

            # Check if there are changes to commit
            process = await asyncio.create_subprocess_exec(
                "git", "status", "--porcelain",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if not stdout:
                return True, "No changes to backup."

            # Run git commit
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            commit_message = f"Auto backup: {timestamp}"
            
            process = await asyncio.create_subprocess_exec(
                "git", "commit", "-m", commit_message,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                return False, f"Git commit failed: {stderr.decode()}"

            # Run git push
            process = await asyncio.create_subprocess_exec(
                "git", "push",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                return False, f"Git push failed: {stderr.decode()}"

            return True, f"Committed and pushed: {commit_message}"

        except Exception as e:
            logger.error(f"Backup exception: {e}")
            return False, str(e)

async def setup(bot):
    await bot.add_cog(BackupCog(bot))
