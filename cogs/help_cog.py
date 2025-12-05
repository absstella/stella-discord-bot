import discord
from discord import app_commands
from discord.ext import commands
import logging

logger = logging.getLogger(__name__)

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Botの機能一覧と使い方を表示します")
    async def help_command(self, interaction: discord.Interaction):
        """Show help menu"""
        view = HelpView()
        embed = discord.Embed(
            title="📘 STELLA Bot ヘルプ",
            description="下のメニューからカテゴリを選択してください。",
            color=0x0099FF
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        await interaction.response.send_message(embed=embed, view=view)

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)

    @discord.ui.select(
        placeholder="カテゴリを選択...",
        options=[
            discord.SelectOption(label="🎮 ゲーム便利機能", description="チーム分け、募集、ルーレットなど", emoji="🎮", value="game"),
            discord.SelectOption(label="🏆 ガチ勢向け", description="大会、スクリム、クリップ、コーチ", emoji="🏆", value="advanced"),
            discord.SelectOption(label="📻 コミュニティ", description="ラジオ、実績、通貨、結婚", emoji="📻", value="community"),
            discord.SelectOption(label="🤡 いたずら", description="ドッキリ、ジョーク機能", emoji="🤡", value="prank"),
            discord.SelectOption(label="🤖 基本機能/AI", description="会話、音楽、検索など", emoji="🤖", value="basic"),
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        category = select.values[0]
        embed = discord.Embed(color=0x0099FF)

        if category == "game":
            embed.title = "🎮 ゲーム便利機能"
            embed.description = """
            `/teams [人数]` - VCメンバーをチーム分け
            `/boshu [ゲーム] [人数]` - メンバー募集
            `/pick_map [ゲーム]` - マップをランダム選択
            `/pick_agent [ゲーム]` - キャラをランダム選択
            `/strat [ゲーム]` - 戦術ルーレット（縛りプレイ）
            """
        elif category == "advanced":
            embed.title = "🏆 ガチ勢向け機能"
            embed.description = """
            `/create_tournament [参加者]` - トーナメント表作成
            `/scrim_poll [日程]` - スクリム日程調整
            `/clip [URL] [タイトル]` - クリップ保存
            `/top_clips` - クリップランキング
            `/coach [質問]` - AIコーチに質問（Web検索）
            `/sens [from] [val] [to]` - 感度変換
            `/add_term` / `/whatis` - サーバー用語集
            """
        elif category == "community":
            embed.title = "📻 コミュニティ機能"
            embed.description = """
            `/start_radio` - STELLAラジオ局を開局
            `/achievements` - 実績確認
            `/start_bet [タイトル]` - 勝敗予想ベット
            （未実装: `/balance`, `/feed`, `/propose`）
            """
        elif category == "prank":
            embed.title = "🤡 いたずら機能"
            embed.description = """
            `/impersonate` - 誰かになりすまし
            `/ghost_whisper` - 幽霊のささやき
            `/fake_error` - 偽エラー
            ...その他多数（管理者限定）
            """
        elif category == "basic":
            embed.title = "🤖 基本機能 / AI"
            embed.description = """
            `/ask [質問]` - AIと会話
            `/play [曲名]` - 音楽再生
            `/search [KW]` - Web検索
            `/myprofile` - プロフィール確認
            """
        
        await interaction.response.edit_message(embed=embed, view=self)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
