import discord
from discord.ext import commands

class HasegawaResponse(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="hasegawa", help="特定のメッセージを送信します。")
    async def hasegawa(self, ctx):
        """!hasegawa コマンドを受け取った際に、特定のメッセージを送信する"""
        try:
            await ctx.send("HIKAKIN4ねよ、ザコ")
        except discord.DiscordException as e:
            print(f"Error sending message: {e}")
            await ctx.send("メッセージ送信に失敗しました。")

async def setup(bot):
    await bot.add_cog(HasegawaResponse(bot))