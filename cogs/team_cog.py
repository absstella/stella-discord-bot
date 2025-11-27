import asyncio
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import discord
from discord.ext import commands, tasks
from views.ui_components import RecruitmentView, PollView
from config import *

logger = logging.getLogger(__name__)

class TeamCog(commands.Cog):
    """Team management and recruitment functionality"""
    
    def __init__(self, bot):
        self.bot = bot
        self.active_recruitments: Dict[int, Dict] = {}  # Message ID -> recruitment data
        self.temporary_channels: Dict[int, Dict] = {}  # Channel ID -> creation data
        self.birthday_check_task.start()

    def cog_unload(self):
        self.birthday_check_task.cancel()

    @commands.hybrid_command(name='recruit', aliases=['lfg', 'looking'])
    async def create_recruitment(self, ctx, game: str, max_members: int = 5):
        """Create a recruitment post for a game"""
        if max_members < 2 or max_members > 20:
            await ctx.send("❌ Member count must be between 2-20!")
            return
        
        try:
            embed = discord.Embed(
                title=f"🎮 {game.upper()} - Team Recruitment",
                description=f"**Leader:** {ctx.author.mention}\n**Slots:** 1/{max_members}",
                color=EMBED_COLOR,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="📝 Participants",
                value=f"1. {ctx.author.display_name} (Leader)",
                inline=False
            )
            
            embed.set_footer(text="Click below to join or leave!")
            
            # Create recruitment view
            view = RecruitmentView(game, max_members, ctx.author)
            message = await ctx.send(embed=embed, view=view)
            
            # Store recruitment data
            self.active_recruitments[message.id] = {
                'game': game,
                'max_members': max_members,
                'leader': ctx.author,
                'participants': [ctx.author],
                'message': message,
                'created_at': datetime.utcnow()
            }
            
            # Auto-delete after timeout
            await asyncio.sleep(RECRUITMENT_TIMEOUT)
            if message.id in self.active_recruitments:
                await self.end_recruitment(message.id)
                
        except Exception as e:
            logger.error(f"Recruitment creation error: {e}")
            await ctx.send(f"❌ Error creating recruitment: {str(e)}")

    async def end_recruitment(self, message_id: int):
        """End a recruitment and clean up"""
        if message_id not in self.active_recruitments:
            return
        
        recruitment = self.active_recruitments[message_id]
        try:
            embed = discord.Embed(
                title=f"⏰ {recruitment['game'].upper()} - Recruitment Ended",
                description="This recruitment has expired.",
                color=WARNING_COLOR
            )
            
            await recruitment['message'].edit(embed=embed, view=None)
            del self.active_recruitments[message_id]
            
        except Exception as e:
            logger.error(f"Error ending recruitment: {e}")

    @commands.hybrid_command(name='vc', aliases=['voice'])
    async def voice_channel_manager(self, ctx, action: str, *, name: str = None):
        """Manage temporary voice channels"""
        if action.lower() not in ['create', 'delete', 'list']:
            await ctx.send("❌ Invalid action! Use: `create`, `delete`, or `list`")
            return
        
        try:
            if action.lower() == 'create':
                if not name:
                    name = f"{ctx.author.display_name}'s Channel"
                
                # Find or create category
                category = None
                for cat in ctx.guild.categories:
                    if cat.name == TEMP_VC_CATEGORY:
                        category = cat
                        break
                
                if not category:
                    category = await ctx.guild.create_category(TEMP_VC_CATEGORY)
                
                # Create voice channel
                channel = await ctx.guild.create_voice_channel(
                    name,
                    category=category,
                    user_limit=10
                )
                
                # Store channel data
                self.temporary_channels[channel.id] = {
                    'creator': ctx.author,
                    'created_at': datetime.utcnow(),
                    'name': name
                }
                
                embed = discord.Embed(
                    title="🔊 Voice Channel Created",
                    description=f"Created: **{name}**\nChannel: {channel.mention}",
                    color=SUCCESS_COLOR
                )
                await ctx.send(embed=embed)
                
            elif action.lower() == 'delete':
                if not name:
                    await ctx.send("❌ Please specify the channel name to delete!")
                    return
                
                # Find channel
                channel_to_delete = None
                for channel in ctx.guild.voice_channels:
                    if channel.name.lower() == name.lower() and channel.id in self.temporary_channels:
                        channel_to_delete = channel
                        break
                
                if not channel_to_delete:
                    await ctx.send("❌ Temporary channel not found!")
                    return
                
                # Check permissions
                channel_data = self.temporary_channels[channel_to_delete.id]
                if ctx.author != channel_data['creator'] and not ctx.author.guild_permissions.manage_channels:
                    await ctx.send("❌ You can only delete channels you created!")
                    return
                
                # Delete channel
                await channel_to_delete.delete()
                del self.temporary_channels[channel_to_delete.id]
                
                embed = discord.Embed(
                    title="🗑️ Voice Channel Deleted",
                    description=f"Deleted: **{channel_to_delete.name}**",
                    color=WARNING_COLOR
                )
                await ctx.send(embed=embed)
                
            elif action.lower() == 'list':
                if not self.temporary_channels:
                    await ctx.send("❌ No temporary channels found!")
                    return
                
                embed = discord.Embed(
                    title="🔊 Temporary Voice Channels",
                    color=EMBED_COLOR
                )
                
                for channel_id, data in self.temporary_channels.items():
                    channel = ctx.guild.get_channel(channel_id)
                    if channel:
                        member_count = len(channel.members)
                        embed.add_field(
                            name=data['name'],
                            value=f"Creator: {data['creator'].mention}\n"
                                  f"Members: {member_count}\n"
                                  f"Created: {data['created_at'].strftime('%H:%M')}\n"
                                  f"Channel: {channel.mention}",
                            inline=False
                        )
                
                await ctx.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Voice channel manager error: {e}")
            await ctx.send(f"❌ Error managing voice channel: {str(e)}")

    @commands.hybrid_command(name='teams', aliases=['divide', 'split'])
    async def create_teams(self, ctx, team_count: int = 2):
        """Divide voice channel members into teams"""
        if not ctx.author.voice:
            await ctx.send("❌ You need to be in a voice channel!")
            return
        
        if team_count < 2 or team_count > 10:
            await ctx.send("❌ Team count must be between 2-10!")
            return
        
        try:
            voice_channel = ctx.author.voice.channel
            members = [member for member in voice_channel.members if not member.bot]
            
            if len(members) < team_count:
                await ctx.send(f"❌ Not enough members! Need at least {team_count} members.")
                return
            
            # Shuffle and divide into teams
            random.shuffle(members)
            teams = [[] for _ in range(team_count)]
            
            for i, member in enumerate(members):
                teams[i % team_count].append(member)
            
            embed = discord.Embed(
                title="⚔️ Teams Created",
                description=f"Divided {len(members)} members into {team_count} teams:",
                color=EMBED_COLOR
            )
            
            team_emojis = ["🔴", "🔵", "🟢", "🟡", "🟣", "🟠", "⚫", "⚪", "🟤", "🔷"]
            
            for i, team in enumerate(teams):
                if team:  # Only show non-empty teams
                    team_members = "\n".join([f"• {member.display_name}" for member in team])
                    embed.add_field(
                        name=f"{team_emojis[i]} Team {i+1} ({len(team)} members)",
                        value=team_members,
                        inline=True
                    )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Team creation error: {e}")
            await ctx.send(f"❌ Error creating teams: {str(e)}")

    @commands.hybrid_command(name='poll')
    async def create_poll(self, ctx, question: str, *options):
        """Create a poll with multiple options"""
        if len(options) < 2:
            await ctx.send("❌ Please provide at least 2 options!")
            return
        
        if len(options) > 10:
            await ctx.send("❌ Maximum 10 options allowed!")
            return
        
        try:
            embed = discord.Embed(
                title="📊 Poll",
                description=f"**{question}**",
                color=EMBED_COLOR,
                timestamp=datetime.utcnow()
            )
            
            option_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            
            options_text = ""
            for i, option in enumerate(options):
                options_text += f"{option_emojis[i]} {option}\n"
            
            embed.add_field(
                name="Options",
                value=options_text,
                inline=False
            )
            
            embed.set_footer(text=f"Poll by {ctx.author.display_name}")
            
            # Create poll view
            view = PollView(list(options), ctx.author)
            message = await ctx.send(embed=embed, view=view)
            
            # Add reaction emojis
            for i in range(len(options)):
                await message.add_reaction(option_emojis[i])
                
        except Exception as e:
            logger.error(f"Poll creation error: {e}")
            await ctx.send(f"❌ Error creating poll: {str(e)}")

    @commands.hybrid_command(name='birthday')
    async def birthday_manager(self, ctx, action: str, *, date: str = None):
        """Manage birthday notifications"""
        if not self.bot.db_manager:
            await ctx.send("❌ Database not available!")
            return
        
        if action.lower() not in ['set', 'remove', 'list', 'next']:
            await ctx.send("❌ Invalid action! Use: `set`, `remove`, `list`, or `next`")
            return
        
        try:
            if action.lower() == 'set':
                if not date:
                    await ctx.send("❌ Please provide a date in MM-DD format (e.g., 12-25)")
                    return
                
                try:
                    month, day = map(int, date.split('-'))
                    if not (1 <= month <= 12 and 1 <= day <= 31):
                        raise ValueError
                    
                    birth_date = datetime(2000, month, day).date()  # Use 2000 as placeholder year
                    
                except ValueError:
                    await ctx.send("❌ Invalid date format! Use MM-DD (e.g., 12-25)")
                    return
                
                # Save to database
                async with self.bot.db_manager.get_connection() as conn:
                    await conn.execute(
                        """INSERT INTO birthdays (user_id, birth_date, guild_id) 
                           VALUES ($1, $2, $3) 
                           ON CONFLICT (user_id) DO UPDATE SET 
                           birth_date = $2, guild_id = $3""",
                        ctx.author.id, birth_date, ctx.guild.id
                    )
                
                embed = discord.Embed(
                    title="🎂 Birthday Set",
                    description=f"Birthday set to {birth_date.strftime('%B %d')}",
                    color=SUCCESS_COLOR
                )
                await ctx.send(embed=embed)
                
            elif action.lower() == 'remove':
                async with self.bot.db_manager.get_connection() as conn:
                    result = await conn.execute(
                        "DELETE FROM birthdays WHERE user_id = $1",
                        ctx.author.id
                    )
                
                if result == "DELETE 1":
                    embed = discord.Embed(
                        title="🗑️ Birthday Removed",
                        description="Your birthday has been removed from the system.",
                        color=WARNING_COLOR
                    )
                else:
                    embed = discord.Embed(
                        title="❌ No Birthday Found",
                        description="You don't have a birthday set.",
                        color=ERROR_COLOR
                    )
                await ctx.send(embed=embed)
                
            elif action.lower() == 'list':
                async with self.bot.db_manager.get_connection() as conn:
                    results = await conn.fetch(
                        "SELECT user_id, birth_date FROM birthdays WHERE guild_id = $1 ORDER BY birth_date",
                        ctx.guild.id
                    )
                
                if not results:
                    await ctx.send("❌ No birthdays found in this server!")
                    return
                
                embed = discord.Embed(
                    title="🎂 Server Birthdays",
                    color=EMBED_COLOR
                )
                
                birthday_text = ""
                for result in results:
                    user = ctx.guild.get_member(result['user_id'])
                    if user:
                        birthday_text += f"• **{user.display_name}** - {result['birth_date'].strftime('%B %d')}\n"
                
                embed.description = birthday_text or "No valid birthdays found."
                await ctx.send(embed=embed)
                
            elif action.lower() == 'next':
                async with self.bot.db_manager.get_connection() as conn:
                    results = await conn.fetch(
                        "SELECT user_id, birth_date FROM birthdays WHERE guild_id = $1",
                        ctx.guild.id
                    )
                
                if not results:
                    await ctx.send("❌ No birthdays found in this server!")
                    return
                
                # Find next birthday
                today = datetime.now().date().replace(year=2000)
                upcoming_birthdays = []
                
                for result in results:
                    birthday = result['birth_date']
                    user = ctx.guild.get_member(result['user_id'])
                    if user:
                        # Calculate days until birthday
                        if birthday >= today:
                            days_until = (birthday - today).days
                        else:
                            # Birthday already passed this year, calculate for next year
                            next_year_birthday = birthday.replace(year=today.year + 1)
                            days_until = (next_year_birthday - today).days
                        
                        upcoming_birthdays.append((user, birthday, days_until))
                
                if upcoming_birthdays:
                    # Sort by days until birthday
                    upcoming_birthdays.sort(key=lambda x: x[2])
                    next_birthday = upcoming_birthdays[0]
                    
                    embed = discord.Embed(
                        title="🎂 Next Birthday",
                        description=f"**{next_birthday[0].display_name}**\n"
                                  f"Date: {next_birthday[1].strftime('%B %d')}\n"
                                  f"Days until: {next_birthday[2]}",
                        color=EMBED_COLOR
                    )
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("❌ No upcoming birthdays found!")
                
        except Exception as e:
            logger.error(f"Birthday manager error: {e}")
            await ctx.send(f"❌ Error managing birthday: {str(e)}")

    @tasks.loop(hours=24)
    async def birthday_check_task(self):
        """Check for birthdays daily"""
        if not self.bot.db_manager:
            return
        
        try:
            today = datetime.now().date().replace(year=2000)
            
            async with self.bot.db_manager.get_connection() as conn:
                results = await conn.fetch(
                    "SELECT user_id, guild_id FROM birthdays WHERE birth_date = $1",
                    today
                )
            
            for result in results:
                guild = self.bot.get_guild(result['guild_id'])
                if not guild:
                    continue
                
                user = guild.get_member(result['user_id'])
                if not user:
                    continue
                
                # Find general channel
                channel = None
                for ch in guild.text_channels:
                    if ch.name in ['general', 'announcements', 'birthday']:
                        channel = ch
                        break
                
                if not channel:
                    channel = guild.text_channels[0]
                
                # Send birthday message
                embed = discord.Embed(
                    title="🎂 Happy Birthday!",
                    description=f"Happy Birthday {user.mention}! 🎉\n"
                              f"Hope you have a wonderful day!",
                    color=0xffb6c1
                )
                
                await channel.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Birthday check error: {e}")

    @birthday_check_task.before_loop
    async def before_birthday_check(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(TeamCog(bot))
