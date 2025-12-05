import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
import random
import logging
from enum import Enum, auto

logger = logging.getLogger(__name__)

class GamePhase(Enum):
    RECRUITMENT = auto()
    NIGHT = auto()
    DAY = auto()
    VOTE = auto()
    RESULT = auto()

class Role(Enum):
    VILLAGER = "村人"
    WEREWOLF = "人狼"
    SEER = "占い師"
    BODYGUARD = "騎士"
    MEDIUM = "霊媒師"
    MADMAN = "狂人"

class Player:
    def __init__(self, member: discord.Member):
        self.member = member
        self.role = Role.VILLAGER
        self.is_alive = True
        self.voted_for = None
        self.protected = False
        self.has_acted = False

class WerewolfGame:
    def __init__(self, channel: discord.TextChannel, bot):
        self.channel = channel
        self.bot = bot
        self.phase = GamePhase.RECRUITMENT
        self.players = {}  # user_id: Player
        self.host_id = None
        self.settings = {
            "day_time": 300,  # seconds
            "night_time": 60, # seconds
            "roles": {} # Will be populated based on player count
        }
        self.timer_task = None
        self.message_cache = [] # To clean up game messages

    async def add_player(self, member: discord.Member):
        if member.id not in self.players:
            self.players[member.id] = Player(member)
            return True
        return False

    async def remove_player(self, member_id: int):
        if member_id in self.players:
            del self.players[member_id]
            return True
        return False

    def assign_roles(self):
        player_ids = list(self.players.keys())
        random.shuffle(player_ids)
        count = len(player_ids)
        
        # Simple role distribution logic
        roles_dist = []
        if count <= 4:
            roles_dist = [Role.WEREWOLF, Role.SEER] + [Role.VILLAGER] * (count - 2)
        elif count <= 6:
            roles_dist = [Role.WEREWOLF, Role.SEER, Role.BODYGUARD] + [Role.VILLAGER] * (count - 3)
        else:
            roles_dist = [Role.WEREWOLF, Role.WEREWOLF, Role.SEER, Role.BODYGUARD, Role.MEDIUM, Role.MADMAN] + [Role.VILLAGER] * (count - 6)
        
        # Adjust if custom settings (future)
        
        for i, uid in enumerate(player_ids):
            if i < len(roles_dist):
                self.players[uid].role = roles_dist[i]
            else:
                self.players[uid].role = Role.VILLAGER

    async def send_dm(self, user_id, content, view=None):
        player = self.players.get(user_id)
        if player:
            try:
                await player.member.send(content, view=view)
            except discord.Forbidden:
                await self.channel.send(f"⚠️ {player.member.mention} にDMを送れませんでした。プライバシー設定を確認してください。")

class SettingsView(discord.ui.View):
    def __init__(self, game: WerewolfGame):
        super().__init__(timeout=60)
        self.game = game

    @discord.ui.select(placeholder="昼の議論時間", options=[
        discord.SelectOption(label="3分", value="180"),
        discord.SelectOption(label="5分", value="300", default=True),
        discord.SelectOption(label="10分", value="600"),
    ])
    async def select_time(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.game.settings["day_time"] = int(select.values[0])
        await interaction.response.send_message(f"⏰ 昼の時間を {int(select.values[0])//60}分 に設定しました。", ephemeral=True)

class RecruitmentView(discord.ui.View):
    def __init__(self, game: WerewolfGame):
        super().__init__(timeout=None)
        self.game = game

    @discord.ui.button(label="参加する", style=discord.ButtonStyle.green, emoji="✋")
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.game.add_player(interaction.user):
            await interaction.response.send_message(f"{interaction.user.mention} が参加しました！ (現在: {len(self.game.players)}人)", ephemeral=False)
        else:
            await interaction.response.send_message("既に参加しています。", ephemeral=True)

    @discord.ui.button(label="設定", style=discord.ButtonStyle.secondary, emoji="⚙️")
    async def settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.game.host_id:
            await interaction.response.send_message("設定はホストのみ変更可能です。", ephemeral=True)
            return
        await interaction.response.send_message("設定メニュー:", view=SettingsView(self.game), ephemeral=True)

    @discord.ui.button(label="開始", style=discord.ButtonStyle.danger, emoji="🚀")
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.game.host_id:
            await interaction.response.send_message("開始できるのはホストのみです。", ephemeral=True)
            return
        if len(self.game.players) < 3: # Minimum 3 for testing, usually 4+
            await interaction.response.send_message("参加者が足りません（最低3人）。", ephemeral=True)
            return
        
        await interaction.response.defer()
        # Disable buttons
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)
        
        # Start Game
        cog = self.game.bot.get_cog("WerewolfCog")
        if cog:
            await cog.start_game_logic(self.game)

