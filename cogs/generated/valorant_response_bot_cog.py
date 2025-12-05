import discord
from discord.ext import commands

class ValorantResponseBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_id = 542607089529257994  # User ID to monitor
        self.response_message = "私も行けたら行きたいな！"
        self.trigger_word = "valorant"

    @commands.Cog.listener()
    async def on_message(self, message):
        try:
            if message.author.id == self.user_id and self.trigger_word in message.content.lower():
                await message.channel.send(self.response_message)
        except Exception as e:
            print(f"Error in on_message: {e}")

async def setup(bot):
    await bot.add_cog(ValorantResponseBot(bot))