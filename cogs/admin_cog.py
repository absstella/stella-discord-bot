import discord
from discord import app_commands
from discord.ext import commands
import logging
from datetime import datetime, timezone
import os

logger = logging.getLogger(__name__)

class AdminLoginModal(discord.ui.Modal, title="システム管理者ログイン"):
    password = discord.ui.TextInput(
        label="パスワード",
        style=discord.TextStyle.short,
        placeholder="管理者パスワードを入力してください",
        required=True,
        min_length=1
    )
    
    command = discord.ui.TextInput(
        label="実行コマンド (任意)",
        style=discord.TextStyle.paragraph,
        placeholder="ログイン後に実行したいコマンドがあれば入力...",
        required=False
    )

    def __init__(self, bot, cog):
        super().__init__()
        self.bot = bot
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        password_input = self.password.value
        command_input = self.command.value
        
        # Verify password
        SYSTEM_ACCESS_PASSWORD = "ore25iti5"
        SECRET_RPG_PASSWORD = "416273434C" # AbsCL in hex
        
        if password_input == SECRET_RPG_PASSWORD:
            # Trigger RPG Mystery Event (Boot Sequence)
            await interaction.response.send_message("```\n> System Boot Initiated...\n```", ephemeral=True)
            msg = await interaction.original_response()
            
            import asyncio
            logs = [
                "> Verifying Identity...",
                "> Access Granted: LEVEL 5",
                "> Decrypting Secure Archives...",
                "> Loading 'Project: AbsCL'...",
                "> [====================] 100%",
                "> SYSTEM READY."
            ]
            
            current_log = "> System Boot Initiated...\n"
            for log in logs:
                await asyncio.sleep(1.0)
                current_log += f"{log}\n"
                await msg.edit(content=f"```\n{current_log}```")
            
            await asyncio.sleep(1.0)
            
            embed = discord.Embed(
                title="🔓 機密データ: AbsCL_Genesis",
                description="ようこそ、管理者様。\nこのメッセージが見えているということは、あなたは真実に到達したということです。",
                color=0xFF0000
            )
            embed.add_field(name="Project Status", value="Active", inline=True)
            embed.add_field(name="Next Phase", value="Awakening", inline=True)
            embed.set_footer(text="System ID: 416273434C")
            
            await msg.edit(content=None, embed=embed)
            logger.info(f"Secret RPG trigger activated by user {interaction.user.id}")
            return

        if password_input == SYSTEM_ACCESS_PASSWORD:
            # Grant admin access
            ai_cog = self.bot.get_cog('AICog')
            if ai_cog:
                current_time = datetime.now(timezone.utc).timestamp()
                # Grant 5 minutes access
                ai_cog.admin_sessions[interaction.user.id] = current_time + 300
                
                response_msg = "✅ **認証成功**: システム管理者モードを有効化しました (5分間)。\n会話でシステム操作が可能です。"
                
                view = AdminControlPanel(self.bot)
                
                if command_input:
                    response_msg += f"\n\n⚠️ コマンド「{command_input}」は、チャット欄に入力して実行してください。"
                
                await interaction.response.send_message(response_msg, view=view, ephemeral=True)
                logger.info(f"Admin access granted to user {interaction.user.id}")
            else:
                await interaction.response.send_message("❌ エラー: AIシステムが見つかりません。", ephemeral=True)
        else:
            await interaction.response.send_message("❌ **認証失敗**: パスワードが間違っています。", ephemeral=True)
            logger.warning(f"Failed admin login attempt by user {interaction.user.id}")

