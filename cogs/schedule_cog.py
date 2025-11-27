import os
import asyncio
import logging
from typing import Dict, List, Optional
import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta, timezone
import json
import re
from database.models import UserProfile, DatabaseHelpers
from config import *

logger = logging.getLogger(__name__)

class ScheduleCog(commands.Cog):
    """スケジュール・リマインダー機能"""
    
    def __init__(self, bot):
        self.bot = bot
        self.scheduled_events = {}  # guild_id -> events list
        self.reminders = {}  # user_id -> reminders list
        
        # スケジュールチェックタスクを開始
        self.schedule_check_task.start()
        
    def cog_unload(self):
        """Cog がアンロードされる時にタスクを停止"""
        if hasattr(self, 'schedule_check_task'):
            self.schedule_check_task.cancel()

    @commands.hybrid_command(name='schedule_event')
    async def schedule_event(self, ctx, date_time: str, *, event_description: str):
        """イベントをスケジュール (/schedule_event "YYYY/MM/DD HH:MM" イベント説明)"""
        try:
            # 日時解析
            try:
                # YYYY/MM/DD HH:MM または MM/DD HH:MM 形式をサポート
                if re.match(r'^\d{4}/\d{1,2}/\d{1,2} \d{1,2}:\d{2}$', date_time):
                    scheduled_time = datetime.strptime(date_time, '%Y/%m/%d %H:%M')
                elif re.match(r'^\d{1,2}/\d{1,2} \d{1,2}:\d{2}$', date_time):
                    current_year = datetime.now().year
                    scheduled_time = datetime.strptime(f"{current_year}/{date_time}", '%Y/%m/%d %H:%M')
                else:
                    await ctx.send("❌ 日時フォーマットが正しくありません。\n例: `2024/12/31 15:30` または `12/31 15:30`")
                    return
                
                # 過去の日時チェック
                if scheduled_time < datetime.now():
                    await ctx.send("❌ 過去の日時は設定できません。")
                    return
                    
            except ValueError:
                await ctx.send("❌ 無効な日時です。正しい日時を入力してください。")
                return
            
            # イベント情報を保存
            guild_id = ctx.guild.id
            if guild_id not in self.scheduled_events:
                self.scheduled_events[guild_id] = []
            
            event = {
                'id': len(self.scheduled_events[guild_id]) + 1,
                'channel_id': ctx.channel.id,
                'creator_id': ctx.author.id,
                'creator_name': ctx.author.display_name,
                'scheduled_time': scheduled_time.isoformat(),
                'description': event_description,
                'created_at': datetime.now().isoformat(),
                'notified': False
            }
            
            self.scheduled_events[guild_id].append(event)
            
            # データベースに保存
            await self.save_event_to_database(ctx.guild.id, event)
            
            embed = discord.Embed(
                title="📅 イベントをスケジュールしました",
                description=f"**{event_description}**",
                color=0x00ff9f,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="📆 日時",
                value=f"{scheduled_time.strftime('%Y年%m月%d日 %H:%M')}",
                inline=True
            )
            
            embed.add_field(
                name="👤 作成者",
                value=ctx.author.display_name,
                inline=True
            )
            
            embed.add_field(
                name="🆔 イベントID",
                value=f"`{event['id']}`",
                inline=True
            )
            
            embed.set_footer(text="イベント時刻に自動で通知します")
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Schedule event error: {e}")
            await ctx.send(f"❌ イベントスケジュールエラー: {str(e)}")

    @commands.hybrid_command(name='list_events')
    async def list_events(self, ctx):
        """予定されているイベント一覧 (/list_events)"""
        try:
            guild_id = ctx.guild.id
            
            if guild_id not in self.scheduled_events or not self.scheduled_events[guild_id]:
                embed = discord.Embed(
                    title="📅 予定されているイベント",
                    description="現在予定されているイベントはありません。",
                    color=0x808080
                )
                await ctx.send(embed=embed)
                return
            
            # データベースからも読み込み
            await self.load_events_from_database(guild_id)
            
            # 未来のイベントのみフィルタ
            current_time = datetime.now()
            future_events = []
            
            for event in self.scheduled_events[guild_id]:
                event_time = datetime.fromisoformat(event['scheduled_time'])
                if event_time > current_time:
                    future_events.append(event)
            
            if not future_events:
                embed = discord.Embed(
                    title="📅 予定されているイベント",
                    description="現在予定されているイベントはありません。",
                    color=0x808080
                )
                await ctx.send(embed=embed)
                return
            
            # 日時順でソート
            future_events.sort(key=lambda x: datetime.fromisoformat(x['scheduled_time']))
            
            embed = discord.Embed(
                title="📅 予定されているイベント一覧",
                description="今後予定されているイベントです",
                color=0x00ff9f,
                timestamp=datetime.utcnow()
            )
            
            for i, event in enumerate(future_events[:10]):  # 最大10件表示
                event_time = datetime.fromisoformat(event['scheduled_time'])
                time_until = event_time - current_time
                
                if time_until.days > 0:
                    time_str = f"あと{time_until.days}日"
                elif time_until.seconds > 3600:
                    hours = time_until.seconds // 3600
                    time_str = f"あと{hours}時間"
                else:
                    minutes = time_until.seconds // 60
                    time_str = f"あと{minutes}分"
                
                embed.add_field(
                    name=f"🎯 {event['description']}",
                    value=f"**日時:** {event_time.strftime('%m/%d %H:%M')}\n"
                          f"**作成者:** {event['creator_name']}\n"
                          f"**残り時間:** {time_str}\n"
                          f"**ID:** `{event['id']}`",
                    inline=False
                )
            
            if len(future_events) > 10:
                embed.set_footer(text=f"他 {len(future_events) - 10} 件のイベントがあります")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"List events error: {e}")
            await ctx.send("❌ イベント一覧表示中にエラーが発生しました。")

    @commands.hybrid_command(name='cancel_event')
    async def cancel_event(self, ctx, event_id: int):
        """イベントをキャンセル (/cancel_event イベントID)"""
        try:
            guild_id = ctx.guild.id
            
            if guild_id not in self.scheduled_events:
                await ctx.send("❌ 予定されているイベントがありません。")
                return
            
            # イベントを探す
            event_to_remove = None
            for event in self.scheduled_events[guild_id]:
                if event['id'] == event_id:
                    event_to_remove = event
                    break
            
            if not event_to_remove:
                await ctx.send(f"❌ ID `{event_id}` のイベントが見つかりません。")
                return
            
            # 作成者または管理者権限チェック
            if (ctx.author.id != event_to_remove['creator_id'] and 
                not ctx.author.guild_permissions.manage_events):
                await ctx.send("❌ このイベントをキャンセルする権限がありません。")
                return
            
            # イベントを削除
            self.scheduled_events[guild_id].remove(event_to_remove)
            
            # データベースからも削除
            await self.delete_event_from_database(guild_id, event_id)
            
            embed = discord.Embed(
                title="🗑️ イベントをキャンセルしました",
                description=f"**{event_to_remove['description']}**",
                color=0xff6b6b,
                timestamp=datetime.utcnow()
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Cancel event error: {e}")
            await ctx.send(f"❌ イベントキャンセルエラー: {str(e)}")

    @commands.hybrid_command(name='set_reminder')
    async def set_reminder(self, ctx, time_str: str, *, message: str):
        """個人リマインダー設定 (/set_reminder "30m" メッセージ または "2024/12/31 15:30" メッセージ)"""
        try:
            # 時間解析
            remind_time = None
            
            # 相対時間（例: 30m, 2h, 1d）
            if re.match(r'^\d+[mhd]$', time_str.lower()):
                number = int(re.search(r'\d+', time_str).group())
                unit = time_str[-1].lower()
                
                if unit == 'm':
                    remind_time = datetime.now() + timedelta(minutes=number)
                elif unit == 'h':
                    remind_time = datetime.now() + timedelta(hours=number)
                elif unit == 'd':
                    remind_time = datetime.now() + timedelta(days=number)
            
            # 絶対時間（例: 2024/12/31 15:30）
            elif re.match(r'^\d{4}/\d{1,2}/\d{1,2} \d{1,2}:\d{2}$', time_str):
                remind_time = datetime.strptime(time_str, '%Y/%m/%d %H:%M')
            elif re.match(r'^\d{1,2}/\d{1,2} \d{1,2}:\d{2}$', time_str):
                current_year = datetime.now().year
                remind_time = datetime.strptime(f"{current_year}/{time_str}", '%Y/%m/%d %H:%M')
            
            if not remind_time:
                await ctx.send("❌ 時間フォーマットが正しくありません。\n"
                             "例: `30m`, `2h`, `1d` または `2024/12/31 15:30`")
                return
            
            if remind_time < datetime.now():
                await ctx.send("❌ 過去の時間は設定できません。")
                return
            
            # リマインダー保存
            user_id = ctx.author.id
            if user_id not in self.reminders:
                self.reminders[user_id] = []
            
            reminder = {
                'id': len(self.reminders[user_id]) + 1,
                'channel_id': ctx.channel.id,
                'guild_id': ctx.guild.id,
                'remind_time': remind_time.isoformat(),
                'message': message,
                'created_at': datetime.now().isoformat(),
                'notified': False
            }
            
            self.reminders[user_id].append(reminder)
            
            # データベースに保存
            await self.save_reminder_to_database(user_id, reminder)
            
            embed = discord.Embed(
                title="⏰ リマインダーを設定しました",
                description=f"**{message}**",
                color=0x00ff9f,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="🕐 通知時刻",
                value=remind_time.strftime('%Y年%m月%d日 %H:%M'),
                inline=True
            )
            
            time_until = remind_time - datetime.now()
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
            logger.error(f"Set reminder error: {e}")
            await ctx.send(f"❌ リマインダー設定エラー: {str(e)}")

    @tasks.loop(minutes=1)
    async def schedule_check_task(self):
        """定期的にスケジュールとリマインダーをチェック"""
        try:
            current_time = datetime.now()
            
            # イベント通知チェック
            for guild_id, events in self.scheduled_events.items():
                for event in events[:]:  # コピーでイテレート
                    if event.get('notified'):
                        continue
                    
                    event_time = datetime.fromisoformat(event['scheduled_time'])
                    if event_time <= current_time:
                        await self.notify_event(guild_id, event)
                        event['notified'] = True
            
            # リマインダー通知チェック
            for user_id, reminders in self.reminders.items():
                for reminder in reminders[:]:  # コピーでイテレート
                    if reminder.get('notified'):
                        continue
                    
                    remind_time = datetime.fromisoformat(reminder['remind_time'])
                    if remind_time <= current_time:
                        await self.notify_reminder(user_id, reminder)
                        reminder['notified'] = True
                        
        except Exception as e:
            logger.error(f"Schedule check task error: {e}")

    @schedule_check_task.before_loop
    async def before_schedule_check(self):
        """スケジュールチェックタスク開始前の待機"""
        await self.bot.wait_until_ready()

    async def notify_event(self, guild_id: int, event: dict):
        """イベント通知を送信"""
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return
            
            channel = guild.get_channel(event['channel_id'])
            if not channel:
                return
            
            embed = discord.Embed(
                title="🔔 イベント通知",
                description=f"**{event['description']}** の時間です！",
                color=0xff9900,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="👤 作成者",
                value=event['creator_name'],
                inline=True
            )
            
            embed.add_field(
                name="📅 予定時刻",
                value=datetime.fromisoformat(event['scheduled_time']).strftime('%Y年%m月%d日 %H:%M'),
                inline=True
            )
            
            # 作成者にメンション
            creator = guild.get_member(event['creator_id'])
            mention_text = f"{creator.mention} " if creator else ""
            
            await channel.send(f"{mention_text}🎯", embed=embed)
            logger.info(f"Event notification sent: {event['description']}")
            
        except Exception as e:
            logger.error(f"Error sending event notification: {e}")

    async def notify_reminder(self, user_id: int, reminder: dict):
        """リマインダー通知を送信"""
        try:
            user = self.bot.get_user(user_id)
            if not user:
                return
            
            guild = self.bot.get_guild(reminder['guild_id'])
            channel = guild.get_channel(reminder['channel_id']) if guild else None
            
            embed = discord.Embed(
                title="⏰ リマインダー",
                description=f"**{reminder['message']}**",
                color=0xff6b6b,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="🕐 設定時刻",
                value=datetime.fromisoformat(reminder['remind_time']).strftime('%Y年%m月%d日 %H:%M'),
                inline=True
            )
            
            # チャンネルまたはDMに送信
            if channel and channel.permissions_for(guild.me).send_messages:
                await channel.send(f"{user.mention} 📢", embed=embed)
            else:
                try:
                    await user.send(embed=embed)
                except discord.Forbidden:
                    logger.warning(f"Could not send reminder to user {user_id}")
            
            logger.info(f"Reminder notification sent: {reminder['message']}")
            
        except Exception as e:
            logger.error(f"Error sending reminder notification: {e}")

    async def save_event_to_database(self, guild_id: int, event: dict):
        """イベントをデータベースに保存"""
        try:
            if hasattr(self.bot, 'db_manager') and self.bot.db_manager:
                query = """
                INSERT INTO scheduled_events (guild_id, channel_id, creator_id, creator_name, 
                                            scheduled_time, description, created_at, notified)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """
                await self.bot.db_manager.execute_query(
                    query, guild_id, event['channel_id'], event['creator_id'],
                    event['creator_name'], event['scheduled_time'], event['description'],
                    event['created_at'], event['notified']
                )
        except Exception as e:
            logger.error(f"Error saving event to database: {e}")

    async def save_reminder_to_database(self, user_id: int, reminder: dict):
        """リマインダーをデータベースに保存"""
        try:
            if hasattr(self.bot, 'db_manager') and self.bot.db_manager:
                query = """
                INSERT INTO reminders (user_id, channel_id, guild_id, remind_time, 
                                     message, created_at, notified)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """
                await self.bot.db_manager.execute_query(
                    query, user_id, reminder['channel_id'], reminder['guild_id'],
                    reminder['remind_time'], reminder['message'], 
                    reminder['created_at'], reminder['notified']
                )
        except Exception as e:
            logger.error(f"Error saving reminder to database: {e}")

    async def load_events_from_database(self, guild_id: int):
        """データベースからイベントを読み込み"""
        try:
            if hasattr(self.bot, 'db_manager') and self.bot.db_manager:
                query = "SELECT * FROM scheduled_events WHERE guild_id = $1 AND notified = FALSE"
                events = await self.bot.db_manager.fetch_all(query, guild_id)
                
                if events:
                    if guild_id not in self.scheduled_events:
                        self.scheduled_events[guild_id] = []
                    
                    for row in events:
                        event = {
                            'id': row['id'],
                            'channel_id': row['channel_id'],
                            'creator_id': row['creator_id'],
                            'creator_name': row['creator_name'],
                            'scheduled_time': row['scheduled_time'],
                            'description': row['description'],
                            'created_at': row['created_at'],
                            'notified': row['notified']
                        }
                        
                        # 重複チェック
                        if not any(e['id'] == event['id'] for e in self.scheduled_events[guild_id]):
                            self.scheduled_events[guild_id].append(event)
                            
        except Exception as e:
            logger.error(f"Error loading events from database: {e}")

    async def delete_event_from_database(self, guild_id: int, event_id: int):
        """データベースからイベントを削除"""
        try:
            if hasattr(self.bot, 'db_manager') and self.bot.db_manager:
                query = "DELETE FROM scheduled_events WHERE guild_id = $1 AND id = $2"
                await self.bot.db_manager.execute_query(query, guild_id, event_id)
        except Exception as e:
            logger.error(f"Error deleting event from database: {e}")

async def setup(bot):
    await bot.add_cog(ScheduleCog(bot))