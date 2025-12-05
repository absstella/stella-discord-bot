import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
from datetime import datetime, timedelta

class GameUtilityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.recruitments = {} # message_id: {data}

    # --- 1. Team Divider ---
    @commands.hybrid_command(name="simple_teams", description="[ゲーム] VCメンバーをチーム分けします")
    @app_commands.describe(count="チーム数", mode="分け方 (random/balanced)")
    async def make_teams(self, ctx: commands.Context, count: int = 2, mode: str = "random"):
        """Divide VC members into teams"""
        if not ctx.author.voice:
            await ctx.send("❌ 先にボイスチャンネルに参加してください。", ephemeral=True)
            return

        members = ctx.author.voice.channel.members
        if len(members) < count:
            await ctx.send(f"❌ メンバー数がチーム数より少ないです（メンバー: {len(members)}人, チーム: {count}）", ephemeral=True)
            return

        # Shuffle
        random.shuffle(members)
        
        # Split
        teams = [[] for _ in range(count)]
        for i, member in enumerate(members):
            teams[i % count].append(member)

        # Display
        embed = discord.Embed(title="🎮 チーム分け結果", color=0x0099FF)
        for i, team in enumerate(teams):
            team_names = "\n".join([f"👤 {m.display_name}" for m in team])
            embed.add_field(name=f"Team {i+1}", value=team_names or "なし", inline=True)

        await ctx.send(embed=embed)

    # --- 2. Map/Agent Roulette ---
    @commands.hybrid_command(name="pick_map", description="[ゲーム] マップをランダムに選びます")
    @app_commands.choices(game=[
        app_commands.Choice(name="Valorant", value="valorant"),
        app_commands.Choice(name="Apex Legends", value="apex"),
        app_commands.Choice(name="Overwatch 2", value="ow2")
    ])
    async def pick_map(self, ctx: commands.Context, game: str):
        """Pick a random map"""
        maps = {
            "valorant": ["Ascent", "Bind", "Haven", "Split", "Icebox", "Breeze", "Fracture", "Pearl", "Lotus", "Sunset", "Abyss"],
            "apex": ["Kings Canyon", "World's Edge", "Olympus", "Storm Point", "Broken Moon"],
            "ow2": ["King's Row", "Watchpoint: Gibraltar", "Dorado", "Route 66", "Lijiang Tower", "Ilios", "Nepal", "Oasis"]
        }
        
        selected = random.choice(maps.get(game, ["Unknown Game"]))
        await ctx.send(f"🗺️ **{game.upper()}** のマップは... \n# 🎲 {selected} 🎲\nに決定！")

    @commands.hybrid_command(name="pick_agent", description="[ゲーム] キャラクターをランダムに選びます")
    @app_commands.choices(game=[
        app_commands.Choice(name="Valorant", value="valorant"),
        app_commands.Choice(name="Apex Legends", value="apex"),
        app_commands.Choice(name="Overwatch 2 (Tank)", value="ow2_tank"),
        app_commands.Choice(name="Overwatch 2 (DPS)", value="ow2_dps"),
        app_commands.Choice(name="Overwatch 2 (Support)", value="ow2_sup")
    ])
    async def pick_agent(self, ctx: commands.Context, game: str):
        """Pick a random agent"""
        agents = {
            "valorant": ["Jett", "Raze", "Reyna", "Yoru", "Phoenix", "Neon", "Iso", "Sova", "Fade", "Skye", "Breach", "Gekko", "KAY/O", "Omen", "Brimstone", "Viper", "Astra", "Harbor", "Clove", "Cypher", "Killjoy", "Sage", "Chamber", "Deadlock", "Vyse"],
            "apex": ["Wraith", "Octane", "Pathfinder", "Horizon", "Bangalore", "Bloodhound", "Lifeline", "Gibraltar", "Caustic", "Mirage", "Wattson", "Crypto", "Revenant", "Loba", "Rampart", "Fuse", "Valkyrie", "Seer", "Ash", "Mad Maggie", "Newcastle", "Vantage", "Catalyst", "Ballistic", "Conduit", "Alter"],
            "ow2_tank": ["D.Va", "Doomfist", "Junker Queen", "Orisa", "Ramattra", "Reinhardt", "Roadhog", "Sigma", "Winston", "Wrecking Ball", "Zarya", "Mauga"],
            "ow2_dps": ["Ashe", "Bastion", "Cassidy", "Echo", "Genji", "Hanzo", "Junkrat", "Mei", "Pharah", "Reaper", "Sojourn", "Soldier: 76", "Sombra", "Symmetra", "Torbjörn", "Tracer", "Widowmaker", "Venture"],
            "ow2_sup": ["Ana", "Baptiste", "Brigitte", "Illari", "Kiriko", "Lifeweaver", "Lucio", "Mercy", "Moira", "Zenyatta", "Juno"]
        }
        
        selected = random.choice(agents.get(game, ["Unknown"]))
        await ctx.send(f"👤 **{game.replace('_', ' ').upper()}** のキャラは... \n# 🎲 {selected} 🎲\nを使ってください！")

    # --- 3. Strat Roulette ---
    @commands.hybrid_command(name="strat", description="[ゲーム] 縛りプレイや戦術を指示します")
    @app_commands.choices(game=[
        app_commands.Choice(name="Valorant", value="valorant"),
        app_commands.Choice(name="Apex Legends", value="apex")
    ])
    async def strat_roulette(self, ctx: commands.Context, game: str):
        """Generate a random strategy"""
        strats = {
            "valorant": [
                "**ショットガン限定**: 全員ジャッジかバッキーのみ購入。",
                "**忍者**: 足音を立ててはいけない（常に歩き）。",
                "**英語禁止**: VCで英語（敵の名前、場所など）を使ったら自害。",
                "**VIP警護**: 一人を「大統領」に指名し、他の全員で肉壁になって守る。",
                "**ラッシュB**: 何があってもBサイトに全員で突撃。止まるな。",
                "**ピストル縛り**: シェリフかゴーストのみ。",
                "**アビリティ禁止**: 撃ち合いだけで勝て。"
            ],
            "apex": [
                "**モザンビーク縛り**: モザンビークを見つけるまで撃ってはいけない。",
                "**グレネード祭り**: バックパックの半分をグレネードにする。",
                "**スナイパー部隊**: 全員スナイパーライフルを持つ。",
                "**激戦区降り**: マップで一番最初に降りられる場所に即降り。",
                "**コミュ障**: ピン指し禁止。VC禁止。",
                "**ストーカー**: 敵を見つけても撃たずに、バレないようにずっとついていく。"
            ]
        }
        
        selected = random.choice(strats.get(game, ["普通にプレイしましょう"]))
        await ctx.send(f"📋 **今回の作戦 ({game.upper()})**\n\n# {selected}")

    # --- 4. Recruitment Board ---
    @commands.hybrid_command(name="boshu", description="[ゲーム] メンバー募集を行います")
    @app_commands.describe(game="ゲーム名", count="募集人数", time="開始時間/備考")
    async def recruit(self, ctx: commands.Context, game: str, count: int, time: str = "集まり次第"):
        """Create a recruitment board"""
        embed = discord.Embed(
            title=f"🎮 メンバー募集: {game}",
            description=f"**募集人数**: 残り {count}人\n**時間**: {time}\n**ホスト**: {ctx.author.mention}",
            color=0x00FF00,
            timestamp=datetime.now()
        )
        embed.add_field(name="参加者", value=ctx.author.display_name, inline=False)
        
        view = RecruitmentView(count, ctx.author)
        message = await ctx.send(embed=embed, view=view)
        view.message = message