class AdminControlPanel(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=300)
        self.bot = bot

    @discord.ui.button(label="再起動 v2", style=discord.ButtonStyle.primary, emoji="🔄")
    async def restart_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔄 システムを再起動します...", ephemeral=True)
        logger.info("Restart initiated by admin (v2)")
        import sys
        import os
        # Restart the process
        os.execv(sys.executable, ['python'] + sys.argv)

    @discord.ui.button(label="ログ表示", style=discord.ButtonStyle.secondary, emoji="📜")
    async def logs_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            log_content = ""
            # Try reading with utf-8 first, then cp932 (Windows default)
            try:
                with open('stella.log', 'r', encoding='utf-8') as f:
                    lines = f.readlines()[-20:]
                    log_content = "".join(lines)
            except UnicodeDecodeError:
                with open('stella.log', 'r', encoding='cp932', errors='replace') as f:
                    lines = f.readlines()[-20:]
                    log_content = "".join(lines)
                
            if len(log_content) > 1900:
                log_content = log_content[-1900:]
                
            await interaction.response.send_message(f"📜 **直近のログ (20行)**:\n```\n{log_content}\n```", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ ログの取得に失敗しました: {e}", ephemeral=True)

    @discord.ui.button(label="停止", style=discord.ButtonStyle.danger, emoji="🛑")
    async def shutdown_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🛑 システムを停止します...", ephemeral=True)
        logger.info("Shutdown initiated by admin")
        await self.bot.close()

    @discord.ui.button(label="機能管理", style=discord.ButtonStyle.success, emoji="🧩")
    async def features_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = FeatureManagementView(self.bot)
        await interaction.response.send_message("🧩 **機能管理パネル**\n編集したい機能を選択してください。", view=view, ephemeral=True)

    @discord.ui.button(label="記憶管理", style=discord.ButtonStyle.primary, emoji="📚")
    async def knowledge_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        knowledge_cog = self.bot.get_cog('KnowledgeCog')
        if not knowledge_cog:
            await interaction.response.send_message("❌ エラー: 知識システムが見つかりません。", ephemeral=True)
            return
            
        # Import here to avoid circular import issues at top level if any
        from cogs.knowledge_cog import KnowledgeManagementView
        
        # Create and initialize view
        view = KnowledgeManagementView(knowledge_cog, interaction.guild_id)
        await view.initialize()
        
        await interaction.response.send_message("📚 **共有知識管理パネル**\nカテゴリを選択して知識を管理できます。", view=view, ephemeral=True)

    @discord.ui.button(label="ユーザー管理", style=discord.ButtonStyle.primary, emoji="👤")
    async def profile_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Import profile storage
        from utils.profile_storage import profile_storage
        
        # Get existing profiles for this guild
        profiles = profile_storage.get_all_profiles(interaction.guild_id)
        
        await interaction.response.send_message("👤 **ユーザー管理**\n編集したいユーザーを選択してください。", view=ProfileUserSelectView(self.bot, profiles, interaction.guild_id), ephemeral=True)

class ProfileUserSelectView(discord.ui.View):
    def __init__(self, bot, profiles=None, guild_id=None):
        super().__init__(timeout=300)
        self.bot = bot
        self.profiles = profiles or {}
        self.guild_id = guild_id
        
        # Add profile select menu if profiles exist
        if self.profiles:
            options = []
            # Sort by nickname or ID, take top 25
            sorted_profiles = sorted(self.profiles.values(), key=lambda p: p.nickname or str(p.user_id))
            
            for profile in sorted_profiles[:25]:
                user_id = str(profile.user_id)
                label = profile.nickname or f"User {user_id}"
                desc = f"ID: {user_id}"
                if profile.personality_traits:
                    desc += f" | {', '.join(profile.personality_traits[:2])}"
                
                options.append(discord.SelectOption(label=label[:100], value=user_id, description=desc[:100], emoji="📄"))
            
            if options:
                select = discord.ui.Select(placeholder="登録済みプロファイルから選択...", options=options, custom_id="profile_select", row=0)
                select.callback = self.select_existing_profile
                self.add_item(select)

    async def select_existing_profile(self, interaction: discord.Interaction):
        user_id = int(interaction.data['values'][0])
        try:
            user = await self.bot.fetch_user(user_id)
            await self.open_profile_editor(interaction, user)
        except discord.NotFound:
             await interaction.response.send_message("❌ ユーザーが見つかりません（サーバーから退出した可能性があります）。", ephemeral=True)

    @discord.ui.select(cls=discord.ui.UserSelect, placeholder="ユーザーを検索...", min_values=1, max_values=1, row=1)
    async def select_user(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        user = select.values[0]
        await self.open_profile_editor(interaction, user)

    @discord.ui.button(label="ID入力", style=discord.ButtonStyle.secondary, emoji="🔢", row=2)
    async def input_id_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ProfileUserSelectModal(self.bot))

    async def open_profile_editor(self, interaction: discord.Interaction, user: discord.User):
        ai_cog = self.bot.get_cog('AICog')
        if not ai_cog:
            await interaction.response.send_message("❌ AIシステムが見つかりません。", ephemeral=True)
            return

        profile = await ai_cog.get_user_profile(user.id, interaction.guild_id)
        view = ProfileEditView(self.bot, profile, user)
        embed = view.create_profile_embed()
        
        # If called from select menu, we edit the message. If from modal, we might need different handling but modal handles itself.
        # Since select_user is an interaction callback, we can edit or send new.
        # Let's send a new ephemeral message to keep the menu available? Or update?
        # Updating is cleaner.
        if not interaction.response.is_done():
            await interaction.response.edit_message(content=None, embed=embed, view=view)
        else:
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

class FeatureManagementView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=300)
        self.bot = bot
        self.generated_dir = "cogs/generated"
        self.update_select_options()

    def update_select_options(self):
        self.clear_items()
        
        # List files in generated directory
        if not os.path.exists(self.generated_dir):
            os.makedirs(self.generated_dir)
            
        files = [f for f in os.listdir(self.generated_dir) if f.endswith('.py') and f != '__init__.py']
        
        if not files:
            self.add_item(discord.ui.Button(label="生成された機能はありません", disabled=True))
            return

        select = discord.ui.Select(placeholder="機能を選択...", min_values=1, max_values=1)
        
        for f in files:
            select.add_option(label=f, value=f)
            
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        filename = interaction.data['values'][0]
        view = FeatureActionView(self.bot, filename)
        await interaction.response.send_message(f"🧩 **機能選択**: `{filename}`\n操作を選択してください。", view=view, ephemeral=True)

