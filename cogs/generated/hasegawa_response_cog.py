import json
import os
import random

import discord
from discord.ext import commands

class HasegawaResponse(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_path = "data/hasegawa_responses.json"
        self.responses = self.load_responses()

    def load_responses(self):
        """JSONファイルからレスポンスをロードします。"""
        try:
            if not os.path.exists("data"):
                os.makedirs("data")

            with open(self.data_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"ファイルが見つかりませんでした: {self.data_path}。デフォルトの辞書を返します。")
            return {}  # デフォルトの空の辞書を返す
        except json.JSONDecodeError:
            print(f"JSONデコードエラー: {self.data_path}。空の辞書を返します。")
            return {} # JSONが不正な場合に空の辞書を返す
        except Exception as e:
            print(f"レスポンスのロード中にエラーが発生しました: {e}。空の辞書を返します。")
            return {} #その他の例外が発生した場合に空の辞書を返す
            

    def save_responses(self):
        """レスポンスをJSONファイルに保存します。"""
        try:
            with open(self.data_path, "w", encoding="utf-8") as f:
                json.dump(self.responses, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"レスポンスの保存中にエラーが発生しました: {e}")

    @commands.command(name="hasegawa", description="長谷川に関連するレスポンスを検索し、表示します。", usage="!hasegawa [キーワード]")
    async def hasegawa(self, ctx, *, keyword: str = None):
        """
        キーワードに関連する長谷川のレスポンスを検索し、表示します。
        キーワードが指定されない場合は、ランダムなレスポンスを返します。
        """
        if not self.responses:
            await ctx.send("長谷川のレスポンスデータがロードされていません。")
            return

        if keyword:
            if keyword.lower() in self.responses:
                response = random.choice(self.responses[keyword.lower()])
                await ctx.send(response)
            else:
                await ctx.send(f"キーワード '{keyword}' に一致する長谷川のレスポンスが見つかりませんでした。")
        else:
            # すべてのキーワードを取得し、ランダムに1つ選択
            all_keywords = list(self.responses.keys())
            if all_keywords:
                random_keyword = random.choice(all_keywords)
                response = random.choice(self.responses[random_keyword])
                await ctx.send(f"キーワード: {random_keyword}\n{response}")
            else:
                await ctx.send("長谷川のレスポンスデータが空です。")

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.__class__.__name__} Cog がロードされました。')


async def setup(bot):
    await bot.add_cog(HasegawaResponse(bot))