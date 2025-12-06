import discord
from discord.ext import commands
import asyncio

class ReuResponse(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="reu", help="reuに関するメッセージを4つ送信します")
    async def reu(self, ctx):
        """!reu コマンドを受け取った際に、4つのメッセージを連続で送信する"""
        
        # ここに送信したい4つのテキストを設定
        messages = [
            "reuが募集すると集まらない理由",
            "reuテキスト2",
            "reuテキスト3",
            "reuテキスト4"
        ]

        try:
            for msg in messages:
                await ctx.send(msg)
                # 順番が前後しないよう、念のため少し待機
                await asyncio.sleep(1) 
                
        except discord.DiscordException as e:
            print(f"Error sending message: {e}")
            await ctx.send("メッセージ送信に失敗しました。")

async def setup(bot):
    await bot.add_cog(ReuResponse(bot))