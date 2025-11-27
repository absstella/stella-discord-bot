import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import discord
from discord.ext import commands, tasks
import re
import json
from views.ui_components import HelpView
from data.help_data import HELP_DATA
from config import *

logger = logging.getLogger(__name__)

class UtilityCog(commands.Cog):
    """Utility and helper functionality"""
    
    def __init__(self, bot):
        self.bot = bot
        self.reminders: List[Dict] = []
        self.quotes_cache: Dict[int, Dict] = {}
        self.memos: Dict[int, List[Dict]] = {}  # User ID -> memos
        self.reminder_check_task.start()

    async def cog_unload(self):
        self.reminder_check_task.cancel()

    @commands.hybrid_command(name='help', aliases=['h', 'commands'])
    async def help_command(self, ctx, category: Optional[str] = None):
        """全コマンドを表示します"""
        # Categorize commands
        categories = {
            "🤖 AI・会話": [],
            "👤 プロフィール": [],
            "📚 共有知識": [],
            "🎵 音声・音楽": [],
            "🎨 クリエイティブ": [],
            "🎮 ゲーム": [],
            "⚙️ 開発・進化": [],
            "🛠️ ユーティリティ": []
        }
        
        # Collect all commands from all cogs
        for cog_name, cog in self.bot.cogs.items():
            for command in cog.get_commands():
                if command.hidden:
                    continue
                
                # Special handling for specific commands
                if command.name in ['generate_feature', 'dev', 'evolve', 'trigger_evolution']:
                    categories["⚙️ 開発・進化"].append(command)
                    continue

                # Categorize based on cog name
                cog_name_lower = cog_name.lower()
                if 'music' in cog_name_lower or 'voice' in cog_name_lower:
                    categories["🎵 音声・音楽"].append(command)
                elif 'image' in cog_name_lower or 'draw' in cog_name_lower:
                    categories["🎨 クリエイティブ"].append(command)
                elif 'ai' in cog_name_lower or 'chat' in cog_name_lower:
                    categories["🤖 AI・会話"].append(command)
                elif 'profile' in cog_name_lower:
                    categories["👤 プロフィール"].append(command)
                elif 'knowledge' in cog_name_lower:
                    categories["📚 共有知識"].append(command)
                elif 'game' in cog_name_lower or 'minecraft' in cog_name_lower:
                    categories["🎮 ゲーム"].append(command)
                elif 'dev' in cog_name_lower or 'evolution' in cog_name_lower:
                    categories["⚙️ 開発・進化"].append(command)
                else:
                    categories["🛠️ ユーティリティ"].append(command)
        
        # Create embed
        embed = discord.Embed(
            title="📋 S.T.E.L.L.A. コマンド一覧",
            description="利用可能な全コマンドです。自然な会話でも多くの機能が使えます！",
            color=0x00ff00
        )
        
        # Add each category
        for cat_name, cmds in categories.items():
            if not cmds:
                continue
                
            cmd_list = []
            # Limit to 10 commands per category to avoid embed limits
            display_limit = 10
            
            for cmd in cmds[:display_limit]:
                aliases = f" ({', '.join(cmd.aliases)})" if cmd.aliases else ""
                cmd_list.append(f"`!{cmd.name}{aliases}` - {cmd.help or '説明なし'}")
            
            if len(cmds) > display_limit:
                cmd_list.append(f"...他{len(cmds) - display_limit}個")
                
            if cmd_list:
                embed.add_field(
                    name=cat_name,
                    value="\n".join(cmd_list),
                    inline=False
                )
        
        embed.set_footer(text="💡 Tip: 多くの機能は会話形式でも使えます（例: 『音楽再生して』『プロフィール見せて』）")
        await ctx.send(embed=embed)
    
    # @commands.hybrid_command(name='ping')
    async def ping_disabled(self, ctx):
        """Check bot latency and status"""
        start_time = datetime.utcnow()
        message = await ctx.send("🏓 Pinging...")
        end_time = datetime.utcnow()
        
        # Calculate latencies
        api_latency = (end_time - start_time).total_seconds() * 1000
        ws_latency = self.bot.latency * 1000
        
        embed = discord.Embed(
            title="🏓 Pong!",
            color=SUCCESS_COLOR,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="📡 WebSocket Latency",
            value=f"{ws_latency:.2f}ms",
            inline=True
        )
        
        embed.add_field(
            name="🔄 API Latency",
            value=f"{api_latency:.2f}ms",
            inline=True
        )
        
        embed.add_field(
            name="📊 Status",
            value="🟢 Online" if ws_latency < 200 else "🟡 Slow" if ws_latency < 500 else "🔴 Lagging",
            inline=True
        )
        
        await message.edit(content=None, embed=embed)

    @commands.hybrid_command(name='info', aliases=['about', 'botinfo'])
    async def info_command(self, ctx):
        """Show bot information and statistics"""
        embed = discord.Embed(
            title="🤖 S.T.E.L.L.A. Information",
            description="Smart Team Enhancement & Leisure Learning Assistant",
            color=EMBED_COLOR,
            timestamp=datetime.utcnow()
        )
        
        # Bot stats
        embed.add_field(
            name="📊 Statistics",
            value=f"**Guilds:** {len(self.bot.guilds)}\n"
                  f"**Users:** {sum(guild.member_count for guild in self.bot.guilds)}\n"
                  f"**Commands:** {len(self.bot.commands)}\n"
                  f"**Cogs:** {len(self.bot.cogs)}",
            inline=True
        )
        
        # Performance stats
        stats = self.bot.performance_stats
        embed.add_field(
            name="⚡ Performance",
            value=f"**Uptime:** {stats.get('uptime_hours', 0):.1f}h\n"
                  f"**Memory:** {stats.get('memory_mb', 0):.1f}MB\n"
                  f"**Commands Executed:** {stats.get('commands_executed', 0)}\n"
                  f"**Messages Processed:** {stats.get('messages_processed', 0)}",
            inline=True
        )
        
        # Version info
        embed.add_field(
            name="🔧 Version",
            value=f"**Bot Version:** {BOT_VERSION}\n"
                  f"**Discord.py:** {discord.__version__}\n"
                  f"**Python:** 3.11+",
            inline=True
        )
        
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        embed.set_footer(text="Created with ❤️ for awesome communities")
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='remind', aliases=['reminder'])
    async def set_reminder(self, ctx, time_str: str, *, message: str):
        """Set a reminder for later"""
        try:
            # Parse time string (e.g., "5m", "1h30m", "2d")
            reminder_time = self.parse_time(time_str)
            if not reminder_time:
                await ctx.send("❌ Invalid time format! Use: 5m, 1h30m, 2d, etc.")
                return
            
            # Calculate target time
            target_time = datetime.utcnow() + reminder_time
            
            # Add to reminders list
            reminder_data = {
                'user_id': ctx.author.id,
                'channel_id': ctx.channel.id,
                'message': message,
                'target_time': target_time,
                'created_at': datetime.utcnow()
            }
            
            self.reminders.append(reminder_data)
            
            # Save to database if available
            if self.bot.db_manager:
                async with self.bot.db_manager.get_connection() as conn:
                    await conn.execute(
                        "INSERT INTO reminders (user_id, channel_id, reminder_time, message) VALUES ($1, $2, $3, $4)",
                        ctx.author.id, ctx.channel.id, target_time, message
                    )
            
            embed = discord.Embed(
                title="⏰ Reminder Set",
                description=f"I'll remind you in **{time_str}** ({target_time.strftime('%Y-%m-%d %H:%M UTC')})",
                color=SUCCESS_COLOR
            )
            
            embed.add_field(
                name="📝 Message",
                value=message,
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Reminder error: {e}")
            await ctx.send(f"❌ Error setting reminder: {str(e)}")

    def parse_time(self, time_str: str) -> Optional[timedelta]:
        """Parse time string into timedelta"""
        try:
            # Match patterns like 5m, 1h30m, 2d, etc.
            pattern = r'(\d+)([smhd])'
            matches = re.findall(pattern, time_str.lower())
            
            if not matches:
                return None
            
            total_seconds = 0
            for amount, unit in matches:
                amount = int(amount)
                if unit == 's':
                    total_seconds += amount
                elif unit == 'm':
                    total_seconds += amount * 60
                elif unit == 'h':
                    total_seconds += amount * 3600
                elif unit == 'd':
                    total_seconds += amount * 86400
            
            return timedelta(seconds=total_seconds)
            
        except Exception:
            return None

    @tasks.loop(seconds=REMINDER_CHECK_INTERVAL)
    async def reminder_check_task(self):
        """Check for due reminders"""
        try:
            current_time = datetime.utcnow()
            due_reminders = []
            
            # Check in-memory reminders
            for reminder in self.reminders[:]:
                if reminder['target_time'] <= current_time:
                    due_reminders.append(reminder)
                    self.reminders.remove(reminder)
            
            # Check database reminders if available
            if self.bot.db_manager:
                async with self.bot.db_manager.get_connection() as conn:
                    db_reminders = await conn.fetch(
                        "SELECT * FROM reminders WHERE reminder_time <= $1",
                        current_time
                    )
                    
                    for reminder in db_reminders:
                        due_reminders.append({
                            'user_id': reminder['user_id'],
                            'channel_id': reminder['channel_id'],
                            'message': reminder['message'],
                            'target_time': reminder['reminder_time']
                        })
                    
                    # Remove processed reminders
                    await conn.execute(
                        "DELETE FROM reminders WHERE reminder_time <= $1",
                        current_time
                    )
            
            # Send reminder notifications
            for reminder in due_reminders:
                try:
                    channel = self.bot.get_channel(reminder['channel_id'])
                    if channel:
                        user = self.bot.get_user(reminder['user_id'])
                        if user:
                            embed = discord.Embed(
                                title="⏰ Reminder",
                                description=reminder['message'],
                                color=WARNING_COLOR,
                                timestamp=datetime.utcnow()
                            )
                            
                            embed.set_footer(text=f"Reminder for {user.display_name}")
                            
                            await channel.send(f"{user.mention}", embed=embed)
                            
                except Exception as e:
                    logger.error(f"Error sending reminder: {e}")
                    
        except Exception as e:
            logger.error(f"Reminder check error: {e}")

    @reminder_check_task.before_loop
    async def before_reminder_check(self):
        await self.bot.wait_until_ready()

    @commands.hybrid_command(name='quote')
    async def quote_message(self, ctx, message_id: int = None, channel: discord.TextChannel = None):
        """Quote a message by ID"""
        if not message_id:
            # Quote the message replied to
            if ctx.message.reference:
                message_id = ctx.message.reference.message_id
                channel = ctx.channel
            else:
                await ctx.send("❌ Please provide a message ID or reply to a message!")
                return
        
        if not channel:
            channel = ctx.channel
        
        try:
            # Get the message
            message = await channel.fetch_message(message_id)
            
            # Cache the quote
            self.quotes_cache[message_id] = {
                'content': message.content,
                'author': message.author,
                'timestamp': message.created_at,
                'channel': message.channel,
                'attachments': [att.url for att in message.attachments]
            }
            
            # Create quote embed
            embed = discord.Embed(
                description=message.content or "*[No text content]*",
                color=EMBED_COLOR,
                timestamp=message.created_at
            )
            
            embed.set_author(
                name=message.author.display_name,
                icon_url=message.author.avatar.url if message.author.avatar else None
            )
            
            embed.add_field(
                name="📍 Source",
                value=f"[Jump to message]({message.jump_url})",
                inline=True
            )
            
            embed.add_field(
                name="📅 Date",
                value=message.created_at.strftime("%Y-%m-%d %H:%M"),
                inline=True
            )
            
            # Add attachments if any
            if message.attachments:
                embed.add_field(
                    name="📎 Attachments",
                    value=f"{len(message.attachments)} file(s)",
                    inline=True
                )
                
                # Show first image attachment
                for att in message.attachments:
                    if att.content_type and att.content_type.startswith('image/'):
                        embed.set_image(url=att.url)
                        break
            
            embed.set_footer(text=f"Quoted by {ctx.author.display_name}")
            
            await ctx.send(embed=embed)
            
        except discord.NotFound:
            await ctx.send("❌ Message not found!")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to access that message!")
        except Exception as e:
            logger.error(f"Quote error: {e}")
            await ctx.send(f"❌ Error quoting message: {str(e)}")

    @commands.hybrid_command(name='memo')
    async def memo_manager(self, ctx, action: str, *, content: str = None):
        """Manage personal memos"""
        if action.lower() not in ['add', 'list', 'remove', 'clear']:
            await ctx.send("❌ Invalid action! Use: `add`, `list`, `remove`, or `clear`")
            return
        
        user_id = ctx.author.id
        
        try:
            if action.lower() == 'add':
                if not content:
                    await ctx.send("❌ Please provide content for the memo!")
                    return
                
                # Parse title and content
                parts = content.split(' ', 1)
                if len(parts) == 1:
                    title = f"Memo #{len(self.memos.get(user_id, [])) + 1}"
                    memo_content = parts[0]
                else:
                    title = parts[0]
                    memo_content = parts[1]
                
                # Add memo
                if user_id not in self.memos:
                    self.memos[user_id] = []
                
                memo = {
                    'title': title,
                    'content': memo_content,
                    'created_at': datetime.utcnow(),
                    'id': len(self.memos[user_id]) + 1
                }
                
                self.memos[user_id].append(memo)
                
                embed = discord.Embed(
                    title="📝 Memo Added",
                    description=f"**{title}**\n{memo_content}",
                    color=SUCCESS_COLOR
                )
                await ctx.send(embed=embed)
                
            elif action.lower() == 'list':
                if user_id not in self.memos or not self.memos[user_id]:
                    await ctx.send("❌ You don't have any memos!")
                    return
                
                embed = discord.Embed(
                    title="📝 Your Memos",
                    color=EMBED_COLOR
                )
                
                for memo in self.memos[user_id]:
                    embed.add_field(
                        name=f"#{memo['id']} {memo['title']}",
                        value=f"{memo['content'][:100]}{'...' if len(memo['content']) > 100 else ''}\n"
                              f"*Created: {memo['created_at'].strftime('%Y-%m-%d %H:%M')}*",
                        inline=False
                    )
                
                await ctx.send(embed=embed)
                
            elif action.lower() == 'remove':
                if not content:
                    await ctx.send("❌ Please specify the memo ID to remove!")
                    return
                
                try:
                    memo_id = int(content)
                except ValueError:
                    await ctx.send("❌ Invalid memo ID!")
                    return
                
                if user_id not in self.memos:
                    await ctx.send("❌ You don't have any memos!")
                    return
                
                # Find and remove memo
                for i, memo in enumerate(self.memos[user_id]):
                    if memo['id'] == memo_id:
                        removed_memo = self.memos[user_id].pop(i)
                        
                        embed = discord.Embed(
                            title="🗑️ Memo Removed",
                            description=f"**{removed_memo['title']}** has been removed.",
                            color=WARNING_COLOR
                        )
                        await ctx.send(embed=embed)
                        return
                
                await ctx.send("❌ Memo not found!")
                
            elif action.lower() == 'clear':
                if user_id in self.memos:
                    count = len(self.memos[user_id])
                    self.memos[user_id].clear()
                    
                    embed = discord.Embed(
                        title="🗑️ Memos Cleared",
                        description=f"Removed {count} memo(s).",
                        color=WARNING_COLOR
                    )
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("❌ You don't have any memos to clear!")
                    
        except Exception as e:
            logger.error(f"Memo error: {e}")
            await ctx.send(f"❌ Error managing memo: {str(e)}")

    @commands.hybrid_command(name='uptime')
    async def show_uptime(self, ctx):
        """Show bot uptime and performance stats"""
        uptime_seconds = time.time() - self.bot.start_time
        uptime_str = str(timedelta(seconds=int(uptime_seconds)))
        
        embed = discord.Embed(
            title="⏱️ Bot Uptime",
            color=EMBED_COLOR,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="🕐 Uptime",
            value=uptime_str,
            inline=True
        )
        
        embed.add_field(
            name="📊 Commands Executed",
            value=self.bot.performance_stats.get('commands_executed', 0),
            inline=True
        )
        
        embed.add_field(
            name="💬 Messages Processed",
            value=self.bot.performance_stats.get('messages_processed', 0),
            inline=True
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(UtilityCog(bot))
