import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
import random
import logging
from datetime import datetime, timedelta
import asyncio
from utils.card_generator import CardGenerator
from utils.gacha_engine import GachaEngine, BattleState as EngineBattleState

logger = logging.getLogger(__name__)

class GachaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.card_gen = CardGenerator()
        self.engine = GachaEngine()
        self.voice_points_loop.start()
        
    def get_player(self, user_id):
        return self.engine.get_player(user_id)

    def add_points(self, user_id, amount):
        return self.engine.add_points(user_id, amount)

    def set_points(self, user_id, amount):
        return self.engine.set_points(user_id, amount)

    def get_player_data(self, user_id):
        player = self.get_player(user_id)
        return {
            "points": player["points"],
            "card_count": len(player["inventory"])
        }

    def clear_inventory(self, user_id):
        player = self.get_player(user_id)
        player["inventory"] = []
        self.engine.save_data()

    def grant_cards(self, user_id, count):
        player = self.get_player(user_id)
        added = []
        for _ in range(count):
            card = self.engine.generate_random_item()
            card["obtained_at"] = datetime.now().isoformat()
            player["inventory"].append(card)
            added.append(card)
        self.engine.save_data()
        return len(added)

    def pick_member_card(self, guild):
        """Pick a random member from the guild"""
        members = [m for m in guild.members if not m.bot]
        if not members:
            return self.engine.generate_random_item()
            
        target = random.choice(members)
        
        rarity_roll = random.random()
        if rarity_roll < 0.03: rarity = "UR"
        elif rarity_roll < 0.15: rarity = "SR"
        elif rarity_roll < 0.50: rarity = "R"
        else: rarity = "N"
        
        titles = ["サーバーの民", "一般市民", "村人A"]
        if rarity == "R": titles = ["熟練の戦士", "常連さん", "期待の星"]
        if rarity == "SR": titles = ["サーバーの柱", "エリート", "英雄"]
        if rarity == "UR": titles = ["伝説の存在", "神", "支配者"]
        
        title = random.choice(titles)
        
        return {
            "type": "member",
            "name": target.display_name,
            "title": title,
            "rarity": rarity,
            "image_url": target.display_avatar.url if target.display_avatar else None,
            "target_id": target.id,
            "stats": self.engine.generate_advanced_stats(rarity, "character")
        }

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
            
        player = self.get_player(message.author.id)
        now = datetime.now()
        
        # Check cooldown (1 minute)
        last_chat = player.get("last_chat_point")
        if last_chat:
            last_time = datetime.fromisoformat(last_chat)
            if now - last_time < timedelta(minutes=1):
                return
                
        # Award points
        player["points"] += 10
        player["last_chat_point"] = now.isoformat()
        self.engine.save_data()

    @tasks.loop(minutes=10)
    async def voice_points_loop(self):
        """Award points for being in VC"""
        for guild in self.bot.guilds:
            for channel in guild.voice_channels:
                for member in channel.members:
                    if member.bot: continue
                    if member.voice.self_mute or member.voice.self_deaf: continue # Skip if muted/deaf
                    
                    self.add_points(member.id, 50) # 50pts per 10 mins

    @voice_points_loop.before_loop
    async def before_voice_loop(self):
        await self.bot.wait_until_ready()

    # --- COMMANDS ---

    @app_commands.command(name="gacha", description="[ガチャ] サーバーガチャを引きます")
    @app_commands.describe(action="操作 (pull/daily/list/ranking/help)", count="回数 (1 or 10)")
    @app_commands.choices(action=[
        app_commands.Choice(name="引く (Pull)", value="pull"),
        app_commands.Choice(name="デイリー (Daily)", value="daily"),
        app_commands.Choice(name="一覧 (List)", value="list"),
        app_commands.Choice(name="ランキング (Ranking)", value="ranking"),
        app_commands.Choice(name="ヘルプ (Help)", value="help")
    ])
    async def gacha(self, interaction: discord.Interaction, action: str, count: int = 1):
        logger.info(f"Gacha command called by {interaction.user.id} with action {action}")
        
        # Global Defer to prevent timeouts
        await interaction.response.defer()
        
        try:
            player = self.get_player(interaction.user.id)
            
            if action == "help":
                embed = discord.Embed(title="🃏 ガチャシステムヘルプ", color=discord.Color.green())
                embed.add_field(name="💰 ポイントの稼ぎ方", value="1. **デイリー**: `/gacha daily` で1000pt\n2. **チャット**: 1分に1回発言で10pt\n3. **VC参加**: 10分ごとに50pt\n4. **売却**: `/gacha sell` で不要なカードを売却", inline=False)
                embed.add_field(name="🎲 ガチャ", value="`/gacha pull 1` (100pt) または `/gacha pull 10` (1000pt)", inline=False)
                embed.add_field(name="⚔️ バトル", value="`/gacha battle [相手]` で対戦！", inline=False)
                await interaction.followup.send(embed=embed)
                return

            if action == "daily":
                now = datetime.now()
                last_daily = player.get("last_daily")
                
                if last_daily:
                    last_date = datetime.fromisoformat(last_daily).date()
                    if last_date == now.date():
                        await interaction.followup.send("❌ 今日のログボは受け取り済みです。", ephemeral=True)
                        return
                
                bonus = 1000
                player["points"] += bonus
                player["last_daily"] = now.isoformat()
                self.engine.save_data()
                
                await interaction.followup.send(f"🎁 **ログインボーナス！**\n{bonus} SP を獲得しました！ (現在: {player['points']} SP)")
                return

            if action == "list":
                inventory = player["inventory"]
                if not inventory:
                    await interaction.followup.send("📭 所持カードはありません。", ephemeral=True)
                    return
                    
                rarity_order = {"LE": 5, "UR": 4, "SR": 3, "R": 2, "N": 1}
                sorted_inv = sorted(inventory, key=lambda x: rarity_order.get(x['rarity'], 0), reverse=True)
                
                desc = ""
                for i, item in enumerate(sorted_inv[:20]):
                    stats = item.get('stats', {'attack': '?', 'defense': '?'})
                    desc += f"**[{item['rarity']}]** {item['name']} (ATK:{stats['attack']})\n"
                
                if len(sorted_inv) > 20:
                    desc += f"\n...他 {len(sorted_inv) - 20} 枚"
                    
                embed = discord.Embed(title=f"📂 {interaction.user.display_name}のコレクション", description=desc, color=discord.Color.blue())
                embed.set_footer(text=f"所持ポイント: {player['points']} SP")
                await interaction.followup.send(embed=embed)
                return

            if action == "ranking":
                sorted_players = sorted(self.engine.data.items(), key=lambda x: len(x[1]['inventory']), reverse=True)
                desc = ""
                for i, (uid, p_data) in enumerate(sorted_players[:10], 1):
                    user = self.bot.get_user(int(uid))
                    name = user.display_name if user else f"User {uid}"
                    desc += f"{i}. **{name}**: {len(p_data['inventory'])} 枚\n"
                embed = discord.Embed(title="🏆 コレクターランキング", description=desc, color=discord.Color.gold())
                await interaction.followup.send(embed=embed)
                return

            if action == "sell":
                view = GachaSellView(self, interaction.user)
                await interaction.followup.send("💰 **カード売却**\n売却するカードを選択してください:", view=view, ephemeral=True)
                return

            if action == "pull":
                # Already deferred
                
                cost = 100 * count
                if player["points"] < cost:
                    await interaction.followup.send(f"❌ ポイントが足りません！ (必要: {cost} SP, 所持: {player['points']} SP)\n`/gacha daily` やチャット/VCで稼ぎましょう。", ephemeral=True)
                    return
                
                if count not in [1, 10]:
                    await interaction.followup.send("❌ 1回か10回のみ指定可能です。", ephemeral=True)
                    return

                # ANIMATION START
                msg = await interaction.followup.send("📦 **ガチャを回しています...**")
                
                await asyncio.sleep(1.0)
                await msg.edit(content="📦 **ガチャを回しています...**\n⚡ エネルギー充填中...")
                await asyncio.sleep(1.0)
                
                # Deduct points
                player["points"] -= cost
                
                results = []
                max_rarity_val = 0
                rarity_order = {"N": 1, "R": 2, "SR": 3, "UR": 4, "LE": 5}
                
                for _ in range(count):
                    if random.random() < 0.5:
                        card = self.pick_member_card(interaction.guild)
                    else:
                        card = self.engine.generate_random_item()
                    
                    card["obtained_at"] = datetime.now().isoformat()
                    results.append(card)
                    player["inventory"].append(card)
                    
                    r_val = rarity_order.get(card['rarity'], 1)
                    if r_val > max_rarity_val:
                        max_rarity_val = r_val
                
                self.engine.save_data()
                
                # Animation: Flash based on best rarity
                if max_rarity_val >= 4: # UR/LE
                    await msg.edit(content="📦 **ガチャを回しています...**\n🌈 **虹色の光が溢れ出す...！！**")
                    await asyncio.sleep(1.5)
                elif max_rarity_val == 3: # SR
                    await msg.edit(content="📦 **ガチャを回しています...**\n🟨 **金色の光だ！！**")
                    await asyncio.sleep(1.0)
                else:
                    await msg.edit(content="📦 **ガチャを回しています...**\n⬜ パカッ")
                    await asyncio.sleep(0.5)

                # Generate Image
                await msg.edit(content="🎨 **結果画像を生成中...**")
                logger.info(f"Starting image generation for {count} items...")
                try:
                    if count == 1:
                        card = results[0]
                        logger.info(f"Generating single card for {card['name']}")
                        img = await self.card_gen.generate_card(
                            card['title'], card['name'], card['rarity'], card['image_url'], card['type'], card.get('stats'), card.get('image_path')
                        )
                        filename = "gacha_result.png"
                    else:
                        logger.info(f"Generating result image for {len(results)} items")
                        img = await self.card_gen.generate_result_image(results)
                        filename = "gacha_results.png"
                    
                    logger.info("Image generation completed. Preparing file...")
                    file_bytes = self.card_gen.get_bytes(img)
                    file = discord.File(file_bytes, filename=filename)
                    
                    summary = " ".join([f"[{r['rarity']}]" for r in results])
                    logger.info("Sending gacha result message...")
                    await msg.edit(content=f"🎉 **ガチャ結果！**\n{summary}", attachments=[file])
                    logger.info("Gacha result message sent.")
                    
                except Exception as e:
                    logger.error(f"Gacha image error: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    await msg.edit(content=f"🎉 **ガチャ結果！** (画像生成エラー: {e})\n" + "\n".join([f"[{r['rarity']}] {r['name']}" for r in results]))
        
        except Exception as e:
            logger.error(f"Gacha command error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            await interaction.followup.send(f"❌ エラーが発生しました: {e}", ephemeral=True)



    @app_commands.command(name="gacha_generate_assets", description="[Admin] ガチャアイテムの画像を生成します")
    @app_commands.default_permissions(administrator=True)
    async def generate_assets(self, interaction: discord.Interaction):
        image_cog = self.bot.get_cog("ImageGenCog")
        if not image_cog or not image_cog.available:
            await interaction.response.send_message("❌ ImageGenCogが利用できないため、画像を生成できません。", ephemeral=True)
            return

        await interaction.response.send_message("🎨 **アイテム画像の生成を開始します...**\nこれには時間がかかります。", ephemeral=True)
        
        assets_dir = "data/gacha/images"
        if not os.path.exists(assets_dir):
            os.makedirs(assets_dir)
            
        generated_count = 0
        # Use engine's ITEM_NAMES if possible, but they are not exposed as property.
        # We can import them or just expose them in engine.
        # For now, let's assume we can access them via a new method or just hardcode/import.
        # Actually, I removed them from this file. I should import them from engine or expose them.
        from utils.gacha_engine import ITEM_NAMES
        
        for item_name in ITEM_NAMES:
            file_path = os.path.join(assets_dir, f"{item_name}.png")
            if os.path.exists(file_path):
                continue
                
            try:
                # Generate
                prompt = f"RPG game icon, {item_name}, fantasy style, high quality, white background"
                image_data = await image_cog.generate_image(prompt)
                
                if image_data:
                    with open(file_path, "wb") as f:
                        f.write(image_data)
                    generated_count += 1
                    logger.info(f"Generated asset for {item_name}")
                    await asyncio.sleep(2) # Prevent rate limit
                else:
                    logger.warning(f"Failed to generate asset for {item_name}")
                    
            except Exception as e:
                logger.error(f"Asset gen error for {item_name}: {e}")
                
        await interaction.followup.send(f"✅ **画像生成完了**: {generated_count} 枚の画像を生成しました。", ephemeral=True)

    @app_commands.command(name="gacha_distribute_starter", description="[Admin] 全プレイヤーにNカードを1枚配布します")
    @app_commands.default_permissions(administrator=True)
    async def distribute_starter(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        count = 0
        for i, (uid, player) in enumerate(self.engine.data.items()):
            if i % 100 == 0: await asyncio.sleep(0) # Yield every 100 users
            
            # Generate N card
            card = self.engine.generate_random_item()
            # Force N rarity for starter (Safety limit 10 tries)
            tries = 0
            while card["rarity"] != "N" and tries < 10:
                card = self.engine.generate_random_item()
                tries += 1
            
            if card["rarity"] != "N":
                card["rarity"] = "N" # Force overwrite if RNG fails
                card["stats"] = self.engine.generate_advanced_stats("N", card["type"])

            card["obtained_at"] = datetime.now().isoformat()
            player["inventory"].append(card)
            count += 1
            
        self.engine.save_data()
        await interaction.followup.send(f"✅ **配布完了**: {count} 人のプレイヤーにスターターカード(N)を配布しました。", ephemeral=True)

    @app_commands.command(name="gacha", description="[ガチャ] サーバーガチャを引きます")
    @app_commands.describe(action="操作 (pull/daily/list/ranking/sell/help)", count="回数 (1 or 10)")
    @app_commands.choices(action=[
        app_commands.Choice(name="引く (Pull)", value="pull"),
        app_commands.Choice(name="デイリー (Daily)", value="daily"),
        app_commands.Choice(name="一覧 (List)", value="list"),
        app_commands.Choice(name="売却 (Sell)", value="sell"),
        app_commands.Choice(name="ランキング (Ranking)", value="ranking"),
        app_commands.Choice(name="ヘルプ (Help)", value="help")
    ])
    async def gacha(self, interaction: discord.Interaction, action: str, count: int = 1):
        player = self.get_player(interaction.user.id)
        
        if action == "help":
            embed = discord.Embed(title="🃏 ガチャシステムヘルプ", color=discord.Color.green())
            embed.add_field(name="💰 ポイントの稼ぎ方", value="1. **デイリー**: `/gacha daily` で1000pt\n2. **チャット**: 1分に1回発言で10pt\n3. **VC参加**: 10分ごとに50pt\n4. **売却**: `/gacha sell` で不要なカードを売却", inline=False)
            embed.add_field(name="🎲 ガチャ", value="`/gacha pull 1` (100pt) または `/gacha pull 10` (1000pt)", inline=False)
            embed.add_field(name="⚔️ バトル", value="`/gacha battle [相手]` で対戦！", inline=False)
            await interaction.response.send_message(embed=embed)
            return

        if action == "sell":
            view = GachaSellView(self, interaction.user)
            await interaction.response.send_message("💰 **カード売却**\n売却するカードを選択してください:", view=view, ephemeral=True)
            return
    @app_commands.describe(opponent="対戦相手")
    async def battle(self, interaction: discord.Interaction, opponent: discord.User):
        try:
            if opponent.bot or opponent.id == interaction.user.id:
                await interaction.response.send_message("❌ 無効な対戦相手です。", ephemeral=True)
                return

            p1 = self.get_player(interaction.user.id)
            p2 = self.get_player(opponent.id)
            
            if not p1["inventory"] or not p2["inventory"]:
                await interaction.response.send_message("❌ カードが足りません。", ephemeral=True)
                return

            embed = discord.Embed(title="⚔️ デュエル申し込み (Advanced)", description=f"{interaction.user.mention} が {opponent.mention} にバトルを挑んでいます！\n\n**3ターン制・スキルあり・フィールド効果あり**", color=discord.Color.red())
            view = BattleChallengeView(self, interaction.user, opponent)
            await interaction.response.send_message(content=opponent.mention, embed=embed, view=view)
        except Exception as e:
            import traceback
            logger.error(traceback.format_exc())
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ エラーが発生しました: {e}", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ エラーが発生しました: {e}", ephemeral=True)

class BattleChallengeView(discord.ui.View):
    def __init__(self, cog, challenger, opponent):
        super().__init__(timeout=60)
        self.cog = cog
        self.challenger = challenger
        self.opponent = opponent
        self.accepted = False

    @discord.ui.button(label="受けて立つ！", style=discord.ButtonStyle.danger, emoji="⚔️")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.opponent.id:
            await interaction.response.send_message("❌ あなたへの挑戦状ではありません。", ephemeral=True)
            return
        
        self.accepted = True
        self.stop()
        
        # Start Card Selection
        await interaction.response.send_message("🔥 **バトル開始！**\nお互いに使用するカードを選択してください。", ephemeral=False)
        
        view = BattleCardSelectLaunchView(self.cog, self.challenger, self.opponent)
        await interaction.channel.send("👇 以下のボタンを押して、使用するカードを選んでください！", view=view)

    @discord.ui.button(label="逃げる", style=discord.ButtonStyle.secondary, emoji="💨")
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.opponent.id:
            await interaction.response.send_message("❌ あなたへの挑戦状ではありません。", ephemeral=True)
            return
            
        await interaction.response.edit_message(content=f"💨 {self.opponent.display_name} は逃げ出した...", view=None, embed=None)
        self.stop()

class BattleCardSelectLaunchView(discord.ui.View):
    def __init__(self, cog, p1, p2):
        super().__init__(timeout=180)
        self.cog = cog
        self.p1 = p1
        self.p2 = p2
        self.decks = {p1.id: {}, p2.id: {}} # {main, equip, support}

    async def check_ready(self, channel):
        p1_ready = len(self.decks[self.p1.id]) == 3
        p2_ready = len(self.decks[self.p2.id]) == 3
        
        if p1_ready and p2_ready:
            self.stop()
            await self.start_battle(channel)

    async def start_battle(self, channel):
        from utils.gacha_engine import FIELDS
        
        # Generate Field
        field_key = random.choice(list(FIELDS.keys()))
        field = FIELDS[field_key]
        
        embed = discord.Embed(title=f"🌋 バトル開始！ フィールド: {field['name']}", description=f"属性ボーナス: {field['buff']}", color=discord.Color.orange())
        await channel.send(embed=embed)
        
        # Init State
        p1_data = {"id": self.p1.id, "name": self.p1.display_name}
        p2_data = {"id": self.p2.id, "name": self.p2.display_name}
        
        state = EngineBattleState(p1_data, p2_data, self.decks[self.p1.id], self.decks[self.p2.id], field, self.cog.engine)
        
        # Start Turn 1
        await self.run_turn(channel, state)

    async def run_turn(self, channel, state):
        if state.turn > 3 or state.p1_hp <= 0 or state.p2_hp <= 0:
            await self.end_battle(channel, state)
            return

        await asyncio.sleep(2)
        log = state.process_turn()
        
        # Status Embed
        embed = discord.Embed(title=f"Turn {state.turn-1} Result", description=log, color=discord.Color.light_grey())
        embed.add_field(name=f"{self.p1.display_name}", value=f"HP: {state.p1_hp}/{state.p1_stats['hp']}", inline=True)
        embed.add_field(name=f"{self.p2.display_name}", value=f"HP: {state.p2_hp}/{state.p2_stats['hp']}", inline=True)
        await channel.send(embed=embed)
        
        if state.p1_hp <= 0 or state.p2_hp <= 0 or state.turn > 3:
            await self.end_battle(channel, state)
        else:
            # Intermission
            view = BattleIntermissionView(self.cog, self.p1, self.p2, state, self, channel)
            await channel.send(f"⏳ **インターミッション (Turn {state.turn-1} 終了)**\nアイテムを使用するか、次のターンへ進んでください。", view=view)

    async def end_battle(self, channel, state):
        # Result
        winner = self.p1 if state.p1_hp > 0 else self.p2
        loser = self.p2 if winner == self.p1 else self.p1
        
        if state.p1_hp <= 0 and state.p2_hp <= 0:
            await channel.send("💀 **引き分け！** 両者倒れました...")
            return

        bet = 100
        self.cog.add_points(winner.id, bet)
        self.cog.add_points(loser.id, -bet)
        
        await channel.send(f"🏆 **勝者: {winner.display_name}**\n{bet} SP を獲得しました！")

    @discord.ui.button(label="デッキ編成 (Player 1)", style=discord.ButtonStyle.primary, custom_id="p1_deck")
    async def select_p1(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.p1.id:
            await interaction.response.send_message("❌ あなたは Player 1 ではありません。", ephemeral=True)
            return
        view = BattleDeckSelectView(self.cog, interaction.user, self)
        await interaction.response.send_message("カードを3枚（メイン・装備・サポート）選んでください:", view=view, ephemeral=True)

    @discord.ui.button(label="デッキ編成 (Player 2)", style=discord.ButtonStyle.danger, custom_id="p2_deck")
    async def select_p2(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.p2.id:
            await interaction.response.send_message("❌ あなたは Player 2 ではありません。", ephemeral=True)
            return
        view = BattleDeckSelectView(self.cog, interaction.user, self)
        await interaction.response.send_message("カードを3枚（メイン・装備・サポート）選んでください:", view=view, ephemeral=True)

class BattleIntermissionView(discord.ui.View):
    def __init__(self, cog, p1, p2, state, battle_manager, channel):
        super().__init__(timeout=60)
        self.cog = cog
        self.p1 = p1
        self.p2 = p2
        self.state = state
        self.battle_manager = battle_manager
        self.channel = channel
        self.ready = {p1.id: False, p2.id: False}
        self.used_item = {p1.id: False, p2.id: False}

    async def check_ready(self, interaction):
        if self.ready[self.p1.id] and self.ready[self.p2.id]:
            self.stop()
            await interaction.channel.send("⚔️ **両者の準備完了！ 次のターンへ！**")
            await self.battle_manager.run_turn(self.channel, self.state)

    @discord.ui.button(label="アイテムを使う", style=discord.ButtonStyle.success, emoji="🧪")
    async def use_item(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id not in [self.p1.id, self.p2.id]:
            await interaction.response.send_message("❌ 観戦者は操作できません。", ephemeral=True)
            return
            
        if self.used_item[user_id]:
            await interaction.response.send_message("❌ アイテムは1ターンに1回までです。", ephemeral=True)
            return

        view = BattleItemSelectView(self.cog, interaction.user, self)
        await interaction.response.send_message("使用するアイテムを選んでください:", view=view, ephemeral=True)

    @discord.ui.button(label="準備完了 / スキップ", style=discord.ButtonStyle.primary, emoji="✅")
    async def ready_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id not in [self.p1.id, self.p2.id]:
            await interaction.response.send_message("❌ 観戦者は操作できません。", ephemeral=True)
            return
            
        self.ready[user_id] = True
        await interaction.response.send_message(f"✅ {interaction.user.display_name} は準備完了！", ephemeral=False)
        await self.check_ready(interaction)

class BattleItemSelectView(discord.ui.View):
    def __init__(self, cog, user, intermission_view):
        super().__init__(timeout=60)
        self.cog = cog
        self.user = user
        self.intermission_view = intermission_view
        
        # Populate items
        player = self.cog.get_player(user.id)
        inventory = player["inventory"]
        
        options = []
        # Filter for items that look usable (or just first 25 items for now)
        for i, card in enumerate(inventory[:25]):
            if "stats" not in card: card["stats"] = self.cog.engine.generate_advanced_stats(card["rarity"], "item")
            
            label = f"[{card['rarity']}] {card['name']}"
            desc = "使用して効果を発動"
            options.append(discord.SelectOption(label=label[:100], description=desc, value=str(i)))
            
        if not options:
            options.append(discord.SelectOption(label="アイテムがありません", value="none"))
            
        select = discord.ui.Select(placeholder="アイテムを選択...", options=options, disabled=(not options))
        select.callback = self.callback
        self.add_item(select)

    async def callback(self, interaction: discord.Interaction):
        if self.intermission_view.used_item[self.user.id]:
             await interaction.response.send_message("❌ 既にアイテムを使用しました。", ephemeral=True)
             return

        val = interaction.data['values'][0]
        if val == "none": return
        
        idx = int(val)
        player = self.cog.get_player(self.user.id)
        card = player["inventory"][idx]
        
        # Apply Effect
        log = self.intermission_view.state.apply_item(self.user.id, card)
        self.intermission_view.used_item[self.user.id] = True
        
        await interaction.response.send_message(f"🧪 **アイテム使用**: {card['name']}\n{log}", ephemeral=False)

class BattleDeckSelectView(discord.ui.View):
    def __init__(self, cog, user, parent_view):
        super().__init__(timeout=120)
        self.cog = cog
        self.user = user
        self.parent_view = parent_view
        self.step = 0 # 0: Main, 1: Equip, 2: Support
        
        self.update_select()

    def update_select(self):
        self.clear_items()
        player = self.cog.get_player(self.user.id)
        inventory = player["inventory"]
        
        steps = ["メインキャラ", "装備", "サポート"]
        
        # Filter Logic
        filtered_inventory = []
        for i, card in enumerate(inventory):
            # Ensure stats exist (migration)
            if "stats" not in card: card["stats"] = self.cog.engine.generate_advanced_stats(card["rarity"], "item")
            
            ctype = card.get("type", "item")
            
            if self.step == 0: # Main
                if ctype in ["character", "member"]:
                    filtered_inventory.append((i, card))
            elif self.step == 1: # Equip
                if ctype in ["weapon", "armor"]:
                    filtered_inventory.append((i, card))
            elif self.step == 2: # Support
                if ctype in ["accessory", "item", "character", "member"]: # Allow chars as support too
                    filtered_inventory.append((i, card))

        options = []
        # Show top 25 of filtered
        for i, card in filtered_inventory[:25]:
            s = card["stats"]
            label = f"[{card['rarity']}] {card['name']}"
            desc = f"{s.get('element','N')} | ATK:{s.get('attack')} HP:{s.get('hp')}"
            options.append(discord.SelectOption(label=label[:100], description=desc[:100], value=str(i)))
            
        if not options:
            options.append(discord.SelectOption(label="選択可能なカードがありません", value="none"))
            
        select = discord.ui.Select(placeholder=f"{steps[self.step]}を選択...", options=options, disabled=(not options or options[0].value == "none"))
        select.callback = self.callback
        self.add_item(select)



    async def callback(self, interaction: discord.Interaction):
        idx = int(interaction.data['values'][0])
        player = self.cog.get_player(self.user.id)
        card = player["inventory"][idx]
        
        # Ensure stats
        if "stats" not in card or "hp" not in card["stats"]:
            card["stats"] = self.cog.engine.generate_advanced_stats(card["rarity"], "item")
        
        if self.step == 0:
            self.parent_view.decks[self.user.id]["main"] = card
            self.step = 1
            self.update_select()
            await interaction.response.edit_message(content="次は **装備カード** を選んでください:", view=self)
        elif self.step == 1:
            self.parent_view.decks[self.user.id]["equip"] = card
            self.step = 2
            self.update_select()
            await interaction.response.edit_message(content="最後は **サポートカード** を選んでください:", view=self)
        elif self.step == 2:
            self.parent_view.decks[self.user.id]["support"] = card
            await interaction.response.edit_message(content="✅ デッキ編成完了！", view=None)
            await self.parent_view.check_ready(interaction.channel)

class GachaSellView(discord.ui.View):
    def __init__(self, cog, user):
        super().__init__(timeout=120)
        self.cog = cog
        self.user = user
        self.update_select()

    def update_select(self):
        self.clear_items()
        player = self.cog.get_player(self.user.id)
        inventory = player["inventory"]
        
        options = []
        # Show top 25 items
        for i, card in enumerate(inventory[:25]):
            rarity = card['rarity']
            value = {"N": 10, "R": 50, "SR": 300, "UR": 1000, "LE": 5000}.get(rarity, 10)
            
            label = f"[{rarity}] {card['name']} (+{value} SP)"
            desc = f"売却してポイントに変換"
            options.append(discord.SelectOption(label=label[:100], description=desc, value=str(i)))
            
        if not options:
            options.append(discord.SelectOption(label="売却可能なカードがありません", value="none"))
            
        select = discord.ui.Select(placeholder="売却するカードを選択...", options=options, disabled=(not options or options[0].value == "none"))
        select.callback = self.callback
        self.add_item(select)

    async def callback(self, interaction: discord.Interaction):
        idx = int(interaction.data['values'][0])
        player = self.cog.get_player(self.user.id)
        
        if idx >= len(player["inventory"]):
            await interaction.response.send_message("❌ エラー: カードが見つかりません。", ephemeral=True)
            return
            
        card = player["inventory"].pop(idx)
        rarity = card['rarity']
        value = {"N": 10, "R": 50, "SR": 300, "UR": 1000, "LE": 5000}.get(rarity, 10)
        
        self.cog.add_points(self.user.id, value)
        
        await interaction.response.send_message(f"💰 **売却完了**: {card['name']} を {value} SP で売却しました。", ephemeral=True)
        
        # Refresh view
        self.update_select()
        await interaction.message.edit(view=self)

async def setup(bot):
    await bot.add_cog(GachaCog(bot))
