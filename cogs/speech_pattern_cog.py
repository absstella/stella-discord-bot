"""
Speech Pattern Commands Cog
Commands for managing individual speech patterns
"""
import discord
from discord.ext import commands
from discord import app_commands
import logging
from utils.speech_pattern_manager import speech_pattern_manager

logger = logging.getLogger(__name__)

class SpeechPatternCog(commands.Cog):
    """個人別話し方パターンの管理コマンド"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("Speech Pattern Cog initialized")
    
    @commands.hybrid_command(name="speech_pattern", aliases=["pattern", "話し方"])
    async def show_speech_pattern(self, ctx, user: discord.Member = None):
        """自分または指定したユーザーの話し方パターンを表示 (!speech_pattern [@ユーザー])"""
        try:
            target_user = user if user else ctx.author
            pattern = speech_pattern_manager.get_or_create_pattern(target_user.id, ctx.guild.id)
            
            # Create detailed pattern display
            embed = discord.Embed(
                title=f"🗣️ {target_user.display_name}の話し方パターン",
                color=discord.Color.blue()
            )
            
            # Basic speaking style
            embed.add_field(
                name="基本スタイル",
                value=f"丁寧度: {pattern.formality_level}\n"
                      f"エネルギー: {pattern.energy_level}\n"
                      f"礼儀正しさ: {pattern.politeness}",
                inline=True
            )
            
            # Expression styles
            embed.add_field(
                name="表現スタイル",
                value=f"絵文字: {pattern.emoji_style}\n"
                      f"顔文字: {pattern.kaomoji_style}\n"
                      f"ユーモア: {pattern.humor_style}",
                inline=True
            )
            
            # Learning statistics
            confidence_percent = int(pattern.confidence_score * 100)
            confidence_bar = "█" * (confidence_percent // 10) + "░" * (10 - confidence_percent // 10)
            
            embed.add_field(
                name="学習状況",
                value=f"分析済みメッセージ: {pattern.analyzed_messages}\n"
                      f"学習度: {confidence_percent}% {confidence_bar}\n"
                      f"最終更新: {pattern.last_updated[:10] if pattern.last_updated else '未更新'}",
                inline=False
            )
            
            # Characteristic expressions
            if pattern.sentence_endings:
                endings_display = "、".join(pattern.sentence_endings[:5])
                if len(pattern.sentence_endings) > 5:
                    endings_display += f" (+{len(pattern.sentence_endings) - 5}個)"
                embed.add_field(
                    name="よく使う語尾",
                    value=endings_display,
                    inline=True
                )
            
            if pattern.frequent_expressions:
                expressions_display = "、".join(pattern.frequent_expressions[:3])
                if len(pattern.frequent_expressions) > 3:
                    expressions_display += f" (+{len(pattern.frequent_expressions) - 3}個)"
                embed.add_field(
                    name="よく使う表現",
                    value=expressions_display,
                    inline=True
                )
            
            # AI adaptation note
            if pattern.confidence_score > 0.2:
                embed.add_field(
                    name="AI適応状況",
                    value="✅ STELLAはあなたの話し方に合わせて応答を調整しています",
                    inline=False
                )
            else:
                embed.add_field(
                    name="AI適応状況",
                    value="📊 もう少し会話を重ねると、より個人的な話し方に適応します",
                    inline=False
                )
            
            embed.set_footer(text="話し方パターンは会話を通じて自動的に学習されます")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error showing speech pattern: {e}")
            await ctx.send(f"❌ エラーが発生しました: {str(e)}")
    
    @commands.hybrid_command(name="reset_pattern", aliases=["reset_speech"])
    @commands.has_permissions(manage_messages=True)
    async def reset_speech_pattern(self, ctx, user: discord.Member = None):
        """話し方パターンをリセット (!reset_pattern [@ユーザー])"""
        try:
            target_user = user if user else ctx.author
            
            # Confirmation for resetting another user's pattern
            if user and user != ctx.author:
                confirm_embed = discord.Embed(
                    title="⚠️ 確認",
                    description=f"{user.display_name}の話し方パターンをリセットしますか？\n"
                               f"学習済みデータ（{speech_pattern_manager.get_or_create_pattern(user.id, ctx.guild.id).analyzed_messages}メッセージ）が失われます。",
                    color=discord.Color.orange()
                )
                
                confirm_msg = await ctx.send(embed=confirm_embed)
                await confirm_msg.add_reaction("✅")
                await confirm_msg.add_reaction("❌")
                
                def check(reaction, user_react):
                    return user_react == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message == confirm_msg
                
                try:
                    reaction, _ = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
                    if str(reaction.emoji) == "❌":
                        await ctx.send("キャンセルしました。")
                        return
                except:
                    await ctx.send("タイムアウトしました。")
                    return
            
            # Reset pattern
            if target_user.id in speech_pattern_manager.patterns:
                del speech_pattern_manager.patterns[target_user.id]
                speech_pattern_manager.save_patterns()
            
            embed = discord.Embed(
                title="✅ 話し方パターンをリセットしました",
                description=f"{target_user.display_name}の話し方パターンが初期化されました。\n"
                           f"今後の会話から新しくパターンを学習していきます。",
                color=discord.Color.green()
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error resetting speech pattern: {e}")
            await ctx.send(f"❌ エラーが発生しました: {str(e)}")
    
    @commands.hybrid_command(name="speech_stats", aliases=["pattern_stats"])
    async def speech_pattern_stats(self, ctx):
        """サーバー全体の話し方パターン統計を表示 (!speech_stats)"""
        try:
            guild_patterns = []
            for user_id, pattern in speech_pattern_manager.patterns.items():
                if pattern.guild_id == ctx.guild.id:
                    guild_patterns.append(pattern)
            
            if not guild_patterns:
                await ctx.send("📊 このサーバーではまだ話し方パターンが学習されていません。")
                return
            
            # Calculate statistics
            total_messages = sum(p.analyzed_messages for p in guild_patterns)
            avg_confidence = sum(p.confidence_score for p in guild_patterns) / len(guild_patterns)
            
            # Style distribution
            formality_counts = {}
            energy_counts = {}
            emoji_counts = {}
            
            for pattern in guild_patterns:
                formality_counts[pattern.formality_level] = formality_counts.get(pattern.formality_level, 0) + 1
                energy_counts[pattern.energy_level] = energy_counts.get(pattern.energy_level, 0) + 1
                emoji_counts[pattern.emoji_style] = emoji_counts.get(pattern.emoji_style, 0) + 1
            
            embed = discord.Embed(
                title="📊 サーバー話し方パターン統計",
                color=discord.Color.purple()
            )
            
            embed.add_field(
                name="学習概要",
                value=f"学習済みユーザー: {len(guild_patterns)}人\n"
                      f"総分析メッセージ: {total_messages:,}件\n"
                      f"平均学習度: {avg_confidence:.1%}",
                inline=False
            )
            
            # Top formality style
            top_formality = max(formality_counts, key=formality_counts.get)
            formality_display = ", ".join([f"{k}: {v}人" for k, v in sorted(formality_counts.items(), key=lambda x: x[1], reverse=True)])
            
            embed.add_field(
                name="丁寧度分布",
                value=formality_display,
                inline=True
            )
            
            # Top energy style
            energy_display = ", ".join([f"{k}: {v}人" for k, v in sorted(energy_counts.items(), key=lambda x: x[1], reverse=True)])
            
            embed.add_field(
                name="エネルギー分布",
                value=energy_display,
                inline=True
            )
            
            # Emoji usage
            emoji_display = ", ".join([f"{k}: {v}人" for k, v in sorted(emoji_counts.items(), key=lambda x: x[1], reverse=True)])
            
            embed.add_field(
                name="絵文字使用分布",
                value=emoji_display,
                inline=True
            )
            
            # Most active learners
            top_learners = sorted(guild_patterns, key=lambda p: p.analyzed_messages, reverse=True)[:3]
            learner_display = []
            
            for i, pattern in enumerate(top_learners):
                try:
                    user = self.bot.get_user(pattern.user_id)
                    user_name = user.display_name if user else f"ユーザー#{pattern.user_id}"
                    learner_display.append(f"{i+1}. {user_name}: {pattern.analyzed_messages}件")
                except:
                    learner_display.append(f"{i+1}. ユーザー#{pattern.user_id}: {pattern.analyzed_messages}件")
            
            if learner_display:
                embed.add_field(
                    name="学習データ上位",
                    value="\n".join(learner_display),
                    inline=False
                )
            
            embed.set_footer(text="話し方パターンは個人のプライバシーを尊重し、安全に管理されています")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error showing speech pattern stats: {e}")
            await ctx.send(f"❌ エラーが発生しました: {str(e)}")

async def setup(bot):
    await bot.add_cog(SpeechPatternCog(bot))
    logger.info("Speech Pattern Cog loaded")