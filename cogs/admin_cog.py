import discord
from discord import app_commands
from discord.ext import commands
import logging
from datetime import datetime, timezone
import os

logger = logging.getLogger(__name__)

# Import for profile injection
import json
from database.models import UserProfile
from utils.profile_storage import profile_storage

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

        # Glitch Mode Activation
        if password_input == "725578":
            if hasattr(self.bot, 'glitch_manager'):
                self.bot.glitch_manager.set_enabled(True)
                await interaction.response.send_message(
                    "⚠️ **SYSTEM FAILURE INITIATED** ⚠️\nGlitch Mode has been ENABLED for all users.\nUse `!repair` to attempt restoration.",
                    ephemeral=True
                )
                logger.warning("Glitch Mode ENABLED by admin")
            else:
                await interaction.response.send_message("❌ Glitch Manager not loaded.", ephemeral=True)
            return

        # Glitch Mode Deactivation
        if password_input == "835682":
            if hasattr(self.bot, 'glitch_manager'):
                self.bot.glitch_manager.set_enabled(False)
                await interaction.response.send_message(
                    "✅ **SYSTEM RESTORED**\nGlitch Mode has been DISABLED.\nAll systems returning to normal parameters.",
                    ephemeral=True
                )
                logger.info("Glitch Mode DISABLED by admin")
            else:
                await interaction.response.send_message("❌ Glitch Manager not loaded.", ephemeral=True)
            return

        # Minecraft Config Access
        if password_input == "minecraft":
            view = MinecraftConfigView(self.bot)
            await interaction.response.send_message("⛏️ **Minecraft 連携設定**\nRCON接続情報を設定してください。", view=view, ephemeral=True)
            return

        # Gacha Management Access
        if password_input == "gacha":
            view = GachaManagementView(self.bot)
            await interaction.response.send_message("🃏 **ガチャ管理パネル**\n操作を選択してください。", view=view, ephemeral=True)
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

    @discord.ui.button(label="ガチャ管理", style=discord.ButtonStyle.success, emoji="🃏")
    async def gacha_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🃏 **ガチャ管理パネル**\n操作を選択してください。", view=GachaManagementView(self.bot), ephemeral=True)

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

    @discord.ui.button(label="JSONインポート", style=discord.ButtonStyle.success, emoji="📥", row=2)
    async def import_json_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "📥 **プロファイルJSONのインポート**\n"
            "適用したいプロファイルJSONファイルを、このチャンネルにアップロード（送信）してください。\n"
            "※ タイムアウト: 60秒",
            ephemeral=True
        )
        
        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id and m.attachments

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=60.0)
            
            # Process the first attachment
            attachment = msg.attachments[0]
            if not attachment.filename.endswith('.json'):
                await interaction.followup.send("❌ エラー: JSONファイルではありません。", ephemeral=True)
                return

            try:
                # Read file content
                file_data = await attachment.read()
                json_data = json.loads(file_data.decode('utf-8'))
                
                # Basic validation
                if 'user_id' not in json_data:
                    await interaction.followup.send("❌ エラー: JSONに `user_id` が含まれていません。", ephemeral=True)
                    return

                user_id = int(json_data['user_id'])
                guild_id = int(json_data.get('guild_id', interaction.guild_id))
                
                # Ensure guild_id matches current guild if not specified or different (optional policy)
                # For now, we trust the JSON or fallback to current guild
                
                # Convert strings back to datetime objects if needed, but UserProfile handles some?
                # Actually UserProfile expects objects, but let's see if we can use the dict directly 
                # or if we need to reconstruct. 
                # profile_storage.load_profile does reconstruction.
                # Let's try to reconstruct manually or use a helper if available.
                # We can use the logic from profile_storage.load_profile but adapted for dict input
                
                # Helper to parse date
                def parse_date(date_str):
                    if not date_str: return None
                    try:
                        return datetime.fromisoformat(date_str)
                    except:
                        return None

                # Create UserProfile object
                # We need to be careful about fields that might be missing in older JSONs
                
                profile = UserProfile(
                    user_id=user_id,
                    guild_id=guild_id,
                    nickname=json_data.get('nickname'),
                    description=json_data.get('description'),
                    personality_traits=json_data.get('personality_traits', []),
                    interests=json_data.get('interests', []),
                    favorite_games=json_data.get('favorite_games', []),
                    memorable_moments=json_data.get('memorable_moments', []),
                    custom_attributes=json_data.get('custom_attributes', {}),
                    conversation_patterns=json_data.get('conversation_patterns', []),
                    emotional_context=json_data.get('emotional_context', {}),
                    interaction_history=json_data.get('interaction_history', []),
                    learned_preferences=json_data.get('learned_preferences', {}),
                    speech_patterns=json_data.get('speech_patterns', {}),
                    reaction_patterns=json_data.get('reaction_patterns', {}),
                    relationship_context=json_data.get('relationship_context', {}),
                    behavioral_traits=json_data.get('behavioral_traits', []),
                    communication_style=json_data.get('communication_style', {}),
                    auto_extracted_info=json_data.get('auto_extracted_info', {}),
                    communication_styles=json_data.get('communication_styles', {}),
                    created_at=parse_date(json_data.get('created_at')) or datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    last_updated=datetime.utcnow()
                )
                
                # Save profile
                if profile_storage.save_profile(profile):
                    await interaction.followup.send(f"✅ ユーザーID `{user_id}` のプロファイルをインポートしました。", ephemeral=True)
                    
                    # Delete the uploaded message to keep channel clean (optional)
                    try:
                        await msg.delete()
                    except:
                        pass
                else:
                    await interaction.followup.send("❌ エラー: プロファイルの保存に失敗しました。", ephemeral=True)

            except json.JSONDecodeError:
                await interaction.followup.send("❌ エラー: JSONファイルの形式が不正です。", ephemeral=True)
            except Exception as e:
                logger.error(f"Profile import error: {e}")
                await interaction.followup.send(f"❌ エラーが発生しました: {e}", ephemeral=True)

        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ タイムアウトしました。もう一度やり直してください。", ephemeral=True)

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

    @discord.ui.button(label="誕生日", style=discord.ButtonStyle.secondary, emoji="🎂")
    async def edit_birthday(self, interaction: discord.Interaction, button: discord.ui.Button):
        birthday_cog = self.bot.get_cog('BirthdayCog')
        if not birthday_cog:
            await interaction.response.send_message("❌ BirthdayCogが見つかりません。", ephemeral=True)
            return
            
        user_id = str(self.user.id)
        current = ""
        if user_id in birthday_cog.birthdays:
            current = birthday_cog.birthdays[user_id]["date"]
            
        await interaction.response.send_modal(BirthdayEditModal(self.bot, self.user, current))

    @discord.ui.button(label="更新", style=discord.ButtonStyle.success, emoji="🔄")
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Reload profile
        ai_cog = self.bot.get_cog('AICog')
        if ai_cog:
            self.profile = await ai_cog.get_user_profile(self.user.id, interaction.guild_id)
            embed = self.create_profile_embed()
            
            # Also update birthday field in embed if we want to show it?
            # The current create_profile_embed doesn't show birthday. 
            # We should probably add it to create_profile_embed too.
            birthday_cog = self.bot.get_cog('BirthdayCog')
            if birthday_cog:
                user_id = str(self.user.id)
                if user_id in birthday_cog.birthdays:
                    bday = birthday_cog.birthdays[user_id]["date"]
                    embed.add_field(name="誕生日", value=bday, inline=True)
            
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("❌ エラー: AIシステムが見つかりません。", ephemeral=True)