class NightActionView(discord.ui.View):
    def __init__(self, game: WerewolfGame, player: Player, targets: list):
        super().__init__(timeout=None)
        self.game = game
        self.player = player
        
        # Create select menu for targets
        options = []
        for target in targets:
            options.append(discord.SelectOption(label=target.member.display_name, value=str(target.member.id)))
            
        select = discord.ui.Select(placeholder="対象を選択してください", options=options)
        select.callback = self.callback
        self.add_item(select)

    async def callback(self, interaction: discord.Interaction):
        target_id = int(interaction.data['values'][0])
        target = self.game.players.get(target_id)
        
        cog = self.game.bot.get_cog("WerewolfCog")
        if cog:
            await cog.handle_night_action(self.game, self.player, target_id, interaction)

class VoteView(discord.ui.View):
    def __init__(self, game: WerewolfGame):
        super().__init__(timeout=None)
        self.game = game
        
        options = []
        for uid, p in self.game.players.items():
            if p.is_alive:
                options.append(discord.SelectOption(label=p.member.display_name, value=str(uid)))
        
        select = discord.ui.Select(placeholder="処刑する人を選択", options=options)
        select.callback = self.callback
        self.add_item(select)

    async def callback(self, interaction: discord.Interaction):
        target_id = int(interaction.data['values'][0])
        player = self.game.players.get(interaction.user.id)
        if player and player.is_alive:
            player.voted_for = target_id
            await interaction.response.send_message(f"{self.game.players[target_id].member.display_name} に投票しました。", ephemeral=True)
            
            # Check if all voted
            alive_count = sum(1 for p in self.game.players.values() if p.is_alive)
            voted_count = sum(1 for p in self.game.players.values() if p.is_alive and p.voted_for is not None)
            
            if voted_count >= alive_count:
                cog = self.game.bot.get_cog("WerewolfCog")
                if cog:
                    await cog.end_day_vote(self.game)

class WerewolfCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = {} # channel_id: WerewolfGame

    # Command Group
    jinrou = app_commands.Group(name="jinrou", description="人狼ゲーム")

    @jinrou.command(name="create", description="人狼ゲームの募集を開始します")
    async def create(self, interaction: discord.Interaction):
        if interaction.channel_id in self.games:
            await interaction.response.send_message("このチャンネルでは既にゲームが進行中です。", ephemeral=True)
            return

        game = WerewolfGame(interaction.channel, self.bot)
        game.host_id = interaction.user.id
        await game.add_player(interaction.user)
        self.games[interaction.channel_id] = game

        embed = discord.Embed(title="🐺 人狼ゲーム募集開始", description="参加者はボタンを押してください！", color=0x990000)
        embed.add_field(name="ホスト", value=interaction.user.mention)
        embed.set_footer(text="最低3人から開始可能です")

        await interaction.response.send_message(embed=embed, view=RecruitmentView(game))

    @jinrou.command(name="stop", description="ゲームを強制終了します")
    async def stop(self, interaction: discord.Interaction):
        if interaction.channel_id in self.games:
            del self.games[interaction.channel_id]
            await interaction.response.send_message("ゲームを強制終了しました。")
        else:
            await interaction.response.send_message("進行中のゲームはありません。", ephemeral=True)

    async def start_game_logic(self, game: WerewolfGame):
        game.phase = GamePhase.NIGHT
        game.assign_roles()
        
        # Announce Roles via DM
        for uid, player in game.players.items():
            role_name = player.role.value
            await game.send_dm(uid, f"あなたの役職は **{role_name}** です。")
            
        await game.channel.send("🌑 **夜が来ました...**\n能力者はDMを確認して行動してください。")
        
        # Night Logic
        await self.process_night_phase(game)

    async def process_night_phase(self, game: WerewolfGame):
        # Reset nightly states
        self.night_actions = {} # uid: target_id
        
        targets = [p for p in game.players.values() if p.is_alive]
        
        for uid, player in game.players.items():
            if not player.is_alive: continue
            
            if player.role == Role.WEREWOLF:
                # Werewolves see each other
                wolves = [p.member.display_name for p in game.players.values() if p.role == Role.WEREWOLF]
                await game.send_dm(uid, f"仲間の人狼: {', '.join(wolves)}\n襲撃先を選んでください。", view=NightActionView(game, player, targets))
            
            elif player.role == Role.SEER:
                others = [p for p in targets if p.member.id != uid]
                await game.send_dm(uid, "占う相手を選んでください。", view=NightActionView(game, player, others))
                
            elif player.role == Role.BODYGUARD:
                others = [p for p in targets if p.member.id != uid]
                await game.send_dm(uid, "護衛する相手を選んでください。", view=NightActionView(game, player, others))

        # Wait for actions (Fixed time for simplicity in MVP)
        await asyncio.sleep(game.settings["night_time"])
        await self.resolve_night(game)

    async def handle_night_action(self, game, player, target_id, interaction):
        # Store action
        if not hasattr(game, 'night_actions'): game.night_actions = {}
        game.night_actions[player.member.id] = target_id
        
        await interaction.response.send_message("行動を受け付けました。", ephemeral=True)
        # Disable view
        await interaction.message.edit(view=None)

    async def resolve_night(self, game: WerewolfGame):
        # Process actions
        victim_id = None
        protected_id = None
        
        # 1. Bodyguard
        for uid, target in getattr(game, 'night_actions', {}).items():
            if game.players[uid].role == Role.BODYGUARD:
                protected_id = target
        
        # 2. Werewolf (Majority vote or random if split)
        wolf_votes = {}
        for uid, target in getattr(game, 'night_actions', {}).items():
            if game.players[uid].role == Role.WEREWOLF:
                wolf_votes[target] = wolf_votes.get(target, 0) + 1
        
        if wolf_votes:
            victim_id = max(wolf_votes, key=wolf_votes.get)
        
        # 3. Seer (Send results immediately when they act? Or now? Let's do immediate in callback for better UX, but here is fine too. 
        # Actually, Seer needs result NOW. So Seer logic should be in handle_night_action or separate.)
        # For MVP, let's assume Seer got result in callback (Requires refactoring handle_night_action).
        # Let's just process Seer here and DM them.
        for uid, target in getattr(game, 'night_actions', {}).items():
            if game.players[uid].role == Role.SEER:
                target_role = game.players[target].role
                is_wolf = target_role == Role.WEREWOLF
                result = "人狼" if is_wolf else "人間"
                await game.send_dm(uid, f"占い結果: {game.players[target].member.display_name} は **{result}** です。")

        # Resolution
        death_message = "昨晩は誰も死にませんでした。"
        if victim_id and victim_id != protected_id:
            game.players[victim_id].is_alive = False
            death_message = f"昨晩、**{game.players[victim_id].member.display_name}** が無残な姿で発見されました..."
        
        await game.channel.send(f"🌅 **朝が来ました。**\n{death_message}")
        
        if await self.check_win_condition(game):
            return

        # Start Day
        await self.start_day_phase(game)

    async def start_day_phase(self, game: WerewolfGame):
        game.phase = GamePhase.DAY
        seconds = game.settings["day_time"]
        await game.channel.send(f"☀️ 議論を開始してください。（残り時間: {seconds//60}分）")
        
        # Timer
        await asyncio.sleep(seconds)
        await self.start_vote_phase(game)

    async def start_vote_phase(self, game: WerewolfGame):
        game.phase = GamePhase.VOTE
        # Reset votes
        for p in game.players.values():
            p.voted_for = None
            
        await game.channel.send("🗳️ **投票の時間です。**\n処刑したい人を選んでください。", view=VoteView(game))

    async def end_day_vote(self, game: WerewolfGame):
        # Count votes
        votes = {}
        for p in game.players.values():
            if p.is_alive and p.voted_for:
                votes[p.voted_for] = votes.get(p.voted_for, 0) + 1
        
        if not votes:
            await game.channel.send("投票が行われませんでした。処刑なし。")
            await self.start_game_logic(game) # Back to Night
            return

        executed_id = max(votes, key=votes.get)
        # Handle ties (Random for MVP)
        max_votes = votes[executed_id]
        candidates = [uid for uid, count in votes.items() if count == max_votes]
        executed_id = random.choice(candidates)
        
        executed_player = game.players[executed_id]
        executed_player.is_alive = False
        
        await game.channel.send(f"投票の結果、**{executed_player.member.display_name}** が処刑されました。")
        
        # Medium Result
        for uid, p in game.players.items():
            if p.role == Role.MEDIUM and p.is_alive:
                is_wolf = executed_player.role == Role.WEREWOLF
                result = "人狼" if is_wolf else "人間"
                await game.send_dm(uid, f"霊媒結果: 処刑された {executed_player.member.display_name} は **{result}** でした。")

        if await self.check_win_condition(game):
            return
            
        await self.start_game_logic(game) # Back to Night

    async def check_win_condition(self, game: WerewolfGame):
        wolves = sum(1 for p in game.players.values() if p.is_alive and p.role == Role.WEREWOLF)
        humans = sum(1 for p in game.players.values() if p.is_alive and p.role != Role.WEREWOLF)
        
        if wolves == 0:
            await game.channel.send("🎉 **村人陣営の勝利です！** 人狼は全滅しました。")
            self.cleanup_game(game)
            return True
        elif wolves >= humans:
            await game.channel.send("🐺 **人狼陣営の勝利です！** 村は食い尽くされました...")
            self.cleanup_game(game)
            return True
        return False

    def cleanup_game(self, game: WerewolfGame):
        # Reveal roles
        role_reveal = "\n".join([f"{p.member.display_name}: {p.role.value}" for p in game.players.values()])
        asyncio.create_task(game.channel.send(f"**役職内訳:**\n{role_reveal}"))
        
        if game.channel.id in self.games:
            del self.games[game.channel.id]

async def setup(bot):
    await bot.add_cog(WerewolfCog(bot))
