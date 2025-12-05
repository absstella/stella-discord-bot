import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import logging
import random
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class AdvancedGameCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.clips_file = "data/game_clips.json"
        self.tournaments = {} # guild_id: {data}
        self.clips = self.load_clips()

    def load_clips(self):
        if os.path.exists(self.clips_file):
            try:
                with open(self.clips_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import logging
import random
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class AdvancedGameCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.clips_file = "data/game_clips.json"
        self.tournaments = {} # guild_id: {data}
        self.clips = self.load_clips()

    def load_clips(self):
        if os.path.exists(self.clips_file):
            try:
                with open(self.clips_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_clips(self):
        os.makedirs(os.path.dirname(self.clips_file), exist_ok=True)
        with open(self.clips_file, 'w', encoding='utf-8') as f:
            json.dump(self.clips, f, ensure_ascii=False, indent=4)

    # --- 1. Tournament Manager (Simplified) ---
    @commands.hybrid_command(name="create_tournament", description="[ゲーム] 簡易トーナメント表を作成します")
    @app_commands.describe(players="参加者（スペース区切りでメンションまたは名前）")
    async def create_tournament(self, ctx: commands.Context, players: str):
        """Create a simple tournament bracket"""
        player_list = players.split()
        if len(player_list) < 2:
            await ctx.send("❌ 参加者は2名以上必要です。", ephemeral=True)
            return

        random.shuffle(player_list)
        
        # Create pairs
        matches = []
        for i in range(0, len(player_list), 2):
            if i + 1 < len(player_list):
                matches.append(f"{player_list[i]} vs {player_list[i+1]}")
            else:
                matches.append(f"{player_list[i]} (シード)")

        bracket = "\n".join([f"第{i+1}試合: {m}" for i, m in enumerate(matches)])
        
        embed = discord.Embed(title="🏆 トーナメント表", description=bracket, color=0xFFD700)
        embed.set_footer(text="勝敗報告は `/report_match` (未実装: 手動で進行してください)")
        
        await ctx.send(embed=embed)

    # --- 2. Scrim Scheduler ---
    @commands.hybrid_command(name="scrim_poll", description="[ゲーム] スクリム（練習試合）の日程調整を行います")
    @app_commands.describe(dates="候補日（カンマ区切り, 例: 12/1 21:00, 12/2 22:00）")
    async def scrim_poll(self, ctx: commands.Context, dates: str):
        """Create a scrim schedule poll"""
        date_list = [d.strip() for d in dates.split(',')]
        
        embed = discord.Embed(
            title="📅 スクリム日程調整",
            description="参加できる日程に投票してください！",
            color=0x0099FF
        )
        
        # In a real bot, we'd use buttons or reactions for each date.
        # For simplicity/robustness here, we'll use a text representation and ask for reactions (if standard messages) 
        # or just display the poll for manual checking. 
        # Let's make it a bit fancy with a description.
        
        body = ""
        for i, date in enumerate(date_list):
            body += f"**{i+1}. {date}**\n"
        
        embed.add_field(name="候補日", value=body, inline=False)
        embed.set_footer(text="各日程の番号のリアクションを押してください（手動運用）")
        
        message = await ctx.send(embed=embed)
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        for i in range(min(len(date_list), len(emojis))):
            await message.add_reaction(emojis[i])

    # --- 3. Clip Manager ---
    @commands.hybrid_command(name="clip", description="[ゲーム] 神プレイのクリップを保存します")
    @app_commands.describe(url="クリップのURL", title="タイトル/コメント")
    async def add_clip(self, ctx: commands.Context, url: str, title: str):
        """Save a game clip"""
        if "http" not in url:
            await ctx.send("❌ 有効なURLを入力してください。", ephemeral=True)
            return

        guild_id = str(ctx.guild.id)
        if guild_id not in self.clips:
            self.clips[guild_id] = []
            
        clip_data = {
            "user_id": ctx.author.id,
            "url": url,
            "title": title,
            "timestamp": datetime.now().isoformat(),
            "likes": 0
        }
        
        self.clips[guild_id].append(clip_data)
        self.save_clips()
        
        await ctx.send(f"🎥 **クリップを保存しました！**\n{title}\n{url}")

    @commands.hybrid_command(name="top_clips", description="[ゲーム] 保存されたクリップの一覧を表示します")
    async def top_clips(self, ctx: commands.Context):
        """Show recent clips"""
        guild_id = str(ctx.guild.id)
        if guild_id not in self.clips or not self.clips[guild_id]:
            await ctx.send("❌ まだクリップがありません。", ephemeral=True)
            return
            
        # Get last 5 clips (In real app, sort by likes)
        recent_clips = self.clips[guild_id][-5:]
        recent_clips.reverse()
        
        embed = discord.Embed(title="🎬 最新の神プレイ集", color=0xFF0000)
        
        for clip in recent_clips:
            user = ctx.guild.get_member(clip['user_id'])
            username = user.display_name if user else "Unknown"
            embed.add_field(
                name=f"{clip['title']} (by {username})",
                value=clip['url'],
                inline=False
            )
            
        await ctx.send(embed=embed)

    # --- 4. AI Coach ---
    @commands.hybrid_command(name="coach", description="[ゲーム] AIコーチにゲームの質問をします（ネット検索付き）")
    @app_commands.describe(question="質問内容（例: アセントのソーヴァの定点は？）")
    async def ai_coach(self, ctx: commands.Context, question: str):
        """Ask AI coach with web search"""
        await ctx.defer()
        
        ai_cog = self.bot.get_cog('AICog')
        if not ai_cog:
            await ctx.send("❌ AI機能が利用できません。")
            return

        # Construct prompt
        search_query = question
        context = ""
        
        # Try Web Search if available
        if hasattr(ai_cog, 'web_search_client') and ai_cog.web_search_client:
            try:
                results = await ai_cog.web_search_client.search(search_query)
                if results:
                    context = "\n".join([f"- {r['title']}: {r['snippet']}" for r in results])
            except Exception as e:
                logger.error(f"Coach search failed: {e}")

        prompt = f"""
        あなたはプロのeスポーツコーチです。
        以下の質問に対して、初心者にも分かりやすく、具体的かつ実践的なアドバイスをしてください。
        
        質問: {question}
        
        参考情報（Web検索結果）:
        {context}
        
        回答のスタイル:
        - 結論から話す
        - 専門用語には簡単な解説をつける
        - 励ましの言葉を添える
        """
        
        try:
            response_text = "申し訳ありません、コーチング中にエラーが発生しました。"
            if ai_cog.model:
                response = await ai_cog.model.generate_content_async(prompt)
                response_text = response.text
            
            # Split if too long
            if len(response_text) > 1900:
                response_text = response_text[:1900] + "..."
                
            await ctx.send(f"🎓 **AIコーチのアドバイス**\n\nQ. {question}\n\n{response_text}")
            
        except Exception as e:
            await ctx.send(f"❌ エラー: {e}")

    # --- 5. Match Betting ---
    @commands.hybrid_command(name="start_bet", description="[ゲーム] 勝敗予想ベットを開始します")
    @app_commands.describe(title="賭けのタイトル（例: 次のランクマッチ勝てる？）")
    async def start_bet(self, ctx: commands.Context, title: str):
        """Start a betting session"""
        embed = discord.Embed(
            title="🎰 ベット開始！",
            description=f"**{title}**\n\nWIN（勝ち）か LOSE（負け）に投票してください！",
            color=0xFFA500
        )
        message = await ctx.send(embed=embed)
        await message.add_reaction("⭕") # Win
        await message.add_reaction("❌") # Lose

    # --- 6. Sensitivity Converter ---
    @commands.hybrid_command(name="sens", description="[ゲーム] ゲーム間の感度を変換します")
    @app_commands.describe(game_from="変換元のゲーム", value="感度数値", game_to="変換先のゲーム")
    @app_commands.choices(game_from=[
        app_commands.Choice(name="Valorant", value="val"),
        app_commands.Choice(name="Apex Legends", value="apex"),
        app_commands.Choice(name="Overwatch 2", value="ow2")
    ], game_to=[
        app_commands.Choice(name="Valorant", value="val"),
        app_commands.Choice(name="Apex Legends", value="apex"),
        app_commands.Choice(name="Overwatch 2", value="ow2")
    ])
    async def sensitivity_converter(self, ctx: commands.Context, game_from: str, value: float, game_to: str):
        """Convert sensitivity between games"""
        # Base multipliers relative to Valorant (approximate)
        # Val: 1
        # Apex: 3.181818
        # OW2: 10.6
        
        multipliers = {
            "val": 1.0,
            "apex": 3.181818,
            "ow2": 10.6
        }
        
        if game_from not in multipliers or game_to not in multipliers:
            await ctx.send("❌ 未対応のゲームです。", ephemeral=True)
            return

        # Convert to base (Val) then to target
        base_val = value / multipliers[game_from]
        result = base_val * multipliers[game_to]
        
        await ctx.send(f"🎚️ **感度変換**\n{game_from.upper()} {value} -> **{game_to.upper()} {result:.3f}**")

    # --- 7. Server Wiki (Simplified) ---
    @commands.hybrid_command(name="add_term", description="[Wiki] サーバー用語を登録します")
    @app_commands.describe(word="単語", meaning="意味")
    async def add_term(self, ctx: commands.Context, word: str, meaning: str):
        """Add a term to server wiki"""
        # In a real app, load/save to JSON. Here we'll use a simple dict in memory or file if needed.
        # Re-using clips file logic for simplicity or creating new one.
        wiki_file = "data/server_wiki.json"
        data = {}
        if os.path.exists(wiki_file):
            try:
                with open(wiki_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except:
                pass
        
        guild_id = str(ctx.guild.id)
        if guild_id not in data:
            data[guild_id] = {}
            
        data[guild_id][word] = meaning
        
        os.makedirs(os.path.dirname(wiki_file), exist_ok=True)
        with open(wiki_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        await ctx.send(f"📖 用語を登録しました: **{word}**")

    @commands.hybrid_command(name="whatis", description="[Wiki] サーバー用語の意味を調べます")
    @app_commands.describe(word="単語")
    async def whatis(self, ctx: commands.Context, word: str):
        """Lookup a term in server wiki"""
        wiki_file = "data/server_wiki.json"
        data = {}
        if os.path.exists(wiki_file):
            try:
                with open(wiki_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except:
                pass
        
        guild_id = str(ctx.guild.id)
        meaning = data.get(guild_id, {}).get(word)
        
        if meaning:
            await ctx.send(f"📖 **{word}**\n{meaning}")
        else:
            await ctx.send(f"❌ 「{word}」は登録されていません。", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdvancedGameCog(bot))
