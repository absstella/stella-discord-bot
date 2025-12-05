import discord
from discord.ext import commands
from discord import app_commands
import logging
import asyncio
import random
import json

logger = logging.getLogger(__name__)

class AkinatorCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ai_cog = None
        self.active_games = {} # {channel_id: game_state}

    @commands.Cog.listener()
    async def on_ready(self):
        self.ai_cog = self.bot.get_cog('AICog')
        logger.info("Akinator Cog loaded")

    @app_commands.command(name="akinator", description="[ゲーム] サーバー内の誰かをBotが当てます（またはその逆）")
    @app_commands.describe(mode="モード選択")
    @app_commands.choices(mode=[
        app_commands.Choice(name="Botが当てる (Bot Guess)", value="bot_guess"),
        # app_commands.Choice(name="Botを当てる (User Guess)", value="user_guess") # Future implementation
    ])
    async def akinator(self, interaction: discord.Interaction, mode: str = "bot_guess"):
        """Start an Akinator game"""
        if interaction.channel_id in self.active_games:
            await interaction.response.send_message("❌ このチャンネルでは既にゲームが進行中です。", ephemeral=True)
            return

        if not self.ai_cog:
            self.ai_cog = self.bot.get_cog('AICog')
        
        if not self.ai_cog or not self.ai_cog.model:
            await interaction.response.send_message("❌ AI機能が利用できないため、ゲームを開始できません。", ephemeral=True)
            return

        await interaction.response.send_message(
            "🧞 **サーバー・アキネイター**へようこそ！\n"
            "サーバー内のメンバー（Bot含む）を一人思い浮かべてください。\n"
            "準備ができたら「スタート」ボタンを押してください。",
            view=AkinatorStartView(self, interaction)
        )

    async def start_game(self, interaction):
        """Initialize game state"""
        # Fetch all members
        members = [m for m in interaction.guild.members if not m.bot] # Exclude bots for now? Or include? Let's include bots if requested, but mainly humans.
        # Actually, let's include everyone but filter out offline if too many? No, all members.
        
        # Load profiles for better guessing
        candidates = []
        for member in members:
            profile = await self.ai_cog.get_user_profile(member.id, interaction.guild.id)
            candidates.append({
                "id": member.id,
                "name": member.display_name,
                "profile": profile
            })
        
        game_state = {
            "candidates": candidates,
            "eliminated": [],
            "questions_asked": [],
            "turn": 0,
            "interaction": interaction,
            "last_question": None
        }
        self.active_games[interaction.channel_id] = game_state
        
        await self.next_turn(interaction.channel_id)

    async def next_turn(self, channel_id):
        """Process next turn"""
        game = self.active_games.get(channel_id)
        if not game:
            return

        # Check win condition
        if len(game["candidates"]) <= 1:
            await self.make_guess(channel_id)
            return
        
        if game["turn"] >= 20: # Max questions
            await self.make_guess(channel_id)
            return

        # Generate Question using Gemini
        try:
            # Create a summary of remaining candidates to help AI generate a splitting question
            # To avoid token limits, we pick a random sample if too many
            sample_candidates = game["candidates"]
            if len(sample_candidates) > 10:
                sample_candidates = random.sample(game["candidates"], 10)
            
            candidate_info = []
            for c in sample_candidates:
                info = f"- {c['name']}: "
                p = c['profile']
                if p.custom_attributes.get('gender'): info += f"性別={p.custom_attributes['gender']}, "
                if p.custom_attributes.get('occupation'): info += f"職業={p.custom_attributes['occupation']}, "
                if p.interests: info += f"趣味={','.join(p.interests[:3])}, "
                if p.favorite_games: info += f"ゲーム={','.join(p.favorite_games[:3])}"
                candidate_info.append(info)
            
            candidates_str = "\n".join(candidate_info)
            
            prompt = f"""
            あなたはアキネイターです。サーバー内のメンバーを特定するための「はい/いいえ」で答えられる質問を1つ作成してください。
            
            現在の候補者の一部:
            {candidates_str}
            
            これまでの質問:
            {', '.join(game['questions_asked'])}
            
            条件:
            1. 候補者を絞り込める質問にしてください（例: 「その人は男性ですか？」「その人はFPSが好きですか？」）。
            2. 質問だけを出力してください。余計な文章は不要です。
            """
            
            response = await self.ai_cog.model.generate_content_async(prompt)
            question = response.text.strip()
            game["last_question"] = question
            game["questions_asked"].append(question)
            game["turn"] += 1
            
            embed = discord.Embed(
                title=f"質問 {game['turn']}",
                description=f"**{question}**",
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"候補者数: {len(game['candidates'])}人")
            
            view = AkinatorQuestionView(self, channel_id)
            await game["interaction"].channel.send(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Akinator error: {e}")
            await game["interaction"].channel.send("❌ エラーが発生しました。ゲームを終了します。")
            del self.active_games[channel_id]

    async def process_answer(self, channel_id, answer):
        """Process user answer and filter candidates"""
        game = self.active_games.get(channel_id)
        if not game:
            return

        question = game["last_question"]
        
        # Use AI to filter candidates based on the answer
        # We ask AI which candidates match the (Question + Answer) pair
        
        # Batch processing if many candidates
        remaining_candidates = []
        
        # Simple heuristic filtering first if possible? No, rely on AI for profile matching.
        # But for 100+ members, this is slow.
        # Let's do a simplified check or batch check.
        
        # For now, let's assume the AI can handle checking a batch of 20 names at a time.
        
        candidates_to_check = game["candidates"]
        chunks = [candidates_to_check[i:i + 15] for i in range(0, len(candidates_to_check), 15)]
        
        for chunk in chunks:
            chunk_info = []
            for c in chunk:
                p = c['profile']
                # Serialize relevant profile data
                p_data = {
                    "name": c['name'],
                    "gender": p.custom_attributes.get('gender'),
                    "occupation": p.custom_attributes.get('occupation'),
                    "hobbies": p.interests,
                    "games": p.favorite_games,
                    "likes": p.custom_attributes.get('likes'),
                    "attributes": p.custom_attributes
                }
                chunk_info.append(json.dumps(p_data, ensure_ascii=False))
            
            chunk_str = "\n".join(chunk_info)
            
            prompt = f"""
            以下の候補者リストから、質問「{question}」に対する回答が「{answer}」である条件に合致する人を選んでください。
            
            回答の意味:
            - yes: 当てはまる
            - no: 当てはまらない
            - dont_know: 分からない（全員残す）
            - probably: たぶん当てはまる
            - probably_not: たぶん当てはまらない
            
            候補者リスト (JSON):
            {chunk_str}
            
            出力形式:
            合致する候補者の名前のみを改行区切りで出力してください。
            """
            
            try:
                response = await self.ai_cog.model.generate_content_async(prompt)
                kept_names = response.text.strip().split('\n')
                kept_names = [n.strip() for n in kept_names]
                
                for c in chunk:
                    if answer == "dont_know":
                        remaining_candidates.append(c)
                    elif c['name'] in kept_names or any(k in c['name'] for k in kept_names): # Loose matching
                        remaining_candidates.append(c)
                    # If answer is 'no', AI should return names that match 'no' condition? 
                    # Wait, the prompt asks for "matches the condition". 
                    # If answer is "no", "matches condition" means "Does NOT have the trait".
                    # So the AI logic should be correct.
            except Exception as e:
                logger.error(f"Filtering error: {e}")
                remaining_candidates.extend(chunk) # Keep all on error to be safe

        game["candidates"] = remaining_candidates
        
        if not game["candidates"]:
            # If everyone eliminated, maybe the user lied or AI erred. 
            # Reset to previous candidates? Or just give up?
            await game["interaction"].channel.send("🤔 うーん... 該当する人がいなくなってしまいました。私の負けです！")
            del self.active_games[channel_id]
            return

        await self.next_turn(channel_id)

    async def make_guess(self, channel_id):
        """Make a final guess"""
        game = self.active_games.get(channel_id)
        if not game:
            return
            
        if not game["candidates"]:
             await game["interaction"].channel.send("🤔 降参です。誰のことか分かりませんでした。")
             del self.active_games[channel_id]
             return

        # Pick the most likely candidate (first one)
        target = game["candidates"][0]
        user = game["interaction"].guild.get_member(target["id"])
        
        embed = discord.Embed(
            title="💡 思い浮かべているのは...",
            description=f"**{target['name']}** さんですか？",
            color=discord.Color.gold()
        )
        if user:
            embed.set_thumbnail(url=user.display_avatar.url)
            
        view = AkinatorGuessView(self, channel_id)
        await game["interaction"].channel.send(embed=embed, view=view)

class AkinatorStartView(discord.ui.View):
    def __init__(self, cog, original_interaction):
        super().__init__(timeout=60)
        self.cog = cog
        self.original_interaction = original_interaction

    @discord.ui.button(label="スタート", style=discord.ButtonStyle.green)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.cog.start_game(self.original_interaction)
        self.stop()

class AkinatorQuestionView(discord.ui.View):
    def __init__(self, cog, channel_id):
        super().__init__(timeout=120)
        self.cog = cog
        self.channel_id = channel_id

    async def handle_answer(self, interaction, answer):
        await interaction.response.defer()
        await interaction.message.delete() # Clean up previous question
        await self.cog.process_answer(self.channel_id, answer)

    @discord.ui.button(label="はい", style=discord.ButtonStyle.success)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_answer(interaction, "yes")

    @discord.ui.button(label="いいえ", style=discord.ButtonStyle.danger)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_answer(interaction, "no")

    @discord.ui.button(label="分からない", style=discord.ButtonStyle.secondary)
    async def dont_know(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_answer(interaction, "dont_know")

    @discord.ui.button(label="たぶんそう", style=discord.ButtonStyle.primary)
    async def probably(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_answer(interaction, "probably")

    @discord.ui.button(label="たぶん違う", style=discord.ButtonStyle.primary)
    async def probably_not(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_answer(interaction, "probably_not")

class AkinatorGuessView(discord.ui.View):
    def __init__(self, cog, channel_id):
        super().__init__(timeout=60)
        self.cog = cog
        self.channel_id = channel_id

    @discord.ui.button(label="正解！", style=discord.ButtonStyle.success)
    async def correct(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🎉 やったー！私の勝ちですね！")
        if self.channel_id in self.cog.active_games:
            del self.cog.active_games[self.channel_id]
        self.stop()

    @discord.ui.button(label="違う", style=discord.ButtonStyle.danger)
    async def incorrect(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Continue game if candidates left? Or just fail?
        # For simplicity, let's just fail or continue if candidates > 1
        game = self.cog.active_games.get(self.channel_id)
        if game and len(game["candidates"]) > 1:
            await interaction.response.send_message("🤔 違いましたか... もう少し質問させてください。")
            # Remove the wrong guess
            game["candidates"].pop(0)
            await self.cog.next_turn(self.channel_id)
        else:
            await interaction.response.send_message("😵 降参です... 誰だったんですか？")
            if self.channel_id in self.cog.active_games:
                del self.cog.active_games[self.channel_id]
        self.stop()

async def setup(bot):
    await bot.add_cog(AkinatorCog(bot))
