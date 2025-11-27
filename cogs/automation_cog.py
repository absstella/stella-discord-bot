import os
import asyncio
import logging
from typing import Dict, List, Optional
import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import json
import re
import google.generativeai as genai
from database.models import UserProfile, DatabaseHelpers
from config import *

logger = logging.getLogger(__name__)

class AutomationCog(commands.Cog):
    """自動化・通知機能"""
    
    def __init__(self, bot):
        self.bot = bot
        self.auto_responses = {}  # guild_id -> auto_response_rules
        self.keyword_alerts = {}  # guild_id -> keyword_alert_rules
        self.scheduled_messages = {}  # guild_id -> scheduled_messages
        
        # Initialize Gemini for smart responses
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
            logger.warning("Gemini API key not found for automation")
        
        # Start automation tasks
        self.automation_check_task.start()
        
    def cog_unload(self):
        """Cog がアンロードされる時にタスクを停止"""
        if hasattr(self, 'automation_check_task'):
            self.automation_check_task.cancel()

    @commands.hybrid_command(name='auto_response')
    async def setup_auto_response(self, ctx, trigger: str, *, response: str):
        """自動返信設定 (/auto_response "おはよう" "おはようございます！今日も頑張りましょう！")"""
        try:
            guild_id = ctx.guild.id
            
            if guild_id not in self.auto_responses:
                self.auto_responses[guild_id] = []
            
            # トリガーの重複チェック
            for rule in self.auto_responses[guild_id]:
                if rule['trigger'].lower() == trigger.lower():
                    await ctx.send(f"❌ トリガー `{trigger}` は既に設定されています。")
                    return
            
            auto_rule = {
                'id': len(self.auto_responses[guild_id]) + 1,
                'trigger': trigger,
                'response': response,
                'creator_id': ctx.author.id,
                'creator_name': ctx.author.display_name,
                'channel_id': ctx.channel.id,
                'created_at': datetime.now().isoformat(),
                'enabled': True,
                'usage_count': 0
            }
            
            self.auto_responses[guild_id].append(auto_rule)
            
            # データベースに保存
            await self.save_auto_response_to_database(guild_id, auto_rule)
            
            embed = discord.Embed(
                title="🤖 自動返信を設定しました",
                color=0x00ff9f,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="🎯 トリガー",
                value=f"`{trigger}`",
                inline=True
            )
            
            embed.add_field(
                name="💬 返信内容",
                value=f"`{response}`",
                inline=True
            )
            
            embed.add_field(
                name="🆔 ルールID",
                value=f"`{auto_rule['id']}`",
                inline=True
            )
            
            embed.set_footer(text="メッセージにトリガーが含まれると自動返信します")
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Auto response setup error: {e}")
            await ctx.send(f"❌ 自動返信設定エラー: {str(e)}")

    @commands.hybrid_command(name='keyword_alert')
    async def setup_keyword_alert(self, ctx, keyword: str, *, mention_role: discord.Role = None):
        """キーワード通知設定 (/keyword_alert "緊急" @管理者)"""
        try:
            guild_id = ctx.guild.id
            
            if guild_id not in self.keyword_alerts:
                self.keyword_alerts[guild_id] = []
            
            # キーワードの重複チェック
            for rule in self.keyword_alerts[guild_id]:
                if rule['keyword'].lower() == keyword.lower():
                    await ctx.send(f"❌ キーワード `{keyword}` は既に設定されています。")
                    return
            
            alert_rule = {
                'id': len(self.keyword_alerts[guild_id]) + 1,
                'keyword': keyword,
                'mention_role_id': mention_role.id if mention_role else None,
                'mention_role_name': mention_role.name if mention_role else None,
                'creator_id': ctx.author.id,
                'creator_name': ctx.author.display_name,
                'channel_id': ctx.channel.id,
                'created_at': datetime.now().isoformat(),
                'enabled': True,
                'alert_count': 0
            }
            
            self.keyword_alerts[guild_id].append(alert_rule)
            
            # データベースに保存
            await self.save_keyword_alert_to_database(guild_id, alert_rule)
            
            embed = discord.Embed(
                title="🔔 キーワード通知を設定しました",
                color=0xff9900,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="🎯 キーワード",
                value=f"`{keyword}`",
                inline=True
            )
            
            embed.add_field(
                name="👥 通知対象",
                value=mention_role.mention if mention_role else "設定者のみ",
                inline=True
            )
            
            embed.add_field(
                name="🆔 ルールID",
                value=f"`{alert_rule['id']}`",
                inline=True
            )
            
            embed.set_footer(text="キーワードが含まれるメッセージで通知します")
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Keyword alert setup error: {e}")
            await ctx.send(f"❌ キーワード通知設定エラー: {str(e)}")

    @commands.hybrid_command(name='schedule_message')
    async def schedule_message(self, ctx, date_time: str, *, message: str):
        """メッセージを予約送信 (/schedule_message "2024/12/31 15:30" 新年のご挨拶)"""
        try:
            # 日時解析
            try:
                if re.match(r'^\d{4}/\d{1,2}/\d{1,2} \d{1,2}:\d{2}$', date_time):
                    scheduled_time = datetime.strptime(date_time, '%Y/%m/%d %H:%M')
                elif re.match(r'^\d{1,2}/\d{1,2} \d{1,2}:\d{2}$', date_time):
                    current_year = datetime.now().year
                    scheduled_time = datetime.strptime(f"{current_year}/{date_time}", '%Y/%m/%d %H:%M')
                else:
                    await ctx.send("❌ 日時フォーマットが正しくありません。\n例: `2024/12/31 15:30` または `12/31 15:30`")
                    return
                
                if scheduled_time < datetime.now():
                    await ctx.send("❌ 過去の日時は設定できません。")
                    return
                    
            except ValueError:
                await ctx.send("❌ 無効な日時です。正しい日時を入力してください。")
                return
            
            guild_id = ctx.guild.id
            if guild_id not in self.scheduled_messages:
                self.scheduled_messages[guild_id] = []
            
            scheduled_msg = {
                'id': len(self.scheduled_messages[guild_id]) + 1,
                'channel_id': ctx.channel.id,
                'creator_id': ctx.author.id,
                'creator_name': ctx.author.display_name,
                'scheduled_time': scheduled_time.isoformat(),
                'message': message,
                'created_at': datetime.now().isoformat(),
                'sent': False
            }
            
            self.scheduled_messages[guild_id].append(scheduled_msg)
            
            # データベースに保存
            await self.save_scheduled_message_to_database(guild_id, scheduled_msg)
            
            embed = discord.Embed(
                title="📅 メッセージを予約しました",
                description=f"**{message}**",
                color=0x00ff9f,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="📆 送信予定時刻",
                value=scheduled_time.strftime('%Y年%m月%d日 %H:%M'),
                inline=True
            )
            
            embed.add_field(
                name="🆔 メッセージID",
                value=f"`{scheduled_msg['id']}`",
                inline=True
            )
            
            time_until = scheduled_time - datetime.now()
            if time_until.days > 0:
                time_str = f"あと{time_until.days}日"
            elif time_until.seconds > 3600:
                hours = time_until.seconds // 3600
                time_str = f"あと{hours}時間"
            else:
                minutes = time_until.seconds // 60
                time_str = f"あと{minutes}分"
            
            embed.add_field(
                name="⏳ 残り時間",
                value=time_str,
                inline=True
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Schedule message error: {e}")
            await ctx.send(f"❌ メッセージ予約エラー: {str(e)}")

    @commands.hybrid_command(name='list_automation')
    async def list_automation_rules(self, ctx):
        """自動化ルール一覧 (/list_automation)"""
        try:
            guild_id = ctx.guild.id
            
            embed = discord.Embed(
                title="🤖 自動化ルール一覧",
                color=0x00ff9f,
                timestamp=datetime.utcnow()
            )
            
            # 自動返信ルール
            if guild_id in self.auto_responses and self.auto_responses[guild_id]:
                auto_response_text = []
                for rule in self.auto_responses[guild_id][:5]:  # 最大5件表示
                    status = "✅" if rule['enabled'] else "❌"
                    auto_response_text.append(
                        f"{status} `{rule['id']}` {rule['trigger']} → {rule['response'][:30]}..."
                    )
                
                embed.add_field(
                    name="💬 自動返信",
                    value="\n".join(auto_response_text) if auto_response_text else "なし",
                    inline=False
                )
            
            # キーワード通知
            if guild_id in self.keyword_alerts and self.keyword_alerts[guild_id]:
                keyword_alert_text = []
                for rule in self.keyword_alerts[guild_id][:5]:
                    status = "✅" if rule['enabled'] else "❌"
                    role_name = rule.get('mention_role_name', '設定者のみ')
                    keyword_alert_text.append(
                        f"{status} `{rule['id']}` {rule['keyword']} → {role_name}"
                    )
                
                embed.add_field(
                    name="🔔 キーワード通知",
                    value="\n".join(keyword_alert_text) if keyword_alert_text else "なし",
                    inline=False
                )
            
            # 予約メッセージ
            if guild_id in self.scheduled_messages and self.scheduled_messages[guild_id]:
                future_messages = []
                current_time = datetime.now()
                
                for msg in self.scheduled_messages[guild_id]:
                    if not msg['sent']:
                        scheduled_time = datetime.fromisoformat(msg['scheduled_time'])
                        if scheduled_time > current_time:
                            future_messages.append(msg)
                
                if future_messages:
                    scheduled_text = []
                    for msg in future_messages[:3]:  # 最大3件表示
                        scheduled_time = datetime.fromisoformat(msg['scheduled_time'])
                        scheduled_text.append(
                            f"📅 `{msg['id']}` {scheduled_time.strftime('%m/%d %H:%M')} - {msg['message'][:30]}..."
                        )
                    
                    embed.add_field(
                        name="📅 予約メッセージ",
                        value="\n".join(scheduled_text),
                        inline=False
                    )
            
            # 何もない場合
            if not embed.fields:
                embed.description = "現在設定されている自動化ルールはありません。"
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"List automation error: {e}")
            await ctx.send("❌ 自動化ルール一覧表示中にエラーが発生しました。")

    @commands.hybrid_command(name='toggle_automation')
    async def toggle_automation_rule(self, ctx, rule_type: str, rule_id: int):
        """自動化ルールのON/OFF切り替え (/toggle_automation auto_response 1)"""
        try:
            guild_id = ctx.guild.id
            
            if rule_type not in ['auto_response', 'keyword_alert']:
                await ctx.send("❌ ルールタイプは `auto_response` または `keyword_alert` を指定してください。")
                return
            
            rule_found = False
            
            if rule_type == 'auto_response':
                if guild_id in self.auto_responses:
                    for rule in self.auto_responses[guild_id]:
                        if rule['id'] == rule_id:
                            rule['enabled'] = not rule['enabled']
                            status = "有効" if rule['enabled'] else "無効"
                            
                            embed = discord.Embed(
                                title="🔄 自動返信ルールを更新しました",
                                description=f"ルールID `{rule_id}` を **{status}** にしました",
                                color=0x00ff9f if rule['enabled'] else 0x808080,
                                timestamp=datetime.utcnow()
                            )
                            
                            await ctx.send(embed=embed)
                            rule_found = True
                            break
            
            elif rule_type == 'keyword_alert':
                if guild_id in self.keyword_alerts:
                    for rule in self.keyword_alerts[guild_id]:
                        if rule['id'] == rule_id:
                            rule['enabled'] = not rule['enabled']
                            status = "有効" if rule['enabled'] else "無効"
                            
                            embed = discord.Embed(
                                title="🔄 キーワード通知ルールを更新しました",
                                description=f"ルールID `{rule_id}` を **{status}** にしました",
                                color=0xff9900 if rule['enabled'] else 0x808080,
                                timestamp=datetime.utcnow()
                            )
                            
                            await ctx.send(embed=embed)
                            rule_found = True
                            break
            
            if not rule_found:
                await ctx.send(f"❌ {rule_type} のルールID `{rule_id}` が見つかりません。")
            
        except Exception as e:
            logger.error(f"Toggle automation error: {e}")
            await ctx.send(f"❌ ルール切り替えエラー: {str(e)}")

    @commands.Cog.listener()
    async def on_message(self, message):
        """メッセージ監視（自動返信・キーワード通知）"""
        if message.author.bot:
            return
        
        guild_id = message.guild.id if message.guild else None
        if not guild_id:
            return
        
        try:
            # 自動返信チェック
            if guild_id in self.auto_responses:
                for rule in self.auto_responses[guild_id]:
                    if rule['enabled'] and rule['trigger'].lower() in message.content.lower():
                        # 使用回数を更新
                        rule['usage_count'] += 1
                        
                        # 返信送信
                        await message.reply(rule['response'], mention_author=False)
                        logger.info(f"Auto response triggered: {rule['trigger']}")
                        break
            
            # キーワード通知チェック
            if guild_id in self.keyword_alerts:
                for rule in self.keyword_alerts[guild_id]:
                    if rule['enabled'] and rule['keyword'].lower() in message.content.lower():
                        # 通知回数を更新
                        rule['alert_count'] += 1
                        
                        # 通知送信
                        embed = discord.Embed(
                            title="🚨 キーワード検出",
                            description=f"キーワード「**{rule['keyword']}**」が検出されました",
                            color=0xff0000,
                            timestamp=datetime.utcnow()
                        )
                        
                        embed.add_field(
                            name="📝 メッセージ",
                            value=f"```{message.content[:500]}```",
                            inline=False
                        )
                        
                        embed.add_field(
                            name="👤 投稿者",
                            value=message.author.mention,
                            inline=True
                        )
                        
                        embed.add_field(
                            name="📍 チャンネル",
                            value=message.channel.mention,
                            inline=True
                        )
                        
                        # メンション対象を決定
                        mention_text = ""
                        if rule['mention_role_id']:
                            role = message.guild.get_role(rule['mention_role_id'])
                            if role:
                                mention_text = role.mention
                        else:
                            creator = message.guild.get_member(rule['creator_id'])
                            if creator:
                                mention_text = creator.mention
                        
                        await message.channel.send(mention_text, embed=embed)
                        logger.info(f"Keyword alert triggered: {rule['keyword']}")
                        
        except Exception as e:
            logger.error(f"Message monitoring error: {e}")

    @tasks.loop(minutes=1)
    async def automation_check_task(self):
        """定期的に予約メッセージをチェック"""
        try:
            current_time = datetime.now()
            
            for guild_id, messages in self.scheduled_messages.items():
                for msg in messages[:]:
                    if msg['sent']:
                        continue
                    
                    scheduled_time = datetime.fromisoformat(msg['scheduled_time'])
                    if scheduled_time <= current_time:
                        await self.send_scheduled_message(guild_id, msg)
                        msg['sent'] = True
                        
        except Exception as e:
            logger.error(f"Automation check task error: {e}")

    @automation_check_task.before_loop
    async def before_automation_check(self):
        """自動化チェックタスク開始前の待機"""
        await self.bot.wait_until_ready()

    async def send_scheduled_message(self, guild_id: int, scheduled_msg: dict):
        """予約メッセージを送信"""
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return
            
            channel = guild.get_channel(scheduled_msg['channel_id'])
            if not channel:
                return
            
            embed = discord.Embed(
                title="📅 予約メッセージ",
                description=scheduled_msg['message'],
                color=0x00ff9f,
                timestamp=datetime.utcnow()
            )
            
            embed.set_footer(text=f"予約者: {scheduled_msg['creator_name']}")
            
            await channel.send(embed=embed)
            logger.info(f"Scheduled message sent: {scheduled_msg['message'][:50]}")
            
        except Exception as e:
            logger.error(f"Error sending scheduled message: {e}")

    async def save_auto_response_to_database(self, guild_id: int, rule: dict):
        """自動返信ルールをデータベースに保存"""
        try:
            if hasattr(self.bot, 'db_manager') and self.bot.db_manager:
                query = """
                INSERT INTO auto_responses (guild_id, trigger_text, response_text, creator_id, 
                                          creator_name, channel_id, created_at, enabled, usage_count)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """
                await self.bot.db_manager.execute_query(
                    query, guild_id, rule['trigger'], rule['response'], rule['creator_id'],
                    rule['creator_name'], rule['channel_id'], rule['created_at'],
                    rule['enabled'], rule['usage_count']
                )
        except Exception as e:
            logger.error(f"Error saving auto response to database: {e}")

    async def save_keyword_alert_to_database(self, guild_id: int, rule: dict):
        """キーワード通知ルールをデータベースに保存"""
        try:
            if hasattr(self.bot, 'db_manager') and self.bot.db_manager:
                query = """
                INSERT INTO keyword_alerts (guild_id, keyword, mention_role_id, mention_role_name,
                                          creator_id, creator_name, channel_id, created_at, enabled, alert_count)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """
                await self.bot.db_manager.execute_query(
                    query, guild_id, rule['keyword'], rule['mention_role_id'], rule['mention_role_name'],
                    rule['creator_id'], rule['creator_name'], rule['channel_id'], rule['created_at'],
                    rule['enabled'], rule['alert_count']
                )
        except Exception as e:
            logger.error(f"Error saving keyword alert to database: {e}")

    async def save_scheduled_message_to_database(self, guild_id: int, msg: dict):
        """予約メッセージをデータベースに保存"""
        try:
            if hasattr(self.bot, 'db_manager') and self.bot.db_manager:
                query = """
                INSERT INTO scheduled_messages (guild_id, channel_id, creator_id, creator_name,
                                              scheduled_time, message, created_at, sent)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """
                await self.bot.db_manager.execute_query(
                    query, guild_id, msg['channel_id'], msg['creator_id'], msg['creator_name'],
                    msg['scheduled_time'], msg['message'], msg['created_at'], msg['sent']
                )
        except Exception as e:
            logger.error(f"Error saving scheduled message to database: {e}")

async def setup(bot):
    await bot.add_cog(AutomationCog(bot))