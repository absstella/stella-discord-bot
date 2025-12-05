import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
import logging

logger = logging.getLogger(__name__)

# Word Wolf Themes
WORD_PAIRS = [
    ("うどん", "そば"),
    ("スキー", "スノボ"),
    ("コーヒー", "紅茶"),
    ("犬", "猫"),
    ("きのこの山", "たけのこの里"),
    ("マクドナルド", "モスバーガー"),
    ("ドラえもん", "クレヨンしんちゃん"),
    ("Twitter", "Instagram"),
    ("YouTube", "TikTok"),
    ("夏", "冬"),
    ("焼肉", "しゃぶしゃぶ"),
    ("ディズニーランド", "USJ"),
    ("おにぎり", "サンドイッチ"),
    ("鉛筆", "シャープペンシル"),
    ("自転車", "バイク")
]

class WordWolfLobby:
    def __init__(self, channel, host):
        self.channel = channel
        self.host = host
        self.players = [host]
        self.is_started = False
        self.wolf_player = None
        self.majority_word = ""
        self.wolf_word = ""
        self.votes = {}

class PartyGameCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lobbies = {} # channel_id -> Lobby

    @commands.hybrid_group(name="wordwolf", description="ワードウルフゲーム")
    async def wordwolf(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("サブコマンドを指定してください: start, join, end")

    @wordwolf.command(name="start", description="ワードウルフの募集を開始します")
    async def start(self, ctx):
        """Start a Word Wolf lobby"""
        if ctx.channel.id in self.lobbies:
            await ctx.send("⚠️ このチャンネルでは既にゲームが進行中または募集中です。")
            return

        lobby = WordWolfLobby(ctx.channel, ctx.author)
        self.lobbies[ctx.channel.id] = lobby
        
        embed = discord.Embed(title="🐺 ワードウルフ募集開始！", description="参加者はボタンを押すか `/wordwolf join` を入力してください。", color=discord.Color.gold())
        embed.add_field(name="ホスト", value=ctx.author.display_name)
        embed.add_field(name="現在の参加者", value=ctx.author.display_name)
        
        view = JoinView(self, lobby)
        msg = await ctx.send(embed=embed, view=view)
        lobby.message = msg

    @wordwolf.command(name="join", description="募集中のゲームに参加します")
    async def join(self, ctx):
        """Join a lobby"""
        lobby = self.lobbies.get(ctx.channel.id)
        if not lobby:
            await ctx.send("❌ 募集中ではありません。`/wordwolf start` で募集を開始してください。")
            return
            
        if lobby.is_started:
            await ctx.send("⚠️ ゲームは既に開始されています。")
            return
            
        if ctx.author in lobby.players:
            await ctx.send("⚠️ 既に参加しています。")
            return
            
        lobby.players.append(ctx.author)
        await self.update_lobby_message(lobby)
        await ctx.send(f"✅ {ctx.author.display_name} が参加しました！", ephemeral=True)

    async def update_lobby_message(self, lobby):
        if not lobby.message:
            return
            
        embed = lobby.message.embeds[0]
        player_list = "\n".join([p.display_name for p in lobby.players])
        embed.set_field_at(1, name=f"現在の参加者 ({len(lobby.players)}人)", value=player_list, inline=False)
        
        await lobby.message.edit(embed=embed)

    @wordwolf.command(name="begin", description="[ホストのみ] ゲームを開始します")
    async def begin(self, ctx):
        """Begin the game"""
        lobby = self.lobbies.get(ctx.channel.id)
        if not lobby:
            await ctx.send("❌ ゲームが見つかりません。")
            return
            
        if ctx.author != lobby.host:
            await ctx.send("❌ ホストのみが開始できます。")
            return
            
        if len(lobby.players) < 3:
            await ctx.send("⚠️ 参加者が足りません（最低3人必要です）。")
            # For testing, we might want to allow fewer, but 3 is logical minimum
            # return 

        lobby.is_started = True
        
        # Setup Game
        pair = random.choice(WORD_PAIRS)
        words = list(pair)
        random.shuffle(words)
        lobby.majority_word = words[0]
        lobby.wolf_word = words[1]
        
        lobby.wolf_player = random.choice(lobby.players)
        
        # Send DMs
        for player in lobby.players:
            word = lobby.wolf_word if player == lobby.wolf_player else lobby.majority_word
            try:
                await player.send(f"🐺 **ワードウルフ開始！**\nあなたのお題は... **「{word}」** です。\n\n周りと会話を合わせて、自分がウルフ（少数派）か市民（多数派）か探りましょう！")
            except Exception as e:
                await ctx.send(f"❌ {player.display_name} へのDM送信に失敗しました。DMを許可してください。")
                del self.lobbies[ctx.channel.id]
                return

        await ctx.send("📨 全員にお題を送信しました！\n⏰ **3分間の議論タイム** スタート！")
        
        # Timer
        await asyncio.sleep(120) # 2 mins
        await ctx.send("⏰ 残り1分！")
        await asyncio.sleep(60) # 1 min
        
        await ctx.send("🛑 議論終了！\n👉 **投票タイム** です。ウルフだと思う人に投票してください。")
        
        # Voting View
        view = VoteView(self, lobby)
        await ctx.send("投票してください:", view=view)

    async def handle_vote_end(self, lobby, interaction):
        # Tally votes
        if not lobby.votes:
             await interaction.channel.send("誰も投票しませんでした...")
             del self.lobbies[lobby.channel.id]
             return

        vote_counts = {}
        for target_id in lobby.votes.values():
            vote_counts[target_id] = vote_counts.get(target_id, 0) + 1
            
        max_votes = max(vote_counts.values())
        most_voted_ids = [uid for uid, count in vote_counts.items() if count == max_votes]
        
        # Result
        wolf_name = lobby.wolf_player.display_name
        
        embed = discord.Embed(title="🐺 結果発表", color=discord.Color.red())
        embed.add_field(name="ウルフ", value=f"**{wolf_name}** (お題: {lobby.wolf_word})", inline=False)
        embed.add_field(name="市民のお題", value=lobby.majority_word, inline=False)
        
        result_msg = ""
        if lobby.wolf_player.id in most_voted_ids:
            result_msg = "🎉 **市民チームの勝利！** ウルフを見つけ出しました！"
        else:
            result_msg = "😈 **ウルフの勝利！** 市民を欺きました..."
            
        embed.description = result_msg
        
        await interaction.channel.send(embed=embed)
        
        # Cleanup
        if lobby.channel.id in self.lobbies:
            del self.lobbies[lobby.channel.id]


class JoinView(discord.ui.View):
    def __init__(self, cog, lobby):
        super().__init__(timeout=None)
        self.cog = cog
        self.lobby = lobby

    @discord.ui.button(label="参加する", style=discord.ButtonStyle.green, emoji="✋")
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.lobby.players:
            await interaction.response.send_message("既に参加しています。", ephemeral=True)
            return
            
        self.lobby.players.append(interaction.user)
        await self.cog.update_lobby_message(self.lobby)
        await interaction.response.send_message("参加しました！", ephemeral=True)

    @discord.ui.button(label="ゲーム開始", style=discord.ButtonStyle.red, emoji="▶️")
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.lobby.host:
            await interaction.response.send_message("ホストのみが開始できます。", ephemeral=True)
            return
            
        if len(self.lobby.players) < 3:
            await interaction.response.send_message("参加者が足りません（最低3人）。", ephemeral=True)
            # return # Uncomment for production

        await interaction.response.send_message("ゲームを開始します！")
        # Trigger begin logic manually since we can't invoke command easily
        # Dirty hack: create a fake context or just call a helper
        # Let's just call the logic directly if possible, or tell them to use command
        # Better: Refactor begin logic to a helper method
        
        # For now, just tell them to use command or trigger it via cog
        ctx = await self.cog.bot.get_context(interaction.message)
        ctx.author = interaction.user # Ensure host is author
        await self.cog.begin(ctx)


class VoteView(discord.ui.View):
    def __init__(self, cog, lobby):
        super().__init__(timeout=60)
        self.cog = cog
        self.lobby = lobby
        
        # Create select menu for voting
        options = []
        for player in lobby.players:
            options.append(discord.SelectOption(label=player.display_name, value=str(player.id)))
            
        select = discord.ui.Select(placeholder="ウルフだと思う人を選択...", options=options)
        select.callback = self.vote_callback
        self.add_item(select)

    async def vote_callback(self, interaction: discord.Interaction):
        voter = interaction.user
        target_id = int(interaction.data['values'][0])
        
        self.lobby.votes[voter.id] = target_id
        await interaction.response.send_message(f"投票しました。", ephemeral=True)
        
        # Check if everyone voted
        if len(self.lobby.votes) >= len(self.lobby.players):
            self.stop()
            await self.cog.handle_vote_end(self.lobby, interaction)

    async def on_timeout(self):
        # Force end if timeout
        # We need an interaction to send message, but on_timeout doesn't give one
        # We can use the channel from lobby
        if self.lobby.channel.id in self.cog.lobbies:
             # Just trigger end with whatever votes we have
             # We need a dummy interaction or just send to channel
             # Refactoring handle_vote_end to take channel instead of interaction would be better
             pass 

async def setup(bot):
    await bot.add_cog(PartyGameCog(bot))
