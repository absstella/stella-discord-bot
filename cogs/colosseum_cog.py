import discord
from discord import app_commands
from discord.ext import commands
import google.generativeai as genai
import os
import logging
import asyncio
import random

logger = logging.getLogger(__name__)

class ColosseumCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_battles = {}  # Store active battles to prevent duplicates

    def get_user_profile_text(self, user_id, guild_id):
        """Helper to get a text summary of user profile for AI"""
        # This assumes AICog is loaded and has get_user_profile
        ai_cog = self.bot.get_cog("AICog")
        if not ai_cog:
            return "Unknown User"
        
        # We need to call the async method from a sync context or ensure we are in async
        # Since this will be called from async commands, we can just return a coroutine or use it there
        return "Profile access required"

    async def generate_combat_persona(self, user: discord.Member):
        """Generate a combat persona using Gemini based on user profile"""
        ai_cog = self.bot.get_cog("AICog")
        if not ai_cog:
            return None

        try:
            profile = await ai_cog.get_user_profile(user.id, user.guild.id)
            
            # Construct prompt
            prompt = f"""
            Analyze this user profile and generate a "Combat Persona" for a fantasy auto-battler game.
            
            User: {user.display_name}
            Nickname: {profile.nickname}
            Personality: {', '.join(profile.personality_traits)}
            Interests: {', '.join(profile.interests)}
            Speech Style: {profile.speech_patterns}
            
            Output strictly in JSON format:
            {{
                "class_name": "Creative Class Name (e.g. Python Paladin)",
                "stats": {{
                    "hp": 100-500,
                    "atk": 10-100,
                    "def": 10-100,
                    "spd": 10-100,
                    "luck": 10-100
                }},
                "passive_skill": {{
                    "name": "Skill Name",
                    "effect": "Description"
                }},
                "ultimate_move": {{
                    "name": "Move Name",
                    "description": "Flashy description",
                    "damage_type": "Physical/Magical/Mental"
                }},
                "intro_quote": "A short battle cry based on their personality"
            }}
            """
            
            if ai_cog.model:
                response = ai_cog.model.generate_content(prompt)
                # Clean up json block if present
                text = response.text.replace("```json", "").replace("```", "").strip()
                import json
                return json.loads(text)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error generating persona: {e}")
            return None

    # Slash Command Group
    colosseum = app_commands.Group(name="colosseum", description="ペルソナ・コロシアム")

    @colosseum.command(name="stats", description="自分または他人の戦闘ペルソナを確認します")
    @app_commands.describe(user="確認するユーザー")
    async def stats(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        await interaction.response.defer()
        
        persona = await self.generate_combat_persona(target)
        if not persona:
            await interaction.followup.send("❌ ペルソナの生成に失敗しました。")
            return

        embed = discord.Embed(
            title=f"⚔️ {target.display_name}の戦闘ペルソナ",
            description=f"**クラス**: {persona['class_name']}\n*「{persona['intro_quote']}」*",
            color=0xFF0000
        )
        
        stats = persona['stats']
        embed.add_field(name="ステータス", value=f"❤️ HP: {stats['hp']}\n⚔️ ATK: {stats['atk']}\n🛡️ DEF: {stats['def']}\n💨 SPD: {stats['spd']}\n🍀 LUCK: {stats['luck']}", inline=True)
        
        embed.add_field(name="パッシブスキル", value=f"**{persona['passive_skill']['name']}**\n{persona['passive_skill']['effect']}", inline=False)
        embed.add_field(name="必殺技", value=f"**{persona['ultimate_move']['name']}**\n{persona['ultimate_move']['description']}", inline=False)
        
        await interaction.followup.send(embed=embed)

    @colosseum.command(name="challenge", description="指定したユーザーと対戦します")
    @app_commands.describe(opponent="対戦相手")
    async def challenge(self, interaction: discord.Interaction, opponent: discord.Member):
        if opponent.id == interaction.user.id:
            await interaction.response.send_message("自分自身とは戦えません。", ephemeral=True)
            return
            
        if opponent.bot:
             await interaction.response.send_message("Botとは戦えません。", ephemeral=True)
             return

        if interaction.channel_id in self.active_battles:
            await interaction.response.send_message("このチャンネルでは既に戦闘が行われています。", ephemeral=True)
            return

        await interaction.response.send_message(f"⚔️ **{interaction.user.display_name}** が **{opponent.display_name}** に決闘を挑んだ！\nペルソナを生成中...")
        self.active_battles[interaction.channel_id] = True

        try:
            p1_persona = await self.generate_combat_persona(interaction.user)
            p2_persona = await self.generate_combat_persona(opponent)
            
            if not p1_persona or not p2_persona:
                await interaction.followup.send("❌ ペルソナ生成エラーにより戦闘中止。")
                return

            # Battle Logic (Simplified for MVP)
            # We will ask AI to narrate the battle in one go or turn by turn.
            # For better UX, let's do a stream of turns.
            
            ai_cog = self.bot.get_cog("AICog")
            prompt = f"""
            Simulate a turn-based battle between two personas.
            
            Player 1: {interaction.user.display_name}
            {p1_persona}
            
            Player 2: {opponent.display_name}
            {p2_persona}
            
            Output a dramatic battle log with 3-5 turns and a clear winner.
            Format:
            Turn 1: [Description]
            Turn 2: [Description]
            ...
            Conclusion: [Winner] wins!
            """
            
            if ai_cog and ai_cog.model:
                response = ai_cog.model.generate_content(prompt)
                battle_log = response.text
                
                # Split by lines and send gradually
                lines = battle_log.split('\n')
                buffer = ""
                for line in lines:
                    if line.strip():
                        buffer += line + "\n"
                        if len(buffer) > 200 or "Turn" in line or "Conclusion" in line:
                            await interaction.channel.send(buffer)
                            buffer = ""
                            await asyncio.sleep(2) # Suspense
                if buffer:
                    await interaction.channel.send(buffer)
            
        except Exception as e:
            logger.error(f"Battle error: {e}")
            await interaction.channel.send("❌ 戦闘中にエラーが発生しました。")
        finally:
            if interaction.channel_id in self.active_battles:
                del self.active_battles[interaction.channel_id]

async def setup(bot):
    await bot.add_cog(ColosseumCog(bot))
