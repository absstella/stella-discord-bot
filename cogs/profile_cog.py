import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class ProfileCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ai_cog = None

    @commands.Cog.listener()
    async def on_ready(self):
        self.ai_cog = self.bot.get_cog('AICog')

    @commands.hybrid_group(name="profile", description="ユーザープロファイル管理")
    async def profile_group(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("サブコマンドを指定してください: show, update, import_absdata")

    @profile_group.command(name="show", description="ユーザーのプロファイルを表示します")
    @app_commands.describe(user="表示するユーザー")
    async def show_profile(self, ctx, user: Optional[discord.Member] = None):
        """Show user profile"""
        target_user = user or ctx.author
        
        if not self.ai_cog:
            self.ai_cog = self.bot.get_cog('AICog')
            
        if not self.ai_cog:
            await ctx.send("❌ AI機能がロードされていません。")
            return

        try:
            profile = await self.ai_cog.get_user_profile(target_user.id, ctx.guild.id)
            
            embed = discord.Embed(title=f"👤 {target_user.display_name} のプロファイル", color=discord.Color.blue())
            
            if profile.nickname:
                embed.add_field(name="ニックネーム", value=profile.nickname, inline=True)
                
            if profile.personality_traits:
                embed.add_field(name="性格", value=", ".join(profile.personality_traits), inline=False)
                
            if profile.interests:
                embed.add_field(name="興味・関心", value=", ".join(profile.interests), inline=False)
                
            if profile.favorite_games:
                embed.add_field(name="好きなゲーム", value=", ".join(profile.favorite_games), inline=False)
                
            # Custom attributes (often where imported data goes)
            if profile.custom_attributes:
                custom_str = ""
                for k, v in profile.custom_attributes.items():
                    custom_str += f"**{k}**: {v}\n"
                if custom_str:
                    embed.add_field(name="その他の情報", value=custom_str, inline=False)

            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error showing profile: {e}")
            await ctx.send(f"❌ プロファイルの表示中にエラーが発生しました: {e}")

    @profile_group.command(name="update", description="プロファイルを手動で更新します")
    @app_commands.describe(user="更新するユーザー", key="項目名（例: 好きなゲーム）", value="設定する値")
    async def update_profile(self, ctx, user: discord.Member, key: str, value: str):
        """Manually update a profile field"""
        if not self.ai_cog:
            self.ai_cog = self.bot.get_cog('AICog')
            
        try:
            profile = await self.ai_cog.get_user_profile(user.id, ctx.guild.id)
            
            # Simple mapping for common fields
            if key in ["好きなゲーム", "games", "game"]:
                profile.add_game(value)
                msg = f"🎮 {user.display_name}の好きなゲームに「{value}」を追加しました。"
            elif key in ["興味", "interest", "interests"]:
                profile.add_interest(value)
                msg = f"✨ {user.display_name}の興味に「{value}」を追加しました。"
            elif key in ["性格", "personality"]:
                profile.add_trait(value)
                msg = f"🧠 {user.display_name}の性格に「{value}」を追加しました。"
            elif key in ["ニックネーム", "nickname"]:
                profile.nickname = value
                msg = f"🏷️ {user.display_name}のニックネームを「{value}」に設定しました。"
            else:
                # Default to custom attributes
                if not profile.custom_attributes:
                    profile.custom_attributes = {}
                profile.custom_attributes[key] = value
                msg = f"📝 {user.display_name}の{key}を「{value}」に設定しました。"
            
            await self.ai_cog.save_user_profile(profile)
            await ctx.send(f"✅ {msg}")
            
        except Exception as e:
            logger.error(f"Error updating profile: {e}")
            await ctx.send(f"❌ 更新中にエラーが発生しました: {e}")

    @profile_group.command(name="import_absdata", description="[管理者] absdata.jsonからメンバー情報をインポートします")
    @commands.has_permissions(administrator=True)
    async def import_absdata(self, ctx):
        """Import data from absdata.json"""
        if not self.ai_cog:
            self.ai_cog = self.bot.get_cog('AICog')
            
        await ctx.defer()
        
        absdata_path = os.path.join("data", "absdata.json")
        if not os.path.exists(absdata_path):
            await ctx.send("❌ data/absdata.json が見つかりません。")
            return
            
        try:
            with open(absdata_path, 'r', encoding='utf-8') as f:
                absdata = json.load(f)
                
            count = 0
            
            # Pre-fetch all members to match names
            members = ctx.guild.members
            
            for entry in absdata:
                player_name = entry.get("プレイヤー名")
                if not player_name:
                    continue
                    
                # Find matching member
                target_member = None
                for m in members:
                    if (player_name.lower() in m.name.lower() or 
                        player_name.lower() in m.display_name.lower()):
                        target_member = m
                        break
                
                if target_member:
                    profile = await self.ai_cog.get_user_profile(target_member.id, ctx.guild.id)
                    
                    # Import fields
                    if entry.get("役職"):
                        if not profile.custom_attributes: profile.custom_attributes = {}
                        profile.custom_attributes["役職"] = entry["役職"]
                        
                    if entry.get("主なジャンル"):
                        profile.add_interest(entry["主なジャンル"])
                        
                    for i in range(1, 4):
                        game = entry.get(f"好きなゲーム{i}")
                        if game and game != "null":
                            profile.add_game(game)
                            
                    if entry.get("好きなもの"):
                        profile.add_interest(entry["好きなもの"])
                        
                    if entry.get("追記1"):
                        profile.add_behavioral_trait(entry["追記1"])
                        
                    if entry.get("追記2"):
                        profile.add_behavioral_trait(entry["追記2"])
                        
                    await self.ai_cog.save_user_profile(profile)
                    count += 1
                    logger.info(f"Imported data for {player_name} -> {target_member.display_name}")
            
            await ctx.send(f"✅ {count}件のメンバー情報をインポートしました！")
            
        except Exception as e:
            logger.error(f"Import failed: {e}")
            await ctx.send(f"❌ インポート中にエラーが発生しました: {e}")
    @profile_group.command(name="link_absdata", description="[管理者] Discordユーザーとabsdataの情報を手動で紐付けます")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(user="紐付けるユーザー", absdata_name="absdata.json内のプレイヤー名")
    async def link_absdata(self, ctx, user: discord.Member, absdata_name: str):
        """Manually link a user to an absdata entry"""
        if not self.ai_cog:
            self.ai_cog = self.bot.get_cog('AICog')
            
        await ctx.defer()
        
        absdata_path = os.path.join("data", "absdata.json")
        if not os.path.exists(absdata_path):
            await ctx.send("❌ data/absdata.json が見つかりません。")
            return
            
        try:
            with open(absdata_path, 'r', encoding='utf-8') as f:
                absdata = json.load(f)
                
            # Find matching entry
            target_entry = None
            for entry in absdata:
                if entry.get("プレイヤー名") == absdata_name:
                    target_entry = entry
                    break
            
            if not target_entry:
                await ctx.send(f"❌ absdata.json 内に「{absdata_name}」というプレイヤー名が見つかりませんでした。")
                return
                
            # Import data
            profile = await self.ai_cog.get_user_profile(user.id, ctx.guild.id)
            
            # Import fields
            if target_entry.get("役職"):
                if not profile.custom_attributes: profile.custom_attributes = {}
                profile.custom_attributes["役職"] = target_entry["役職"]
                
            if target_entry.get("主なジャンル"):
                profile.add_interest(target_entry["主なジャンル"])
                
            for i in range(1, 4):
                game = target_entry.get(f"好きなゲーム{i}")
                if game and game != "null":
                    profile.add_game(game)
                    
            if target_entry.get("好きなもの"):
                profile.add_interest(target_entry["好きなもの"])
                
            if target_entry.get("追記1"):
                profile.add_behavioral_trait(target_entry["追記1"])
                
            if target_entry.get("追記2"):
                profile.add_behavioral_trait(target_entry["追記2"])
                
            # Save mapping alias for future reference (optional but good idea)
            if not profile.custom_attributes: profile.custom_attributes = {}
            profile.custom_attributes["absdata_name"] = absdata_name
                
            await self.ai_cog.save_user_profile(profile)
            
            await ctx.send(f"✅ **{user.display_name}** と **{absdata_name}** の情報を紐付けました！")
            
        except Exception as e:
            logger.error(f"Link failed: {e}")
            await ctx.send(f"❌ 紐付け中にエラーが発生しました: {e}")

async def setup(bot):
    await bot.add_cog(ProfileCog(bot))