class BirthdayEditModal(discord.ui.Modal, title="誕生日編集"):
    def __init__(self, bot, user, current):
        super().__init__()
        self.bot = bot
        self.user = user
        
        self.date_input = discord.ui.TextInput(
            label="誕生日 (YYYY-MM-DD)",
            placeholder="例: 2000-01-01 (削除する場合は 'remove')",
            default=current,
            required=True,
            max_length=20
        )
        self.add_item(self.date_input)

    async def on_submit(self, interaction: discord.Interaction):
        value = self.date_input.value.strip()
        birthday_cog = self.bot.get_cog('BirthdayCog')
        
        if not birthday_cog:
            await interaction.response.send_message("❌ BirthdayCogが見つかりません。", ephemeral=True)
            return

        user_id = str(self.user.id)
        
        if value.lower() == "remove" or value == "":
            if user_id in birthday_cog.birthdays:
                del birthday_cog.birthdays[user_id]
                birthday_cog.save_birthdays()
                await interaction.response.send_message(f"🗑️ {self.user.display_name} の誕生日を削除しました。", ephemeral=True)
            else:
                await interaction.response.send_message("変更ありませんでした。", ephemeral=True)
            return

        try:
            # Validate
            from datetime import datetime
            datetime.strptime(value, "%Y-%m-%d")
            
            birthday_cog.birthdays[user_id] = {
                "date": value,
                "last_celebrated": None
            }
            birthday_cog.save_birthdays()
            await interaction.response.send_message(f"🎂 {self.user.display_name} の誕生日を `{value}` に設定しました。", ephemeral=True)
            
        except ValueError:
            await interaction.response.send_message("❌ 日付形式が正しくありません。YYYY-MM-DD で入力してください。", ephemeral=True)

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

