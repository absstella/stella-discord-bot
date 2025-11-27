import discord
from discord.ext import commands
import logging

class SimpleTextResponse(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @commands.command(name="az", description="Responds with \"あほくさｗ\".", usage="!az")
    async def az(self, ctx):
        try:
            await ctx.send("あほくさｗ")
        except discord.HTTPException as e:
            self.logger.error(f"Failed to send message: {e}")
            await ctx.send("メッセージの送信に失敗しました。")
        except Exception as e:
            self.logger.exception(f"An unexpected error occurred: {e}")
            await ctx.send("予期せぬエラーが発生しました。")


async def setup(bot):
    await bot.add_cog(SimpleTextResponse(bot))