class RecruitmentView(discord.ui.View):
    def __init__(self, max_count, host):
        super().__init__(timeout=None)
        self.max_count = max_count
        self.host = host
        self.participants = [host]
        self.remaining = max_count

    @discord.ui.button(label="参加する", style=discord.ButtonStyle.primary, emoji="✋")
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.participants:
            await interaction.response.send_message("既に参加しています。", ephemeral=True)
            return
        
        if self.remaining <= 0:
            await interaction.response.send_message("満員です！", ephemeral=True)
            return

        self.participants.append(interaction.user)
        self.remaining -= 1
        
        await self.update_message(interaction)
        
        if self.remaining == 0:
            await interaction.channel.send(f"🎉 **{self.host.mention} 募集が埋まりました！**\nメンバー: {' '.join([p.mention for p in self.participants])}")
            # Disable button
            button.disabled = True
            button.label = "満員御礼"
            button.style = discord.ButtonStyle.secondary
            await interaction.message.edit(view=self)

    @discord.ui.button(label="キャンセル", style=discord.ButtonStyle.danger, emoji="✖️")
    async def leave_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.participants:
            await interaction.response.send_message("参加していません。", ephemeral=True)
            return
        
        if interaction.user == self.host:
            await interaction.response.send_message("ホストは抜けられません。募集を取り消す場合はメッセージを削除してください。", ephemeral=True)
            return

        self.participants.remove(interaction.user)
        self.remaining += 1
        await self.update_message(interaction)

    async def update_message(self, interaction):
        embed = interaction.message.embeds[0]
        embed.description = f"**募集人数**: 残り {self.remaining}人\n**時間**: {embed.fields[0].value if len(embed.fields) > 0 else '不明'}\n**ホスト**: {self.host.mention}"
        
        # Rebuild participant list
        participant_names = "\n".join([f"👤 {p.display_name}" for p in self.participants])
        embed.set_field_at(0, name="参加者", value=participant_names, inline=False)
        
        await interaction.response.edit_message(embed=embed, view=self)

async def setup(bot):
    await bot.add_cog(GameUtilityCog(bot))
