import discord
from discord.ext import commands
from discord import app_commands
import logging
import asyncio
import random
from utils.speech_pattern_manager import speech_pattern_manager

logger = logging.getLogger(__name__)

class DoppelgangerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ai_cog = None
        self.active_doppelgangers = {} # {channel_id: target_user_id}

    @commands.Cog.listener()
    async def on_ready(self):
        self.ai_cog = self.bot.get_cog('AICog')
        logger.info("Doppelganger Cog loaded")

    @app_commands.command(name="doppelganger", description="[いたずら] Botが指定したユーザーになりきって会話に参加します")
    @app_commands.describe(action="開始/停止", target="なりきる対象（開始時のみ）")
    @app_commands.choices(action=[
        app_commands.Choice(name="開始 (Start)", value="start"),
        app_commands.Choice(name="停止 (Stop)", value="stop")
    ])
    async def doppelganger(self, interaction: discord.Interaction, action: str, target: discord.Member = None):
        """Start or stop doppelganger mode"""
        if action == "start":
            if not target:
                await interaction.response.send_message("❌ 開始するにはターゲットを指定してください。", ephemeral=True)
                return
            
            if interaction.channel_id in self.active_doppelgangers:
                await interaction.response.send_message("❌ このチャンネルでは既にドッペルゲンガーが活動中です。", ephemeral=True)
                return

            self.active_doppelgangers[interaction.channel_id] = target.id
            
            # Change nickname to match target (if possible)
            try:
                await interaction.guild.me.edit(nick=target.display_name)
            except:
                pass # Ignore permission errors

            await interaction.response.send_message(f"🪞 ドッペルゲンガーモード起動... {target.display_name} になりきります。", ephemeral=True)
            # Send a greeting as the user
            await self.send_doppelganger_message(interaction.channel, target.id, "（ニヤリ...）")

        elif action == "stop":
            if interaction.channel_id in self.active_doppelgangers:
                del self.active_doppelgangers[interaction.channel_id]
                try:
                    await interaction.guild.me.edit(nick=None)
                except:
                    pass
                await interaction.response.send_message("✨ ドッペルゲンガーモードを終了しました。", ephemeral=True)
            else:
                await interaction.response.send_message("❌ このチャンネルではドッペルゲンガーは活動していません。", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        # Check if doppelganger is active in this channel
        if message.channel.id in self.active_doppelgangers:
            target_id = self.active_doppelgangers[message.channel.id]
            
            # Don't reply to the target themselves (to avoid confusion/loops)
            # Or maybe do? It's funny. Let's do it.
            
            # Chance to reply (30%?)
            if random.random() < 0.3:
                async with message.channel.typing():
                    await self.send_doppelganger_message(message.channel, target_id, message.content, reply_to=message)

    async def send_doppelganger_message(self, channel, target_id, trigger_content, reply_to=None):
        """Generate and send a message as the target"""
        if not self.ai_cog or not self.ai_cog.model:
            return

        # Get speech instructions
        instructions = speech_pattern_manager.generate_speech_instructions(target_id, channel.guild.id)
        
        # Get profile for context
        profile = await self.ai_cog.get_user_profile(target_id, channel.guild.id)
        profile_context = f"名前: {profile.nickname or 'Unknown'}\n"
        if profile.interests: profile_context += f"趣味: {', '.join(profile.interests)}\n"
        if profile.custom_attributes.get('occupation'): profile_context += f"職業: {profile.custom_attributes['occupation']}\n"

        prompt = f"""
        あなたは今、以下のユーザーになりきって会話をしています。
        
        【ユーザー情報】
        {profile_context}
        
        【話し方の指示】
        {instructions}
        
        【会話の状況】
        相手の発言: {trigger_content}
        
        このユーザーとして、自然な返答を生成してください。
        名前を名乗る必要はありません。短めの返答（1-2文）が望ましいです。
        """
        
        try:
            response = await self.ai_cog.model.generate_content_async(prompt)
            content = response.text.strip()
            
            if reply_to:
                await reply_to.reply(content)
            else:
                await channel.send(content)
                
        except Exception as e:
            logger.error(f"Doppelganger generation failed: {e}")

async def setup(bot):
    await bot.add_cog(DoppelgangerCog(bot))
