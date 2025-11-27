"""
Personality Cog
Provides a quick view of STELLA's current personality traits, notes, and relationship status.
"""

import json
import os
import discord
from discord.ext import commands

PROFILE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "stella_profile.json")

class PersonalityCog(commands.Cog):
    """Display STELLA's personality information"""

    def __init__(self, bot):
        self.bot = bot

    def _load_profile(self):
        try:
            with open(PROFILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            return {"error": str(e)}

    @commands.hybrid_command(name="personality", aliases=["profile", "traits"])
    async def personality(self, ctx):
        """Show current personality traits and notes"""
        data = self._load_profile()
        if "error" in data:
            await ctx.send(f"⚠️ プロフィール読み込みエラー: {data['error']}")
            return
        embed = discord.Embed(title="🤖 STELLA の人格情報", color=0x00ff00)
        traits = data.get("personality_traits", [])
        embed.add_field(name="性格特徴", value=", ".join(traits) or "なし", inline=False)
        embed.add_field(name="人物メモ", value=data.get("personality_notes", "なし"), inline=False)
        rel = data.get("relationship_status", "不明")
        embed.add_field(name="関係性ステータス", value=rel, inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(PersonalityCog(bot))
