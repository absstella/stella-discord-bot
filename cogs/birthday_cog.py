import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
import os
import datetime
import logging

logger = logging.getLogger(__name__)

BIRTHDAY_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "birthdays.json")

class BirthdayCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.birthdays = self.load_birthdays()
        self.check_birthdays.start()

    def load_birthdays(self):
        if not os.path.exists(BIRTHDAY_FILE):
            return {}
        try:
            with open(BIRTHDAY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load birthdays: {e}")
            return {}

    def save_birthdays(self):
        os.makedirs(os.path.dirname(BIRTHDAY_FILE), exist_ok=True)
        try:
            with open(BIRTHDAY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.birthdays, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save birthdays: {e}")

    # Create a slash command group
    birthday_group = app_commands.Group(name="birthday", description="誕生日機能")

    @birthday_group.command(name="set", description="誕生日を登録します (形式: YYYY-MM-DD)")
    @app_commands.describe(date="誕生日 (例: 2000-01-01)")
    async def set_birthday(self, interaction: discord.Interaction, date: str):
        """誕生日を登録します"""
        try:
            # Validate date format
            date_obj = datetime.datetime.strptime(date, "%Y-%m-%d").date()
            
            # Store as string
            user_id = str(interaction.user.id)
            self.birthdays[user_id] = {
                "date": date,
                "last_celebrated": None
            }
            self.save_birthdays()
            
            await interaction.response.send_message(f"🎂 **登録完了**: {interaction.user.mention} さんの誕生日を `{date}` に設定しました！")
            
        except ValueError:
            await interaction.response.send_message("❌ **エラー**: 日付の形式が正しくありません。`YYYY-MM-DD` (例: 2000-01-01) で入力してください。", ephemeral=True)

    async def register_birthday_internal(self, user_id: int, date_str: str) -> str:
        """Internal method to register birthday from other cogs"""
        try:
            # Validate date format
            date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            
            # Store as string
            self.birthdays[str(user_id)] = {
                "date": date_str,
                "last_celebrated": None
            }
            self.save_birthdays()
            return f"🎂 誕生日を `{date_str}` に設定しました！"
        except ValueError:
            return "❌ 日付の形式が正しくありません。`YYYY-MM-DD` (例: 2000-01-01) で指定してください。"

    async def check_birthday_internal(self, user_id: int) -> str:
        """Internal method to check birthday"""
        if str(user_id) in self.birthdays:
            data = self.birthdays[str(user_id)]
            return f"📅 誕生日は `{data['date']}` です。"
        else:
            return "❓ 誕生日は登録されていません。"

    @birthday_group.command(name="check", description="自分または他の人の誕生日を確認します")
    @app_commands.describe(target="確認するユーザー (省略時は自分)")
    async def check_birthday(self, interaction: discord.Interaction, target: discord.Member = None):
        """誕生日を確認します"""
        target_user = target or interaction.user
        user_id = str(target_user.id)
        
        if user_id in self.birthdays:
            data = self.birthdays[user_id]
            await interaction.response.send_message(f"📅 **{target_user.display_name}** さんの誕生日は `{data['date']}` です。")
        else:
            await interaction.response.send_message(f"❓ **{target_user.display_name}** さんの誕生日は登録されていません。", ephemeral=True)

    @birthday_group.command(name="channel", description="[管理者] 誕生日メッセージを送るチャンネルを設定します")
    @app_commands.describe(channel="設定するチャンネル")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """チャンネルを設定します"""
        if "channels" not in self.birthdays:
            self.birthdays["channels"] = {}
        
        self.birthdays["channels"][str(interaction.guild.id)] = channel.id
        self.save_birthdays()
        self.birthdays["channels"][str(interaction.guild.id)] = channel.id
        self.save_birthdays()
        await interaction.response.send_message(f"🎉 **設定完了**: 誕生日のお祝いメッセージを {channel.mention} に送信するように設定しました。")

    @birthday_group.command(name="admin_set", description="[管理者] 他のユーザーの誕生日を登録します")
    @app_commands.describe(target="対象ユーザー", date="誕生日 (例: 2000-01-01)")
    @app_commands.checks.has_permissions(administrator=True)
    async def admin_set_birthday(self, interaction: discord.Interaction, target: discord.Member, date: str):
        """管理者が他人の誕生日を設定します"""
        try:
            # Validate date format
            datetime.datetime.strptime(date, "%Y-%m-%d").date()
            
            user_id = str(target.id)
            self.birthdays[user_id] = {
                "date": date,
                "last_celebrated": None
            }
            self.save_birthdays()
            
            await interaction.response.send_message(f"👮 **管理者権限**: {target.mention} さんの誕生日を `{date}` に設定しました。")
            
        except ValueError:
            await interaction.response.send_message("❌ **エラー**: 日付の形式が正しくありません。`YYYY-MM-DD` (例: 2000-01-01) で入力してください。", ephemeral=True)

    @birthday_group.command(name="remove", description="[管理者] ユーザーの誕生日を削除します")
    @app_commands.describe(target="対象ユーザー")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_birthday(self, interaction: discord.Interaction, target: discord.Member):
        """誕生日を削除します"""
        user_id = str(target.id)
        if user_id in self.birthdays:
            del self.birthdays[user_id]
            self.save_birthdays()
            await interaction.response.send_message(f"🗑️ **削除完了**: {target.mention} さんの誕生日データを削除しました。")
        else:
            await interaction.response.send_message(f"❓ {target.mention} さんの誕生日は登録されていません。", ephemeral=True)

    def get_upcoming_birthdays(self, limit=5):
        """直近の誕生日リストを取得"""
        upcoming = []
        today = datetime.date.today()
        
        for user_id, data in self.birthdays.items():
            if user_id == "channels":
                continue
            
            try:
                bday_date = datetime.datetime.strptime(data["date"], "%Y-%m-%d").date()
                # Calculate next birthday
                next_bday = bday_date.replace(year=today.year)
                if next_bday < today:
                    next_bday = next_bday.replace(year=today.year + 1)
                
                days_until = (next_bday - today).days
                upcoming.append({
                    "user_id": user_id,
                    "date": data["date"],
                    "next_date": next_bday,
                    "days_until": days_until
                })
            except ValueError:
                continue
        
        # Sort by days until
        upcoming.sort(key=lambda x: x["days_until"])
        return upcoming[:limit]

    @tasks.loop(minutes=1)
    async def check_birthdays(self):
        """毎日日本時間の朝9時に誕生日をチェック"""
        # JST timezone
        jst = datetime.timezone(datetime.timedelta(hours=9))
        now = datetime.datetime.now(jst)
        
        # Check if it's 9:00 AM (allow some buffer for loop timing)
        if now.hour == 9 and now.minute == 0:
            today_str = now.strftime("%m-%d")
            current_year = now.year
            
            for user_id, data in self.birthdays.items():
                if user_id == "channels":
                    continue
                    
                # Parse stored date
                try:
                    bday_date = datetime.datetime.strptime(data["date"], "%Y-%m-%d").date()
                    bday_str = bday_date.strftime("%m-%d")
                    
                    # Check if today is birthday
                    if bday_str == today_str:
                        # Check if already celebrated this year
                        last_celebrated = data.get("last_celebrated")
                        if last_celebrated != current_year:
                            # Celebrate!
                            user = self.bot.get_user(int(user_id))
                            if user:
                                # Try to send DM first, or find a suitable channel
                                try:
                                    embed = discord.Embed(
                                        title="🎉 HAPPY BIRTHDAY! 🎉",
                                        description=f"{user.mention} さん、お誕生日おめでとうございます！\n素敵な1年になりますように！",
                                        color=0xFFD700
                                    )
                                    
                                    sent = False
                                    # Check for configured channels in mutual guilds
                                    for guild in self.bot.guilds:
                                        if guild.get_member(user.id):
                                            target_channel = None
                                            
                                            # Check configured channel
                                            if "channels" in self.birthdays and str(guild.id) in self.birthdays["channels"]:
                                                channel_id = self.birthdays["channels"][str(guild.id)]
                                                target_channel = guild.get_channel(channel_id)
                                            
                                            # Fallback to general/system
                                            if not target_channel:
                                                target_channel = discord.utils.get(guild.text_channels, name="general") or \
                                                                 discord.utils.get(guild.text_channels, name="雑談") or \
                                                                 guild.system_channel
                                            
                                            if target_channel and target_channel.permissions_for(guild.me).send_messages:
                                                await target_channel.send(content=user.mention, embed=embed)
                                                sent = True
                                                # We only send to one guild to avoid spamming if they are in multiple
                                                break
                                    
                                    if not sent:
                                        # Fallback to DM
                                        await user.send(embed=embed)
                                        
                                    # Update last celebrated
                                    data["last_celebrated"] = current_year
                                    self.save_birthdays()
                                    logger.info(f"Celebrated birthday for user {user_id}")
                                    
                                except Exception as e:
                                    logger.error(f"Failed to send birthday message to {user_id}: {e}")
                                    
                except Exception as e:
                    logger.error(f"Error processing birthday for {user_id}: {e}")

    @check_birthdays.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(BirthdayCog(bot))
