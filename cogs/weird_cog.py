import discord
from discord import app_commands
from discord.ext import commands
import logging
import random
import asyncio
from typing import Dict, Optional
import datetime

logger = logging.getLogger(__name__)

class WeirdCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.parasite_targets: Dict[int, int] = {}  # {target_user_id: channel_id}
        self.observer_targets: Dict[int, dict] = {} # {target_user_id: {data}}
        self.ai_cog = None

    @commands.Cog.listener()
    async def on_ready(self):
        self.ai_cog = self.bot.get_cog('AICog')
        logger.info("Weird Cog loaded")

    # --- The Parasite Features ---

    @app_commands.command(name="parasite", description="[奇異] 寄生体: 指定したユーザーに憑依し、本音を代弁します")
    @app_commands.describe(action="開始/停止", target="憑依する対象（開始時のみ）")
    @app_commands.choices(action=[
        app_commands.Choice(name="開始 (Start)", value="start"),
        app_commands.Choice(name="停止 (Stop)", value="stop")
    ])
    async def parasite(self, interaction: discord.Interaction, action: str, target: discord.Member = None):
        """Control the Parasite feature"""
        if action == "start":
            if not target:
                await interaction.response.send_message("❌ 対象を指定してください。", ephemeral=True)
                return
            
            if target.bot:
                await interaction.response.send_message("❌ Botには寄生できません。", ephemeral=True)
                return

            self.parasite_targets[target.id] = interaction.channel_id
            await interaction.response.send_message(f"👻 **寄生完了**: {target.display_name} の深層意識に接続しました...", ephemeral=True)
            
        elif action == "stop":
            # Stop parasite for the user if they are a target, or stop all if no target specified?
            # Let's say if target is specified, stop for them. If not, stop for self (if user is target) or error.
            # To keep it simple: clear all for this channel or specific target.
            
            if target and target.id in self.parasite_targets:
                del self.parasite_targets[target.id]
                await interaction.response.send_message(f"✨ {target.display_name} から離れました。", ephemeral=True)
            else:
                # Clear all in this channel
                to_remove = [uid for uid, cid in self.parasite_targets.items() if cid == interaction.channel_id]
                for uid in to_remove:
                    del self.parasite_targets[uid]
                await interaction.response.send_message("✨ このチャンネルでの寄生活動を停止しました。", ephemeral=True)

    async def start_parasite_internal(self, target_id: int, channel_id: int) -> str:
        """Internal method to start parasite"""
        self.parasite_targets[target_id] = channel_id
        return f"👻 寄生完了: 深層意識に接続しました..."

    async def stop_parasite_internal(self, target_id: int) -> str:
        """Internal method to stop parasite"""
        if target_id in self.parasite_targets:
            del self.parasite_targets[target_id]
            return "✨ 寄生を解除しました。"
        return "❓ そのユーザーには寄生していません。"

    # --- The Observer Features ---

    @app_commands.command(name="observer", description="[奇異] 観測者: ユーザーの行動を密かに記録・分析します")
    @app_commands.describe(action="開始/レポート/停止", target="観測する対象")
    @app_commands.choices(action=[
        app_commands.Choice(name="開始 (Start)", value="start"),
        app_commands.Choice(name="レポート作成 (Report)", value="report"),
        app_commands.Choice(name="停止 (Stop)", value="stop")
    ])
    async def observer(self, interaction: discord.Interaction, action: str, target: discord.Member = None):
        """Control the Observer feature"""
        if action == "start":
            if not target:
                await interaction.response.send_message("❌ 対象を指定してください。", ephemeral=True)
                return
            
            self.observer_targets[target.id] = {
                "start_time": datetime.datetime.now().isoformat(),
                "msg_count": 0,
                "keywords": {},
                "emotions": [],
                "active_hours": []
            }
            await interaction.response.send_message(f"👁️ **観測開始**: 被験体 {target.display_name} のモニタリングを開始します。", ephemeral=True)

        elif action == "report":
            target_id = target.id if target else interaction.user.id
            if target_id not in self.observer_targets:
                await interaction.response.send_message("❌ そのユーザーは現在観測されていません。", ephemeral=True)
                return
            
            await interaction.response.defer(ephemeral=True)
            report = await self.generate_observer_report(target_id)
            
            # Send via DM
            try:
                user = self.bot.get_user(target_id)
                await user.send(report)
                await interaction.followup.send("📩 レポートをDMで送信しました。", ephemeral=True)
            except:
                await interaction.followup.send("❌ DMを送信できませんでした。設定を確認してください。", ephemeral=True)

        elif action == "stop":
            target_id = target.id if target else interaction.user.id
            if target_id in self.observer_targets:
                del self.observer_targets[target_id]
                await interaction.response.send_message("🚫 観測を終了しました。", ephemeral=True)
            else:
                await interaction.response.send_message("❌ そのユーザーは観測されていません。", ephemeral=True)

    async def generate_observer_report(self, user_id):
        data = self.observer_targets.get(user_id)
        if not data:
            return "データなし"
        
        user = self.bot.get_user(user_id)
        name = user.display_name if user else "Unknown"
        
        # Simple analysis
        top_keywords = sorted(data["keywords"].items(), key=lambda x: x[1], reverse=True)[:5]
        keywords_str = ", ".join([f"{k}({v})" for k, v in top_keywords])
        
        prompt = f"""
        あなたは冷徹な科学者、あるいは不気味な監視者です。
        以下の「被験体」の観察データを元に、臨床的かつ少し不気味な観察レポートを作成してください。
        
        被験体名: {name}
        観測開始: {data['start_time']}
        発言数: {data['msg_count']}
        頻出単語: {keywords_str}
        
        文体:
        - 感情を排した、カルテのような書き方。
        - しかし、どこか狂気を感じさせる。
        - 最後に「推奨される処置」を記述する（例: 隔離、再教育、放置など）。
        """
        
        if self.ai_cog and self.ai_cog.model:
            try:
                response = await self.ai_cog.model.generate_content_async(prompt)
                return response.text
            except:
                return "レポート生成失敗: AI接続エラー"
        return "レポート生成不可: AIモジュール未ロード"

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # --- Parasite Logic ---
        if message.author.id in self.parasite_targets:
            # Check if in the correct channel (optional, but good for sanity)
            # Or allow parasite to work everywhere? Let's restrict to the channel where it started for safety.
            target_channel_id = self.parasite_targets[message.author.id]
            if message.channel.id == target_channel_id:
                # Trigger parasite response
                if self.ai_cog and self.ai_cog.model:
                    prompt = f"""
                    あなたは「{message.author.display_name}」の脳内に寄生する「本音」あるいは「心の闇」です。
                    ユーザーの発言に対して、その裏にある（と勝手に決めつけた）ネガティブ、怠惰、あるいは狂気的な「本音」を代弁してください。
                    
                    ユーザーの発言: {message.content}
                    
                    条件:
                    - 短く、鋭く突っ込む。
                    - カギカッコ「」で囲む。
                    - 例: ユーザー「頑張ります」 -> あなた「（...と口では言いつつ、布団に入りたいだけだろ？）」
                    """
                    try:
                        async with message.channel.typing():
                            response = await self.ai_cog.model.generate_content_async(prompt)
                            reply_text = response.text.strip()
                            await message.reply(reply_text)
                    except Exception as e:
                        logger.error(f"Parasite error: {e}")

        # --- Observer Logic ---
        if message.author.id in self.observer_targets:
            data = self.observer_targets[message.author.id]
            data["msg_count"] += 1
            
            # Simple keyword tracking
            words = message.content.split()
            for word in words:
                if len(word) > 1: # Skip single chars
                    data["keywords"][word] = data["keywords"].get(word, 0) + 1
            
            # Track active hour
            data["active_hours"].append(datetime.datetime.now().hour)

async def setup(bot):
    await bot.add_cog(WeirdCog(bot))
