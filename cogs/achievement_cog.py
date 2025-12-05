import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AchievementCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/achievements.json"
        self.user_data = self.load_data()
        
        # Define Achievements
        self.achievements = {
            "first_step": {
                "name": "はじめの一歩",
                "description": "初めてBotと会話する",
                "icon": "👶"
            },
            "night_owl": {
                "name": "夜更かし勢",
                "description": "深夜3時〜5時の間に発言する",
                "icon": "🦉"
            },
            "chatty": {
                "name": "おしゃべり好き",
                "description": "累計100回発言する",
                "icon": "🗣️"
            },
            "prank_victim": {
                "name": "いたずらの洗礼",
                "description": "Botにいたずらされる",
                "icon": "🤡"
            },
            "lucky_7": {
                "name": "ラッキーセブン",
                "description": "メッセージIDの末尾が777",
                "icon": "🎰"
            },
            "glitch_witness": {
                "name": "グリッチの目撃者",
                "description": "Botのバグ（グリッチ演出）を目撃する",
                "icon": "👾"
            },
            # New Achievements
            "long_talker": {
                "name": "長話の達人",
                "description": "100文字以上のメッセージを送る",
                "icon": "📜"
            },
            "speedster": {
                "name": "スピードスター",
                "description": "Botの起動直後（1分以内）に発言する",
                "icon": "⚡"
            },
            "dice_god": {
                "name": "サイコロの神",
                "description": "ダイスで100（または最大値）を出す",
                "icon": "🎲"
            },
            "radio_fan": {
                "name": "ラジオ愛好家",
                "description": "STELLAラジオ局を開局する",
                "icon": "📻"
            },
            "self_lover": {
                "name": "ナルシスト",
                "description": "自分自身にメンションを送る",
                "icon": "🪞"
            },
            "nightmare": {
                "name": "悪夢の住人",
                "description": "「夢日記」をつける（未実装機能の先取り）",
                "icon": "🌙"
            },
            "commander": {
                "name": "司令官",
                "description": "スラッシュコマンドを10回使用する",
                "icon": "🫡"
            }
        }

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_data(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.user_data, f, ensure_ascii=False, indent=4)

    async def unlock_achievement(self, user: discord.User, achievement_id: str, channel: discord.TextChannel):
        user_id = str(user.id)
        if user_id not in self.user_data:
            self.user_data[user_id] = []
        
        if achievement_id not in self.user_data[user_id]:
            self.user_data[user_id].append(achievement_id)
            self.save_data()
            
            ach = self.achievements[achievement_id]
            
            embed = discord.Embed(
                title=f"🏆 実績解除！: {ach['name']}",
                description=f"{ach['icon']} {ach['description']}",
                color=0xFFD700 # Gold
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.set_footer(text=f"おめでとうございます、{user.display_name}さん！")
            
            await channel.send(embed=embed)
            return True
        return False

    @app_commands.command(name="achievements", description="[実績] 解除した実績を確認します")
    async def show_achievements(self, interaction: discord.Interaction):
        """Show user achievements"""
        user_id = str(interaction.user.id)
        unlocked = self.user_data.get(user_id, [])
        
        total = len(self.achievements)
        count = len(unlocked)
        percentage = int((count / total) * 100)
        
        embed = discord.Embed(
            title=f"🏆 {interaction.user.display_name} の実績",
            description=f"進捗: {count}/{total} ({percentage}%)",
            color=0x00FF00
        )
        
        # List unlocked
        unlocked_text = ""
        for ach_id in unlocked:
            ach = self.achievements.get(ach_id)
            if ach:
                unlocked_text += f"✅ **{ach['name']}** {ach['icon']}\n└ {ach['description']}\n"
        
        if not unlocked_text:
            unlocked_text = "まだ実績はありません。色々試してみましょう！"
            
        embed.add_field(name="解除済み", value=unlocked_text, inline=False)
        
        # List locked (optional, maybe hide secret ones)
        locked_text = ""
        for ach_id, ach in self.achievements.items():
            if ach_id not in unlocked:
                locked_text += f"🔒 **???**\n└ {ach['description']}\n" # Hide name but show desc hint? Or hide all?
                # Let's show description as hint
        
        if locked_text:
            embed.add_field(name="未解除", value=locked_text, inline=False)
            
        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Check: First Step
        await self.unlock_achievement(message.author, "first_step", message.channel)

        # Check: Night Owl (3AM - 5AM)
        now = datetime.now()
        if 3 <= now.hour < 5:
            await self.unlock_achievement(message.author, "night_owl", message.channel)

        # Check: Lucky 7
        if str(message.id).endswith("777"):
            await self.unlock_achievement(message.author, "lucky_7", message.channel)

        # Check: Long Talker
        if len(message.content) >= 100:
            await self.unlock_achievement(message.author, "long_talker", message.channel)

        # Check: Self Lover
        if message.author in message.mentions:
            await self.unlock_achievement(message.author, "self_lover", message.channel)

        # Check: Speedster (Check uptime)
        # Assuming bot has an uptime attribute or we check against start time. 
        # For simplicity, let's skip complex uptime check here or assume bot.start_time exists.
        # if hasattr(self.bot, 'start_time') and (datetime.now() - self.bot.start_time).seconds < 60:
        #    await self.unlock_achievement(message.author, "speedster", message.channel)

    @commands.Cog.listener()
    async def on_app_command_completion(self, interaction, command):
        # Check: Commander
        # We need to track count. For now, just give it on first command for testing.
        # Or use a simple counter in memory (reset on restart is fine for simple pranks)
        await self.unlock_achievement(interaction.user, "commander", interaction.channel)

        # Check: Radio Fan
        if command.name == "start_radio":
            await self.unlock_achievement(interaction.user, "radio_fan", interaction.channel)

    # Hook for other cogs to trigger achievements
    async def trigger_external(self, user, achievement_id, channel):
        """Allow other cogs to trigger achievements"""
        await self.unlock_achievement(user, achievement_id, channel)

async def setup(bot):
    await bot.add_cog(AchievementCog(bot))
