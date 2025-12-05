import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/stats.json"
        self.stats = self.load_stats()
        self.voice_states = {} # user_id: start_time
        self.save_stats_loop.start()

    def load_stats(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_stats(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=4)

    def cog_unload(self):
        self.save_stats_loop.cancel()
        self.save_stats()

    @tasks.loop(minutes=5)
    async def save_stats_loop(self):
        self.save_stats()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        guild_id = str(message.guild.id)
        user_id = str(message.author.id)
        today = datetime.now().strftime("%Y-%m-%d")

        if guild_id not in self.stats:
            self.stats[guild_id] = {"messages": {}, "voice": {}, "daily": {}}

        # Total messages
        if user_id not in self.stats[guild_id]["messages"]:
            self.stats[guild_id]["messages"][user_id] = 0
        self.stats[guild_id]["messages"][user_id] += 1

        # Daily messages
        if today not in self.stats[guild_id]["daily"]:
            self.stats[guild_id]["daily"][today] = {"messages": 0, "voice": 0}
        self.stats[guild_id]["daily"][today]["messages"] += 1

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return

        user_id = str(member.id)
        guild_id = str(member.guild.id)
        now = datetime.now()

        if guild_id not in self.stats:
            self.stats[guild_id] = {"messages": {}, "voice": {}, "daily": {}}

        # Joined voice
        if not before.channel and after.channel:
            self.voice_states[user_id] = now

        # Left voice
        elif before.channel and not after.channel:
            if user_id in self.voice_states:
                start_time = self.voice_states.pop(user_id)
                duration = (now - start_time).total_seconds()
                
                # Update total voice time
                if user_id not in self.stats[guild_id]["voice"]:
                    self.stats[guild_id]["voice"][user_id] = 0
                self.stats[guild_id]["voice"][user_id] += duration

                # Update daily voice time
                today = now.strftime("%Y-%m-%d")
                if today not in self.stats[guild_id]["daily"]:
                    self.stats[guild_id]["daily"][today] = {"messages": 0, "voice": 0}
                self.stats[guild_id]["daily"][today]["voice"] += duration

        # Switched channel (treat as continue, or split? simple: treat as continue unless disconnect)
        # If we want to be precise, we could split, but for now simple join/leave is enough.
        # Actually, if they switch, before.channel is not None and after.channel is not None.
        # So the above logic ignores switches, which is correct (they are still in voice).

    @app_commands.command(name="stats", description="サーバーの統計情報を表示します")
    async def show_stats(self, interaction: discord.Interaction):
        guild = interaction.guild
        guild_id = str(guild.id)
        
        embed = discord.Embed(title=f"📊 {guild.name} 統計情報", color=discord.Color.gold())
        
        # Basic Info
        total_members = guild.member_count
        online_members = sum(1 for m in guild.members if m.status != discord.Status.offline)
        bot_count = sum(1 for m in guild.members if m.bot)
        human_count = total_members - bot_count
        
        embed.add_field(name="👥 メンバー", value=f"合計: **{total_members}**\n(人: {human_count}, Bot: {bot_count})\n🟢 オンライン: {online_members}", inline=True)
        embed.add_field(name="💬 チャンネル", value=f"テキスト: {len(guild.text_channels)}\nボイス: {len(guild.voice_channels)}", inline=True)
        embed.add_field(name="📅 作成日", value=guild.created_at.strftime("%Y/%m/%d"), inline=True)

        # Activity Stats
        if guild_id in self.stats:
            # Top Messagers
            sorted_msgs = sorted(self.stats[guild_id]["messages"].items(), key=lambda x: x[1], reverse=True)[:5]
            msg_text = ""
            for uid, count in sorted_msgs:
                user = guild.get_member(int(uid))
                name = user.display_name if user else "Unknown"
                msg_text += f"**{name}**: {count}回\n"
            
            if msg_text:
                embed.add_field(name="🏆 発言数ランキング", value=msg_text, inline=False)

            # Top Voice Users
            sorted_voice = sorted(self.stats[guild_id]["voice"].items(), key=lambda x: x[1], reverse=True)[:5]
            voice_text = ""
            for uid, seconds in sorted_voice:
                user = guild.get_member(int(uid))
                name = user.display_name if user else "Unknown"
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                voice_text += f"**{name}**: {hours}時間{minutes}分\n"
            
            if voice_text:
                embed.add_field(name="🎙️ 通話時間ランキング", value=voice_text, inline=False)

        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(StatsCog(bot))
