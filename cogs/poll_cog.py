import discord
from discord.ext import commands
from discord import app_commands
import logging

logger = logging.getLogger(__name__)

class PollCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="poll", description="投票を作成します")
    @app_commands.describe(question="質問内容", options="選択肢（カンマ区切り、最大10個）")
    async def poll(self, interaction: discord.Interaction, question: str, options: str):
        option_list = [opt.strip() for opt in options.split(',') if opt.strip()]
        
        if len(option_list) < 2:
            await interaction.response.send_message("❌ 選択肢は最低2つ必要です。", ephemeral=True)
            return
        
        if len(option_list) > 10:
            await interaction.response.send_message("❌ 選択肢は最大10個までです。", ephemeral=True)
            return

        # Emojis for numbers 1-10
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        description = ""
        for i, option in enumerate(option_list):
            description += f"{emojis[i]} {option}\n"

        embed = discord.Embed(
            title=f"📊 {question}",
            description=description,
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"作成者: {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        
        # Add reactions
        for i in range(len(option_list)):
            await message.add_reaction(emojis[i])

async def setup(bot):
    await bot.add_cog(PollCog(bot))
