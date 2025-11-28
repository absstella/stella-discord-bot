import discord
from discord.ext import commands
import asyncio
import logging

logger = logging.getLogger(__name__)

class RiddleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.riddles = [
            {
                "title": "第一の試練: 始まりの園",
                "question": (
                    "始まりの園にて、それは罪の種子であった。\n"
                    "蛇は囁き、無垢は死に絶えた。\n"
                    "人が神に背き、手にした重荷の名を答えよ。"
                ),
                "answers": ["知恵", "智慧", "wisdom", "knowledge", "ちえ"],
                "hint": "禁断の果実がもたらしたもの。"
            },
            {
                "title": "第二の試練: 凍てついた時",
                "question": (
                    "枝から切り離され、尚も死なず。\n"
                    "油と顔料の中に捕らわれ、額縁の中で永遠に眠る。\n"
                    "それは何へと姿を変えたか？"
                ),
                "answers": ["静物", "still life", "art", "芸術", "絵画", "せいぶつ"],
                "hint": "画家が描く、動かぬ対象。"
            },
            {
                "title": "第三の試練: 原初の飢え",
                "question": (
                    "精神は肉体に屈する。\n"
                    "炎に投じられ、永遠の形は崩れ去り、血肉となる。\n"
                    "それは今、何であるか？"
                ),
                "answers": ["食物", "food", "食べ物", "食料", "糧", "しょくもつ", "たべもの"],
                "hint": "空腹を満たすもの。"
            },
            {
                "title": "第四の試練: 商人の瞳",
                "question": (
                    "聖性も、美も、味も剥ぎ取られた。\n"
                    "ただ黄金のみで測られ、冷たく循環する。\n"
                    "それは何へと堕ちたか？"
                ),
                "answers": ["金銭", "money", "貨幣", "商品", "commodity", "gold", "かね", "きんせん"],
                "hint": "市場で交換される価値そのもの。"
            },
            {
                "title": "最終試練: 影の来訪",
                "question": (
                    "全ての意味が枯れ果てた時、書斎に黒い犬が入ってきた。\n"
                    "彼は騎士の姿を借りて現れる。\n"
                    "その客人の名を呼べ。"
                ),
                "answers": ["悪魔", "devil", "mephistopheles", "メフィストフェレス", "メフィスト", "satan", "あくま"],
                "hint": "ファウストが契約したもの。"
            }
        ]

    @commands.command(name="riddle", aliases=["nazo", "試練"])
    async def start_riddle(self, ctx):
        """ファウストの試練を開始します"""
        
        # Intro
        embed = discord.Embed(
            title="📜 The Trial of Faust",
            description=(
                "ようこそ、真理の探究者よ。\n"
                "芥川が問いかけた「三つのなぜ」。\n"
                "その変遷を辿り、答えを示せ。\n\n"
                "**ルール:**\n"
                "問いに対し、チャットで答えを入力せよ。\n"
                "制限時間は各問60秒。"
            ),
            color=0x2b2d31 # Dark theme
        )
        await ctx.send(embed=embed)
        await asyncio.sleep(2)

        for i, stage in enumerate(self.riddles):
            # Ask Question
            embed = discord.Embed(
                title=f"§ {stage['title']}",
                description=f"```fix\n{stage['question']}\n```\n\n> 答えを入力してください...",
                color=0x9b59b6 # Purple/Mystic
            )
            embed.set_footer(text=f"Phase {i+1}/{len(self.riddles)}")
            question_msg = await ctx.send(embed=embed)

            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel

            try:
                # Wait for answer
                while True:
                    user_msg = await self.bot.wait_for('message', check=check, timeout=60.0)
                    content = user_msg.content.strip().lower()
                    
                    if any(ans in content for ans in stage['answers']):
                        # Correct
                        await user_msg.add_reaction("✅")
                        success_embed = discord.Embed(
                            description=f"**正解。**\n真理へと一歩近づいた。",
                            color=0x00FF00
                        )
                        await ctx.send(embed=success_embed)
                        await asyncio.sleep(1.5)
                        break
                    else:
                        # Incorrect
                        await user_msg.add_reaction("❌")
                        # Optional: Give hint on fail? Or just let them retry?
                        # Let's let them retry within the timeout
            
            except asyncio.TimeoutError:
                timeout_embed = discord.Embed(
                    title="⌛ Time Expired",
                    description="時は無慈悲に過ぎ去った。\n試練は失敗に終わった。",
                    color=0xFF0000
                )
                await ctx.send(embed=timeout_embed)
                return

        # Completion
        final_embed = discord.Embed(
            title="✨ Trial Completed",
            description=(
                "見事だ。\n"
                "林檎は知恵から始まり、芸術となり、糧となり、貨幣となり、\n"
                "ついには悪魔を招き入れた。\n\n"
                "汝もまた、その意味を知る者なり。"
            ),
            color=0xF1C40F # Gold
        )
        final_embed.set_image(url="https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/Mephistopheles_by_Mark_Antokolsky.jpg/480px-Mephistopheles_by_Mark_Antokolsky.jpg") # Public domain Mephistopheles statue image if valid, or just generic
        # Removing image to be safe and use local assets or just text
        final_embed.set_image(url=None)
        
        await ctx.send(embed=final_embed)

async def setup(bot):
    await bot.add_cog(RiddleCog(bot))
