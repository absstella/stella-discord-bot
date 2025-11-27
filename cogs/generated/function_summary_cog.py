import discord
from discord.ext import commands
import logging

class FunctionSummary(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @commands.command(name="summary", help="現在Botで利用可能なすべての機能を一覧表示します。")
    async def summary(self, ctx):
        """
        現在Botで利用可能なすべての機能を一覧表示します。
        """
        try:
            command_list = []
            for command in self.bot.commands:
                command_list.append(f"`{command.name}`: {command.help or '説明がありません'}")

            if not command_list:
                await ctx.send("利用可能なコマンドはありません。")
                return

            embed = discord.Embed(title="機能の概要", description="\n".join(command_list), color=discord.Color.blue())
            await ctx.send(embed=embed)

        except Exception as e:
            self.logger.exception(f"Error during summary command: {e}")
            await ctx.send("エラーが発生しました。管理者に連絡してください。")


async def setup(bot):
    await bot.add_cog(FunctionSummary(bot))