class MinecraftConfigView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=300)
        self.bot = bot
        self.config_file = "data/minecraft_config.json"

    @discord.ui.button(label="接続設定 (RCON)", style=discord.ButtonStyle.primary, emoji="🔌")
    async def config_rcon(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Load current config
        current = {}
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    current = json.load(f)
            except:
                pass
        
        await interaction.response.send_modal(MinecraftConfigModal(self.bot, current))

    @discord.ui.button(label="設定確認", style=discord.ButtonStyle.secondary, emoji="👀")
    async def check_config(self, interaction: discord.Interaction, button: discord.ui.Button):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Mask password
                display_data = data.copy()
                if 'password' in display_data:
                    display_data['password'] = "********"
                
                await interaction.response.send_message(f"⚙️ **現在の設定**:\n```json\n{json.dumps(display_data, indent=2)}\n```", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"❌ 設定読み込みエラー: {e}", ephemeral=True)
        else:
            await interaction.response.send_message("❌ 設定ファイルが存在しません。", ephemeral=True)

class MinecraftConfigModal(discord.ui.Modal, title="Minecraft RCON設定"):
    def __init__(self, bot, current_config):
        super().__init__()
        self.bot = bot
        self.config_file = "data/minecraft_config.json"
        
        self.host = discord.ui.TextInput(
            label="Host (IP)",
            placeholder="localhost",
            default=current_config.get('host', 'localhost'),
            required=True
        )
        self.port = discord.ui.TextInput(
            label="Port (RCON Port)",
            placeholder="25575",
            default=str(current_config.get('port', '25575')),
            required=True
        )
        self.password = discord.ui.TextInput(
            label="Password (RCON)",
            placeholder="password",
            default=current_config.get('password', ''),
            required=True,
            style=discord.TextStyle.short
        )
        
        self.add_item(self.host)
        self.add_item(self.port)
        self.add_item(self.password)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            port_val = int(self.port.value)
        except ValueError:
            await interaction.response.send_message("❌ ポート番号は数字で入力してください。", ephemeral=True)
            return

        data = {
            "host": self.host.value,
            "port": port_val,
            "password": self.password.value
        }
        
        try:
            if not os.path.exists("data"):
                os.makedirs("data")
                
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            # Reload cog to apply changes
            if 'cogs.minecraft_cog' in self.bot.extensions:
                await self.bot.reload_extension('cogs.minecraft_cog')
                
            await interaction.response.send_message("✅ 設定を保存し、Minecraft連携機能をリロードしました。", ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ 保存エラー: {e}", ephemeral=True)

class GachaManagementView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=300)
        self.bot = bot

    async def prompt_user_select(self, interaction: discord.Interaction, mode: str, title: str):
        view = GachaUserSelectView(self.bot, mode)
        await interaction.response.send_message(f"👤 **{title}**\n対象のユーザーを選択してください。", view=view, ephemeral=True)

    @discord.ui.button(label="ポイント付与", style=discord.ButtonStyle.primary, emoji="➕")
    async def add_points(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.prompt_user_select(interaction, "add_points", "ポイント付与")

    @discord.ui.button(label="ポイント設定", style=discord.ButtonStyle.secondary, emoji="✏️")
    async def set_points(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.prompt_user_select(interaction, "set_points", "ポイント設定")

    @discord.ui.button(label="ユーザー確認", style=discord.ButtonStyle.success, emoji="👀")
    async def check_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.prompt_user_select(interaction, "check", "ユーザー情報確認")

    @discord.ui.button(label="カード操作", style=discord.ButtonStyle.danger, emoji="🃏")
    async def manage_cards(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.prompt_user_select(interaction, "manage_cards", "カードインベントリ操作")

class GachaUserSelectView(discord.ui.View):
    def __init__(self, bot, mode):
        super().__init__(timeout=60)
        self.bot = bot
        self.mode = mode
        
        self.select = discord.ui.UserSelect(placeholder="ユーザーを選択...", min_values=1, max_values=1)
        self.select.callback = self.callback
        self.add_item(self.select)

    async def callback(self, interaction: discord.Interaction):
        user = self.select.values[0]
        
        if self.mode == "check":
            gacha_cog = self.bot.get_cog('GachaCog')
            if not gacha_cog:
                await interaction.response.send_message("❌ GachaCogが見つかりません。", ephemeral=True)
                return
            
            try:
                data = gacha_cog.get_player_data(user.id)
                embed = discord.Embed(title=f"🃏 Gacha Data: {user.display_name}", color=discord.Color.blue())
                embed.set_thumbnail(url=user.display_avatar.url)
                embed.add_field(name="Points", value=f"{data['points']} SP", inline=True)
                embed.add_field(name="Cards", value=f"{data['card_count']} 枚", inline=True)
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"❌ エラー: {e}", ephemeral=True)
                
        elif self.mode == "add_points":
            await interaction.response.send_modal(GachaPointModal(self.bot, "add", user))
            
        elif self.mode == "set_points":
            await interaction.response.send_modal(GachaPointModal(self.bot, "set", user))
            
        elif self.mode == "manage_cards":
            await interaction.response.send_modal(GachaInventoryModal(self.bot, user))

class GachaInventoryModal(discord.ui.Modal, title="カードインベントリ操作"):
    action = discord.ui.TextInput(label="操作 (grant/clear)", placeholder="grant [枚数] / clear", required=True)

    def __init__(self, bot, user):
        super().__init__()
        self.bot = bot
        self.user = user

    async def on_submit(self, interaction: discord.Interaction):
        gacha_cog = self.bot.get_cog('GachaCog')
        if not gacha_cog:
            await interaction.response.send_message("❌ GachaCogが見つかりません。", ephemeral=True)
            return
            
        try:
            act_str = self.action.value.lower().strip()
            
            if act_str == "clear":
                gacha_cog.clear_inventory(self.user.id)
                await interaction.response.send_message(f"🗑️ {self.user.display_name} のインベントリを全消去しました。", ephemeral=True)
            
            elif act_str.startswith("grant"):
                try:
                    count = int(act_str.split()[1])
                except:
                    count = 1
                
                added = gacha_cog.grant_cards(self.user.id, count)
                await interaction.response.send_message(f"🎁 {self.user.display_name} に {added} 枚のカードを付与しました。", ephemeral=True)
            
            else:
                await interaction.response.send_message("❌ 操作は 'grant [枚数]' または 'clear' で指定してください。", ephemeral=True)
                
        except Exception as e:
            await interaction.response.send_message(f"❌ エラー: {e}", ephemeral=True)

class GachaPointModal(discord.ui.Modal):
    def __init__(self, bot, mode, user):
        super().__init__(title="ガチャポイント管理")
        self.bot = bot
        self.mode = mode
        self.user = user
        
        self.amount = discord.ui.TextInput(
            label="ポイント数",
            placeholder="例: 1000",
            required=True
        )
        self.add_item(self.amount)

    async def on_submit(self, interaction: discord.Interaction):
        gacha_cog = self.bot.get_cog('GachaCog')
        if not gacha_cog:
            await interaction.response.send_message("❌ GachaCogが見つかりません。", ephemeral=True)
            return

        try:
            amount = int(self.amount.value)
            
            if self.mode == "add":
                new_val = gacha_cog.add_points(self.user.id, amount)
                await interaction.response.send_message(f"✅ {self.user.display_name} に {amount} SP を付与しました。(合計: {new_val} SP)", ephemeral=True)
            elif self.mode == "set":
                new_val = gacha_cog.set_points(self.user.id, amount)
                await interaction.response.send_message(f"✅ {self.user.display_name} のポイントを {amount} SP に設定しました。", ephemeral=True)
                
        except ValueError:
            await interaction.response.send_message("❌ 数値を入力してください。", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ エラー: {e}", ephemeral=True)

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="admin", description="システム管理者ログイン (パスワード必須)")
    async def admin_login(self, interaction: discord.Interaction):
        """Open admin login modal"""
        await interaction.response.send_modal(AdminLoginModal(self.bot, self))

    @commands.command(name="sync")
    @commands.is_owner()
    async def sync_commands(self, ctx):
        """Force sync slash commands"""
        msg = await ctx.send("🔄 Syncing commands...")
        try:
            # Sync global
            self.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await self.bot.tree.sync(guild=ctx.guild)
            await msg.edit(content=f"✅ Synced {len(synced)} commands to this guild.")
        except Exception as e:
            await msg.edit(content=f"❌ Sync failed: {e}")

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
