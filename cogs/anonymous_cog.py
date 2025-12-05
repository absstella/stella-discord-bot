import discord
from discord.ext import commands
from discord import app_commands
import logging
import json
import os

logger = logging.getLogger(__name__)

DATA_FILE = "data/anonymous_settings.json"

class AnonymousCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings = {} # {guild_id: channel_id}
        self.load_settings()

    def load_settings(self):
        if not os.path.exists("data"):
            os.makedirs("data")
        
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.settings = {int(k): v for k, v in data.items()}
            except Exception as e:
                logger.error(f"Failed to load anonymous settings: {e}")
                self.settings = {}
        else:
            self.settings = {}

    def save_settings(self):
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save anonymous settings: {e}")

    @app_commands.command(name="set_confess_channel", description="[設定] 匿名メッセージ（目安箱）の送信先チャンネルを設定します")
    @app_commands.describe(channel="送信先チャンネル")
    @app_commands.default_permissions(administrator=True)
    async def set_confess_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Set the channel for anonymous messages"""
        self.settings[interaction.guild_id] = channel.id
        self.save_settings()
        await interaction.response.send_message(f"✅ 匿名目安箱の送信先を {channel.mention} に設定しました。", ephemeral=True)

    @app_commands.command(name="confess", description="[目安箱] 匿名でメッセージを送信します")
    @app_commands.describe(message="送信する内容")
    async def confess(self, interaction: discord.Interaction, message: str):
        """Send an anonymous message"""
        if interaction.guild_id not in self.settings:
            await interaction.response.send_message("❌ このサーバーでは匿名目安箱が設定されていません。管理者に連絡してください。", ephemeral=True)
            return

        channel_id = self.settings[interaction.guild_id]
        channel = self.bot.get_channel(channel_id)
        
        if not channel:
            await interaction.response.send_message("❌ 設定されたチャンネルが見つかりません。", ephemeral=True)
            return

        embed = discord.Embed(
            title="📮 匿名メッセージ",
            description=message,
            color=discord.Color.light_grey()
        )
        embed.set_footer(text="このメッセージは匿名で送信されました")
        
        try:
            await channel.send(embed=embed)
            await interaction.response.send_message("✅ メッセージを匿名で送信しました。", ephemeral=True)
            logger.info(f"Anonymous message sent in guild {interaction.guild_id}")
        except Exception as e:
            await interaction.response.send_message(f"❌ 送信に失敗しました: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AnonymousCog(bot))