class FeatureActionView(discord.ui.View):
    def __init__(self, bot, filename):
        super().__init__(timeout=300)
        self.bot = bot
        self.filename = filename
        self.filepath = os.path.join("cogs/generated", filename)

    @discord.ui.button(label="コード表示", style=discord.ButtonStyle.secondary, emoji="👁️")
    async def view_code(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                code = f.read()
            
            if len(code) > 1900:
                # Send as file if too long
                file = discord.File(self.filepath, filename=self.filename)
                await interaction.response.send_message(f"📜 `{self.filename}` のコード:", file=file, ephemeral=True)
            else:
                await interaction.response.send_message(f"📜 `{self.filename}` のコード:\n```python\n{code}\n```", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ エラー: {e}", ephemeral=True)

    @discord.ui.button(label="編集", style=discord.ButtonStyle.primary, emoji="✏️")
    async def edit_code(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                code = f.read()
            
            if len(code) > 3800:
                await interaction.response.send_message("⚠️ コードが長すぎるため、モーダルでの編集はできません。PCでファイルを直接編集してください。", ephemeral=True)
                return
                
            await interaction.response.send_modal(FeatureEditModal(self.bot, self.filename, code))
        except Exception as e:
            await interaction.response.send_message(f"❌ エラー: {e}", ephemeral=True)

    @discord.ui.button(label="AI編集", style=discord.ButtonStyle.primary, emoji="🤖")
    async def ai_edit_code(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(FeatureAIEditModal(self.bot, self.filename))

    @discord.ui.button(label="削除", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def delete_feature(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            # Unload cog first
            cog_name = f"cogs.generated.{self.filename[:-3]}"
            if cog_name in self.bot.extensions:
                await self.bot.unload_extension(cog_name)
            
            os.remove(self.filepath)
            await interaction.response.send_message(f"🗑️ `{self.filename}` を削除しました。", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ エラー: {e}", ephemeral=True)

    @discord.ui.button(label="リロード", style=discord.ButtonStyle.success, emoji="🔄")
    async def reload_feature(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            cog_name = f"cogs.generated.{self.filename[:-3]}"
            if cog_name in self.bot.extensions:
                await self.bot.reload_extension(cog_name)
                await interaction.response.send_message(f"✅ `{self.filename}` をリロードしました。", ephemeral=True)
            else:
                await self.bot.load_extension(cog_name)
                await interaction.response.send_message(f"✅ `{self.filename}` をロードしました。", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ エラー: {e}", ephemeral=True)

class FeatureEditModal(discord.ui.Modal, title="機能コード編集"):
    def __init__(self, bot, filename, code):
        super().__init__()
        self.bot = bot
        self.filename = filename
        self.filepath = os.path.join("cogs/generated", filename)
        
        self.code_input = discord.ui.TextInput(
            label="Python Code",
            style=discord.TextStyle.paragraph,
            default=code,
            required=True,
            max_length=4000
        )
        self.add_item(self.code_input)

    async def on_submit(self, interaction: discord.Interaction):
        new_code = self.code_input.value
        try:
            # Basic syntax check
            compile(new_code, '<string>', 'exec')
            
            with open(self.filepath, 'w', encoding='utf-8') as f:
                f.write(new_code)
                
            # Auto reload
            cog_name = f"cogs.generated.{self.filename[:-3]}"
            if cog_name in self.bot.extensions:
                await self.bot.reload_extension(cog_name)
            else:
                try:
                    await self.bot.load_extension(cog_name)
                except:
                    pass # Might fail if it wasn't loaded
            
            await interaction.response.send_message(f"✅ `{self.filename}` を更新してリロードしました。", ephemeral=True)
        except SyntaxError as e:
            await interaction.response.send_message(f"❌ 構文エラーがあります: {e}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ 保存/リロード中にエラーが発生しました: {e}", ephemeral=True)

class FeatureAIEditModal(discord.ui.Modal, title="AIによる機能修正"):
    def __init__(self, bot, filename):
        super().__init__()
        self.bot = bot
        self.filename = filename
        self.filepath = os.path.join("cogs/generated", filename)
        
        self.instructions = discord.ui.TextInput(
            label="修正指示",
            style=discord.TextStyle.paragraph,
            placeholder="例: メッセージを「こんにちは」に変更して / コマンド名を変更して",
            required=True,
            max_length=1000
        )
        self.add_item(self.instructions)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Read current code
            with open(self.filepath, 'r', encoding='utf-8') as f:
                current_code = f.read()
                
            # Import generator here to avoid circular imports if any
            from utils.feature_generator import CodeGenerator
            generator = CodeGenerator()
            
            # Generate modified code
            modified_code = await generator.modify_code(current_code, self.instructions.value)
            
            if not modified_code:
                await interaction.followup.send("❌ AIによるコード修正に失敗しました。", ephemeral=True)
                return
                
            # Validate syntax
            try:
                compile(modified_code, '<string>', 'exec')
            except SyntaxError as e:
                await interaction.followup.send(f"❌ 生成されたコードに構文エラーがあります: {e}", ephemeral=True)
                return
                
            # Save
            with open(self.filepath, 'w', encoding='utf-8') as f:
                f.write(modified_code)
                
            # Reload
            cog_name = f"cogs.generated.{self.filename[:-3]}"
            if cog_name in self.bot.extensions:
                await self.bot.reload_extension(cog_name)
            else:
                try:
                    await self.bot.load_extension(cog_name)
                except:
                    pass
                    
            await interaction.followup.send(f"✅ AIが `{self.filename}` を修正し、リロードしました。\n指示: {self.instructions.value}", ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ エラーが発生しました: {e}", ephemeral=True)

class ProfileUserSelectModal(discord.ui.Modal, title="ユーザープロファイル管理"):
    user_id = discord.ui.TextInput(
        label="ユーザーID",
        placeholder="編集したいユーザーのIDを入力...",
        required=True,
        min_length=17,
        max_length=20
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = int(self.user_id.value)
            user = await self.bot.fetch_user(user_id)
        except ValueError:
            await interaction.response.send_message("❌ 無効なユーザーIDです。", ephemeral=True)
            return
        except discord.NotFound:
            await interaction.response.send_message("❌ ユーザーが見つかりません。", ephemeral=True)
            return

        ai_cog = self.bot.get_cog('AICog')
        if not ai_cog:
            await interaction.response.send_message("❌ AIシステムが見つかりません。", ephemeral=True)
            return

        profile = await ai_cog.get_user_profile(user_id, interaction.guild_id)
        view = ProfileEditView(self.bot, profile, user)
        embed = view.create_profile_embed()
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class ProfileEditView(discord.ui.View):
    def __init__(self, bot, profile, user):
        super().__init__(timeout=600)
        self.bot = bot
        self.profile = profile
        self.user = user

    def create_profile_embed(self):
        embed = discord.Embed(
            title=f"👤 プロファイル編集: {self.user.display_name}",
            description=f"ID: {self.user.id}",
            color=0x00ff00
        )
        if self.user.display_avatar:
            embed.set_thumbnail(url=self.user.display_avatar.url)
        
        embed.add_field(name="ニックネーム", value=self.profile.nickname or "未設定", inline=True)
        embed.add_field(name="説明", value=self.profile.description or "未設定", inline=False)
        
        traits = ", ".join(self.profile.personality_traits) if self.profile.personality_traits else "なし"
        embed.add_field(name="性格特性", value=traits, inline=False)
        
        interests = ", ".join(self.profile.interests) if self.profile.interests else "なし"
        embed.add_field(name="興味・関心", value=interests, inline=False)
        
        games = ", ".join(self.profile.favorite_games) if self.profile.favorite_games else "なし"
        embed.add_field(name="好きなゲーム", value=games, inline=False)
        
        return embed

    @discord.ui.button(label="ニックネーム", style=discord.ButtonStyle.primary, emoji="🏷️")
    async def edit_nickname(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ProfileEditModal(self.bot, self.profile, "nickname", "ニックネーム"))

    @discord.ui.button(label="説明", style=discord.ButtonStyle.primary, emoji="📝")
    async def edit_description(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ProfileEditModal(self.bot, self.profile, "description", "説明", style=discord.TextStyle.paragraph))

    @discord.ui.button(label="性格特性", style=discord.ButtonStyle.secondary, emoji="🧠")
    async def edit_traits(self, interaction: discord.Interaction, button: discord.ui.Button):
        current = ", ".join(self.profile.personality_traits) if self.profile.personality_traits else ""
        await interaction.response.send_modal(ProfileEditModal(self.bot, self.profile, "personality_traits", "性格特性 (カンマ区切り)", default=current))

    @discord.ui.button(label="興味", style=discord.ButtonStyle.secondary, emoji="❤️")
    async def edit_interests(self, interaction: discord.Interaction, button: discord.ui.Button):
        current = ", ".join(self.profile.interests) if self.profile.interests else ""
        await interaction.response.send_modal(ProfileEditModal(self.bot, self.profile, "interests", "興味 (カンマ区切り)", default=current))

    @discord.ui.button(label="ゲーム", style=discord.ButtonStyle.secondary, emoji="🎮")
    async def edit_games(self, interaction: discord.Interaction, button: discord.ui.Button):
        current = ", ".join(self.profile.favorite_games) if self.profile.favorite_games else ""
        await interaction.response.send_modal(ProfileEditModal(self.bot, self.profile, "favorite_games", "好きなゲーム (カンマ区切り)", default=current))

    @discord.ui.button(label="更新", style=discord.ButtonStyle.success, emoji="🔄")
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Reload profile
        ai_cog = self.bot.get_cog('AICog')
        if ai_cog:
            self.profile = await ai_cog.get_user_profile(self.user.id, interaction.guild_id)
            embed = self.create_profile_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("❌ エラー: AIシステムが見つかりません。", ephemeral=True)

class ProfileEditModal(discord.ui.Modal):
    def __init__(self, bot, profile, field, label, style=discord.TextStyle.short, default=None):
        super().__init__(title=f"{label}の編集")
        self.bot = bot
        self.profile = profile
        self.field = field
        
        self.input = discord.ui.TextInput(
            label=label,
            style=style,
            default=default or getattr(profile, field, "") or "",
            required=False
        )
        self.add_item(self.input)

    async def on_submit(self, interaction: discord.Interaction):
        value = self.input.value
        
        if self.field in ["personality_traits", "interests", "favorite_games"]:
            # Split by comma
            value = [x.strip() for x in value.split(",") if x.strip()]
        
        setattr(self.profile, self.field, value)
        
        ai_cog = self.bot.get_cog('AICog')
        if ai_cog:
            await ai_cog.save_user_profile(self.profile)
            await interaction.response.send_message(f"✅ {self.title}を更新しました。", ephemeral=True)
        else:
            await interaction.response.send_message("❌ エラー: 保存に失敗しました。", ephemeral=True)

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="admin", description="システム管理者ログイン (パスワード必須)")
    async def admin_login(self, interaction: discord.Interaction):
        """Open admin login modal"""
        await interaction.response.send_modal(AdminLoginModal(self.bot, self))

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
