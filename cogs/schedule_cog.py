import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ScheduleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.schedules_file = "data/schedules.json"
        self.schedules = self.load_schedules()

    def load_schedules(self):
        if os.path.exists(self.schedules_file):
            try:
                with open(self.schedules_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_schedules(self):
        os.makedirs(os.path.dirname(self.schedules_file), exist_ok=True)
        with open(self.schedules_file, 'w', encoding='utf-8') as f:
            json.dump(self.schedules, f, ensure_ascii=False, indent=4)

    @commands.hybrid_group(name="schedule", description="スケジュール調整")
    async def schedule(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("サブコマンドを指定してください: create")

    @schedule.command(name="create", description="日程調整を作成します")
    @app_commands.describe(title="イベント名", dates="候補日（カンマ区切り, 例: 12/1 21:00, 12/2 22:00）")
    async def create(self, ctx, title: str, dates: str):
        """Create a schedule poll"""
        date_list = [d.strip() for d in dates.split(',')]
        
        # Create initial data structure
        schedule_id = str(ctx.message.id) # Use message ID as key (will update after sending)
        
        embed = discord.Embed(
            title=f"📅 日程調整: {title}",
            description="下のボタンから参加可能な日程を回答してください。",
            color=0x00BFFF,
            timestamp=datetime.now()
        )
        embed.add_field(name="主催者", value=ctx.author.display_name, inline=False)
        
        # Initial table
        table_text = self.generate_table_text(date_list, {})
        embed.add_field(name="集計状況", value=table_text, inline=False)
        
        view = ScheduleView(self, schedule_id, date_list)
        msg = await ctx.send(embed=embed, view=view)
        
        # Update ID to actual message ID and save
        real_id = str(msg.id)
        view.schedule_id = real_id # Update view's ID reference
        
        self.schedules[real_id] = {
            "title": title,
            "dates": date_list,
            "responses": {}, # user_id: {date: status} (status: 0=x, 1=ok, 2=maybe)
            "channel_id": ctx.channel.id,
            "author_id": ctx.author.id
        }
        self.save_schedules()

    def generate_table_text(self, dates, responses):
        text = "```\n"
        # Header
        # text += "日程             | 〇 | △ | ✕ | メンバー\n"
        # text += "-" * 40 + "\n"
        
        for date in dates:
            ok_users = []
            maybe_users = []
            ng_users = []
            
            for uid, user_resp in responses.items():
                status = user_resp.get(date, 0) # Default to 0 (unknown/ng) - actually let's say 0 is unselected
                # Let's define: 1=OK, 2=Maybe, 0=None/NG
                # But we need to know who responded.
                # Let's simplify: If user is in responses, they responded.
                
                if status == 1:
                    ok_users.append(uid)
                elif status == 2:
                    maybe_users.append(uid)
                else:
                    ng_users.append(uid) # Explicit NG or just not selected but responded
            
            # Count
            ok_count = len(ok_users)
            maybe_count = len(maybe_users)
            
            # Format line
            # 12/01 21:00 | 〇3 △1
            text += f"{date:<15} | 〇{ok_count} △{maybe_count}\n"
            
        text += "```"
        return text

    async def update_schedule_message(self, message_id):
        data = self.schedules.get(message_id)
        if not data:
            return
            
        channel = self.bot.get_channel(data["channel_id"])
        if not channel:
            return
            
        try:
            msg = await channel.fetch_message(int(message_id))
        except:
            return
            
        embed = msg.embeds[0]
        
        # Re-generate table
        table_text = self.generate_table_text(data["dates"], data["responses"])
        
        # Find the field to update
        for i, field in enumerate(embed.fields):
            if field.name == "集計状況":
                embed.set_field_at(i, name="集計状況", value=table_text, inline=False)
                break
        
        # Add detailed list field
        details = ""
        # Get all users who responded
        responder_ids = list(data["responses"].keys())
        if responder_ids:
            details += "**回答済みメンバー**:\n"
            for uid in responder_ids:
                member = channel.guild.get_member(int(uid))
                name = member.display_name if member else "Unknown"
                details += f"{name}, "
            details = details.rstrip(", ")
        
        # Update or add details field
        found_details = False
        for i, field in enumerate(embed.fields):
            if field.name == "詳細":
                embed.set_field_at(i, name="詳細", value=details or "なし", inline=False)
                found_details = True
                break
        if not found_details and details:
            embed.add_field(name="詳細", value=details, inline=False)

        await msg.edit(embed=embed)


class ScheduleView(discord.ui.View):
    def __init__(self, cog, schedule_id, dates):
        super().__init__(timeout=None)
        self.cog = cog
        self.schedule_id = schedule_id
        self.dates = dates

    @discord.ui.button(label="回答する", style=discord.ButtonStyle.primary, emoji="📝", custom_id="schedule_answer_btn")
    async def answer_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # We need to ensure we have the correct schedule_id if it was updated from temp ID
        # The custom_id is static, so we rely on the view's state or the message ID
        real_id = str(interaction.message.id)
        
        data = self.cog.schedules.get(real_id)
        if not data:
            await interaction.response.send_message("❌ データが見つかりません。", ephemeral=True)
            return

        # Create a view for selection
        view = ResponseView(self.cog, real_id, data["dates"])
        await interaction.response.send_message("参加可能な日程を選んでください。", view=view, ephemeral=True)


class ResponseView(discord.ui.View):
    def __init__(self, cog, schedule_id, dates):
        super().__init__(timeout=180)
        self.cog = cog
        self.schedule_id = schedule_id
        self.dates = dates
        
        # Select for OK
        options_ok = []
        for date in dates:
            options_ok.append(discord.SelectOption(label=date, value=date))
        
        if len(options_ok) > 25:
            options_ok = options_ok[:25] # Limit
            
        self.select_ok = discord.ui.Select(placeholder="参加できる日程 (〇)", min_values=0, max_values=len(options_ok), options=options_ok)
        self.select_ok.callback = self.callback_ok
        self.add_item(self.select_ok)
        
        # Select for Maybe
        # We can't reuse options objects, need new ones
        options_maybe = []
        for date in dates:
            options_maybe.append(discord.SelectOption(label=date, value=date))
            
        if len(options_maybe) > 25:
            options_maybe = options_maybe[:25]

        self.select_maybe = discord.ui.Select(placeholder="微妙な日程 (△)", min_values=0, max_values=len(options_maybe), options=options_maybe)
        self.select_maybe.callback = self.callback_maybe
        self.add_item(self.select_maybe)
        
        self.ok_dates = []
        self.maybe_dates = []

    async def callback_ok(self, interaction: discord.Interaction):
        self.ok_dates = self.select_ok.values
        await interaction.response.defer()

    async def callback_maybe(self, interaction: discord.Interaction):
        self.maybe_dates = self.select_maybe.values
        await interaction.response.defer()

    @discord.ui.button(label="送信", style=discord.ButtonStyle.success)
    async def submit(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        
        # Update data
        if self.schedule_id not in self.cog.schedules:
            await interaction.response.send_message("エラー: データがありません", ephemeral=True)
            return
            
        responses = {}
        for date in self.dates:
            if date in self.ok_dates:
                responses[date] = 1
            elif date in self.maybe_dates:
                responses[date] = 2
            else:
                responses[date] = 0 # NG
        
        self.cog.schedules[self.schedule_id]["responses"][user_id] = responses
        self.cog.save_schedules()
        
        await self.cog.update_schedule_message(self.schedule_id)
        await interaction.response.send_message("✅ 回答を記録しました！", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ScheduleCog(bot))