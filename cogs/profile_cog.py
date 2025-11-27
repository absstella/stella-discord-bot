"""
Enhanced Profile Display Cog for S.T.E.L.L.A.
Provides comprehensive user profile viewing and management
"""
import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Optional
from datetime import datetime
from utils.profile_storage import profile_storage

logger = logging.getLogger(__name__)

class ProfileCog(commands.Cog):
    """Profile management and display commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(name="myprofile", description="プロフィールを表示します")
    async def myprofile(self, ctx, user: Optional[discord.Member] = None):
        """プロフィールを表示します (!myprofile [@ユーザー])"""
        target_user = user or ctx.author
        
        try:
            # Load profile from storage
            profile = profile_storage.load_profile(target_user.id, ctx.guild.id)
            
            if not profile:
                embed = discord.Embed(
                    title=f"📊 {target_user.display_name}のプロフィール",
                    description="プロフィールが見つかりません。会話をするとプロフィールが自動的に作成されます。",
                    color=0x3498db
                )
                await ctx.send(embed=embed)
                return
            
            # Create detailed profile embed
            embed = discord.Embed(
                title=f"📊 {target_user.display_name}のプロフィール",
                color=0x00ff00
            )
            
            # Basic info
            if profile.nickname:
                embed.add_field(name="ニックネーム", value=profile.nickname, inline=True)
            
            if profile.description:
                embed.add_field(name="説明", value=profile.description[:100] + "...", inline=False)
            
            # Personality traits
            if profile.personality_traits:
                traits_text = ", ".join(profile.personality_traits[:5])
                if len(profile.personality_traits) > 5:
                    traits_text += f" など {len(profile.personality_traits)}個"
                embed.add_field(name="🧠 性格特性", value=traits_text, inline=False)
            
            # Interests
            if profile.interests:
                interests_text = ", ".join(profile.interests[:5])
                if len(profile.interests) > 5:
                    interests_text += f" など {len(profile.interests)}個"
                embed.add_field(name="❤️ 興味・関心", value=interests_text, inline=False)
            
            # Favorite games
            if profile.favorite_games:
                games_text = ", ".join(profile.favorite_games[:3])
                if len(profile.favorite_games) > 3:
                    games_text += f" など {len(profile.favorite_games)}個"
                embed.add_field(name="🎮 お気に入りゲーム", value=games_text, inline=False)
            
            # Communication style
            if profile.communication_style:
                style_items = []
                for key, value in list(profile.communication_style.items())[:3]:
                    style_items.append(f"{key}: {value}")
                if style_items:
                    embed.add_field(name="💬 コミュニケーションスタイル", 
                                  value="\n".join(style_items), inline=False)
            
            # Statistics
            stats_text = []
            if profile.conversation_patterns:
                stats_text.append(f"会話パターン: {len(profile.conversation_patterns)}個")
            if profile.interaction_history:
                stats_text.append(f"インタラクション履歴: {len(profile.interaction_history)}回")
            if profile.memorable_moments:
                stats_text.append(f"記憶された瞬間: {len(profile.memorable_moments)}個")
            
            if stats_text:
                embed.add_field(name="📈 統計", value="\n".join(stats_text), inline=True)
            
            # Timestamps
            if profile.created_at:
                embed.add_field(name="作成日", 
                              value=profile.created_at.strftime("%Y年%m月%d日"), inline=True)
            if profile.updated_at:
                embed.add_field(name="最終更新", 
                              value=profile.updated_at.strftime("%Y年%m月%d日 %H:%M"), inline=True)
            
            # Recent memorable moments
            if profile.memorable_moments:
                recent_moments = profile.memorable_moments[-3:]
                moments_text = "\n".join([f"• {moment.get('summary', str(moment))[:50]}..." 
                                        for moment in recent_moments if isinstance(moment, dict)])
                if moments_text:
                    embed.add_field(name="🌟 最近の記憶", value=moments_text, inline=False)
            
            embed.set_thumbnail(url=target_user.display_avatar.url)
            embed.set_footer(text="S.T.E.L.L.A. プロフィールシステム")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error displaying profile: {e}")
            embed = discord.Embed(
                title="エラー",
                description="プロフィールの表示中にエラーが発生しました。",
                color=0xff0000
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="profiles", description="サーバー内の全プロフィールを表示")
    async def profiles(self, ctx):
        """サーバー内の全プロフィールを表示します (!profiles)"""
        try:
            all_profiles = profile_storage.get_all_profiles(ctx.guild.id)
            
            if not all_profiles:
                embed = discord.Embed(
                    title="📊 サーバープロフィール",
                    description="まだプロフィールが作成されていません。",
                    color=0x3498db
                )
                await ctx.send(embed=embed)
                return
            
            embed = discord.Embed(
                title=f"📊 {ctx.guild.name} のプロフィール一覧",
                description=f"合計 {len(all_profiles)} 人のプロフィールが見つかりました",
                color=0x00ff00
            )
            
            for user_id, profile in list(all_profiles.items())[:10]:  # Show first 10
                try:
                    user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
                    if user:
                        profile_summary = []
                        if profile.personality_traits:
                            profile_summary.append(f"性格: {len(profile.personality_traits)}個")
                        if profile.interests:
                            profile_summary.append(f"興味: {len(profile.interests)}個")
                        if profile.conversation_patterns:
                            profile_summary.append(f"会話: {len(profile.conversation_patterns)}回")
                        
                        summary_text = " | ".join(profile_summary) if profile_summary else "基本情報のみ"
                        embed.add_field(
                            name=user.display_name,
                            value=summary_text,
                            inline=False
                        )
                except:
                    continue
            
            if len(all_profiles) > 10:
                embed.set_footer(text=f"他に {len(all_profiles) - 10} 人のプロフィールがあります")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error displaying all profiles: {e}")
            embed = discord.Embed(
                title="エラー",
                description="プロフィール一覧の表示中にエラーが発生しました。",
                color=0xff0000
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ProfileCog(bot))