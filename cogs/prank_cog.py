import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import random
import logging
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)

DATA_FILE = "data/mind_control.json"
IMPERSONATE_LOG_FILE = "data/impersonate_logs.json"

class PrankCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mimic_targets = set()
        self.roulette_targets = set()
        self.typing_tasks = {}
        self.possession_map = {} # {user_id: channel_id}
        self.shadow_clone_targets = set()
        self.mind_control_targets = {} # {user_id: {from: to}}
        self.load_data()

    def load_data(self):
        """Load mind control data from file"""
        if not os.path.exists("data"):
            os.makedirs("data")
        
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Convert keys (user_id) back to int
                    self.mind_control_targets = {int(k): v for k, v in data.items()}
            except Exception as e:
                logger.error(f"Failed to load mind control data: {e}")
                self.mind_control_targets = {}
        else:
            self.mind_control_targets = {}

    def save_data(self):
        """Save mind control data to file"""
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.mind_control_targets, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save mind control data: {e}")

    def _log_impersonation(self, executor, target, message, channel_id):
        """Log impersonation usage"""
        executor_id = executor.id if executor else 0
        executor_name = executor.display_name if executor else "Unknown"
        target_name = target.display_name if target else "Unknown"

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "executor_id": executor_id,
            "executor_name": executor_name,
            "target_name": target_name,
            "message": message,
            "channel_id": channel_id
        }
        
        logs = []
        if os.path.exists(IMPERSONATE_LOG_FILE):
            try:
                with open(IMPERSONATE_LOG_FILE, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            except: pass
            
        logs.append(log_entry)
        # Keep last 100 logs
        logs = logs[-100:]
        
        try:
            with open(IMPERSONATE_LOG_FILE, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save impersonation log: {e}")

    # Define Groups
    prank_group = app_commands.Group(name="prank", description="[いたずら] いたずらコマンドセット")
    
    mimic_group = app_commands.Group(name="mimic", description="真似っこ機能", parent=prank_group)
    roulette_group = app_commands.Group(name="roulette", description="リアクションルーレット", parent=prank_group)
    typing_group = app_commands.Group(name="typing", description="無限入力中", parent=prank_group)
    possess_group = app_commands.Group(name="possess", description="憑依モード", parent=prank_group)
    shadow_group = app_commands.Group(name="shadow_clone", description="影分身", parent=prank_group)
    mind_group = app_commands.Group(name="mind_control", description="マインドコントロール")
    identity_group = app_commands.Group(name="identity", description="なりすまし・変身", parent=prank_group)

    # --- Mimic Group ---
    @mimic_group.command(name="start", description="指定したユーザーの真似（オウム返し）をします")
    @app_commands.describe(user="ターゲット")
    @app_commands.default_permissions(administrator=True)
    async def mimic_start(self, interaction: discord.Interaction, user: discord.User):
        if user.id in self.mimic_targets:
            await interaction.response.send_message(f"⚠️ 既に {user.display_name} の真似をしています。", ephemeral=True)
        else:
            self.mimic_targets.add(user.id)
            await interaction.response.send_message(f"😈 {user.display_name} の真似を始めます。", ephemeral=True)

    @mimic_group.command(name="stop", description="オウム返しを停止します")
    @app_commands.default_permissions(administrator=True)
    async def mimic_stop(self, interaction: discord.Interaction):
        self.mimic_targets.clear()
        await interaction.response.send_message("✅ 全てのオウム返しを停止しました。", ephemeral=True)

    # --- Roulette Group ---
    @roulette_group.command(name="start", description="指定したユーザーにランダムなリアクションをつけまくります")
    @app_commands.describe(user="ターゲット")
    @app_commands.default_permissions(administrator=True)
    async def roulette_start(self, interaction: discord.Interaction, user: discord.User):
        if user.id in self.roulette_targets:
            await interaction.response.send_message(f"⚠️ 既に {user.display_name} をターゲットにしています。", ephemeral=True)
        else:
            self.roulette_targets.add(user.id)
            await interaction.response.send_message(f"😈 {user.display_name} へのリアクション攻撃を始めます。", ephemeral=True)

    @roulette_group.command(name="stop", description="リアクション攻撃を停止します")
    @app_commands.default_permissions(administrator=True)
    async def roulette_stop(self, interaction: discord.Interaction):
        self.roulette_targets.clear()
        await interaction.response.send_message("✅ 全てのリアクション攻撃を停止しました。", ephemeral=True)

    # --- Typing Group ---
    @typing_group.command(name="start", description="無限に入力中表示を出します")
    @app_commands.default_permissions(administrator=True)
    async def typing_start(self, interaction: discord.Interaction):
        channel_id = interaction.channel_id
        if channel_id in self.typing_tasks:
            await interaction.response.send_message("⚠️ 既に実行中です。", ephemeral=True)
        else:
            async def manual_typing_loop():
                try:
                    while True:
                        await interaction.channel.trigger_typing()
                        await asyncio.sleep(8)
                except asyncio.CancelledError:
                    pass

            task = asyncio.create_task(manual_typing_loop())
            self.typing_tasks[channel_id] = task
            await interaction.response.send_message("😈 このチャンネルで無限入力中表示を始めました。", ephemeral=True)

    @typing_group.command(name="stop", description="入力中表示を停止します")
    @app_commands.default_permissions(administrator=True)
    async def typing_stop(self, interaction: discord.Interaction):
        channel_id = interaction.channel_id
        if channel_id in self.typing_tasks:
            task = self.typing_tasks.pop(channel_id)
            task.cancel()
            await interaction.response.send_message("✅ 入力中表示を停止しました。", ephemeral=True)
        else:
            await interaction.response.send_message("❌ このチャンネルでは実行されていません。", ephemeral=True)

    # --- Possession Group ---
    @possess_group.command(name="start", description="憑依モード：DMで送った内容をBotがこのチャンネルで話します")
    @app_commands.default_permissions(administrator=True)
    async def possess_start(self, interaction: discord.Interaction):
        self.possession_map[interaction.user.id] = interaction.channel_id
        await interaction.response.send_message(
            "👻 **憑依完了**\n"
            "私にDMを送ると、このチャンネルで私が喋ったことになります。\n"
            "解除するには `/prank possess stop` を実行してください。",
            ephemeral=True
        )

    @possess_group.command(name="stop", description="憑依モードを解除します")
    @app_commands.default_permissions(administrator=True)
    async def possess_stop(self, interaction: discord.Interaction):
        if interaction.user.id in self.possession_map:
            del self.possession_map[interaction.user.id]
            await interaction.response.send_message("👻 憑依を解除しました。", ephemeral=True)
        else:
            await interaction.response.send_message("❌ 憑依していません。", ephemeral=True)

    # --- Shadow Clone Group ---
    @shadow_group.command(name="start", description="影分身：指定したユーザーが喋ると分身が現れます")
    @app_commands.default_permissions(administrator=True)
    async def shadow_start(self, interaction: discord.Interaction, user: discord.User):
        if user.id in self.shadow_clone_targets:
            self.shadow_clone_targets.remove(user.id)
            await interaction.response.send_message(f"✅ {user.display_name} の影分身を解除しました。", ephemeral=True)
        else:
            self.shadow_clone_targets.add(user.id)
            await interaction.response.send_message(f"🥷 {user.display_name} に影分身を憑けました。", ephemeral=True)

    @shadow_group.command(name="stop", description="全ての影分身を解除します")
    @app_commands.default_permissions(administrator=True)
    async def shadow_stop(self, interaction: discord.Interaction):
        self.shadow_clone_targets.clear()
        await interaction.response.send_message("✅ 全ての影分身を解除しました。", ephemeral=True)

    # --- Mind Control Group ---
    @mind_group.command(name="add", description="マインドコントロール：発言を勝手に書き換えます")
    @app_commands.describe(user="ターゲット", word_from="言った言葉", word_to="書き換える言葉")
    @app_commands.default_permissions(administrator=True)
    async def mind_add(self, interaction: discord.Interaction, user: discord.User, word_from: str, word_to: str):
        if user.id not in self.mind_control_targets:
            self.mind_control_targets[user.id] = {}
        self.mind_control_targets[user.id][word_from] = word_to
        self.save_data()
        await interaction.response.send_message(f"🧠 {user.display_name} の「{word_from}」を「{word_to}」に書き換えます。", ephemeral=True)

    @mind_group.command(name="clear", description="マインドコントロールを全て解除します")
    @app_commands.default_permissions(administrator=True)
    async def mind_clear(self, interaction: discord.Interaction):
        self.mind_control_targets.clear()
        self.save_data()
        await interaction.response.send_message("✅ 全てのマインドコントロールを解除しました。", ephemeral=True)

    @mind_group.command(name="list", description="現在のマインドコントロール設定を確認します")
    @app_commands.default_permissions(administrator=True)
    async def mind_list(self, interaction: discord.Interaction):
        if not self.mind_control_targets:
            await interaction.response.send_message("🧠 現在有効なマインドコントロールはありません。", ephemeral=True)
            return

        embed = discord.Embed(title="🧠 マインドコントロール一覧", color=discord.Color.dark_purple())
        for user_id, rules in self.mind_control_targets.items():
            user = self.bot.get_user(user_id)
            name = user.display_name if user else f"Unknown ({user_id})"
            rules_str = "\n".join([f"「{k}」→「{v}」" for k, v in rules.items()])
            embed.add_field(name=name, value=rules_str, inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @mind_group.command(name="remove", description="特定の言葉のマインドコントロールを解除します")
    @app_commands.describe(user="ターゲット", word_from="解除する言葉")
    @app_commands.default_permissions(administrator=True)
    async def mind_remove(self, interaction: discord.Interaction, user: discord.User, word_from: str):
        if user.id in self.mind_control_targets and word_from in self.mind_control_targets[user.id]:
            del self.mind_control_targets[user.id][word_from]
            if not self.mind_control_targets[user.id]:
                del self.mind_control_targets[user.id]
            self.save_data()
            await interaction.response.send_message(f"✅ {user.display_name} の「{word_from}」の書き換えを解除しました。", ephemeral=True)
        else:
            await interaction.response.send_message("❌ その設定は見つかりませんでした。", ephemeral=True)

    # --- Identity Group ---
    @identity_group.command(name="copy", description="指定したユーザーのニックネームをコピーします")
    @app_commands.describe(user="コピーするユーザー")
    @app_commands.default_permissions(administrator=True)
    async def identity_copy(self, interaction: discord.Interaction, user: discord.User):
        try:
            await interaction.guild.me.edit(nick=user.display_name)
            await interaction.response.send_message(f"🪞 {user.display_name} に変身しました。", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ ニックネームを変更する権限がありません。", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ エラー: {e}", ephemeral=True)

    @identity_group.command(name="reset", description="変身を解除します")
    @app_commands.default_permissions(administrator=True)
    async def identity_reset(self, interaction: discord.Interaction):
        try:
            await interaction.guild.me.edit(nick=None)
            await interaction.response.send_message("✨ 元の姿に戻りました。", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ エラー: {e}", ephemeral=True)

    @identity_group.command(name="steal", description="サーバー内の誰かランダムな一人に変身します")
    @app_commands.default_permissions(administrator=True)
    async def identity_steal(self, interaction: discord.Interaction):
        members = [m for m in interaction.guild.members if not m.bot]
        if not members:
            await interaction.response.send_message("❌ ターゲットがいません。", ephemeral=True)
            return
        
        target = random.choice(members)
        try:
            await interaction.guild.me.edit(nick=target.display_name)
            await interaction.response.send_message(f"🕵️ {target.display_name} のIDを盗みました。", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ エラー: {e}", ephemeral=True)

    # --- Other Pranks (Direct under /prank) ---
    @app_commands.command(name="impersonate", description="指定したユーザーになりすまして発言します")
    @app_commands.describe(user="なりすますユーザー", message="発言させる内容")
    @app_commands.default_permissions(administrator=True)
    async def impersonate(self, interaction: discord.Interaction, user: discord.User, message: str):
        await interaction.response.defer(ephemeral=True)
        try:
            channel = interaction.channel
            thread = None
            if isinstance(channel, (discord.Thread, discord.abc.GuildChannel)) and hasattr(channel, 'parent') and isinstance(channel, discord.Thread):
                thread = channel
                channel = channel.parent
            
            webhook = await channel.create_webhook(name=user.display_name)
            kwargs = {
                "content": message,
                "username": user.display_name,
                "avatar_url": user.display_avatar.url,
                "wait": True
            }
            if thread:
                kwargs["thread"] = thread
            
            await webhook.send(**kwargs)
            await webhook.delete()
            
            # Log the usage
            self._log_impersonation(interaction.user, user, message, interaction.channel_id)
            
            await interaction.followup.send(f"✅ {user.display_name} になりすましました。", ephemeral=True)
        except Exception as e:
            import traceback
            logger.error(f"Impersonate error: {traceback.format_exc()}")
            await interaction.followup.send(f"❌ エラー: {e}", ephemeral=True)

    @prank_group.command(name="fake_error", description="偽のエラーメッセージを表示します")
    @app_commands.default_permissions(administrator=True)
    async def fake_error(self, interaction: discord.Interaction):
        await interaction.response.send_message("⚠️ **CRITICAL SYSTEM FAILURE** ⚠️\nInitiating emergency shutdown sequence...", ephemeral=False)
        msg = await interaction.original_response()
        await asyncio.sleep(2)
        await msg.edit(content="⚠️ **CRITICAL SYSTEM FAILURE** ⚠️\nInitiating emergency shutdown sequence...\n> Deleting database... [||██████████||] 100%")
        await asyncio.sleep(2)
        await msg.edit(content="⚠️ **CRITICAL SYSTEM FAILURE** ⚠️\nInitiating emergency shutdown sequence...\n> Deleting database... [||██████████||] 100%\n> Purging user data... [||███████---||] 70%")
        await asyncio.sleep(2)
        await msg.edit(content="⚠️ **CRITICAL SYSTEM FAILURE** ⚠️\nInitiating emergency shutdown sequence...\n> Deleting database... [||██████████||] 100%\n> Purging user data... [||██████████||] 100%\n> **SYSTEM DESTROYED.**")
        await asyncio.sleep(3)
        await msg.edit(content="...なーんちゃって！😜\nただのいたずらです。システムは正常です。")

    @prank_group.command(name="ghost_ping", description="ゴーストメンション（通知だけ飛ばして消す）を送ります")
    @app_commands.describe(user="ターゲット")
    @app_commands.default_permissions(administrator=True)
    async def ghost_ping(self, interaction: discord.Interaction, user: discord.User):
        await interaction.response.send_message("👻 ゴーストメンションを実行します...", ephemeral=True)
        msg = await interaction.channel.send(f"{user.mention}")
        await msg.delete()

    @prank_group.command(name="fake_nitro", description="偽のNitroギフトリンクを送信します")
    @app_commands.default_permissions(administrator=True)
    async def fake_nitro(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎁 A wild gift appears!",
            description="**Nitro**\n[Accept](https://www.youtube.com/watch?v=dQw4w9WgXcQ)",
            color=0x5865F2
        )
        embed.set_thumbnail(url="https://i.imgur.com/4M34hi2.png")
        await interaction.channel.send(embed=embed)
        await interaction.response.send_message("😈 偽Nitroを送りました。", ephemeral=True)

    @prank_group.command(name="audit_impersonate", description="[Admin] なりすましコマンドの使用履歴を確認します")
    @app_commands.default_permissions(administrator=True)
    async def audit_impersonate(self, interaction: discord.Interaction, limit: int = 10):
        if not os.path.exists(IMPERSONATE_LOG_FILE):
            await interaction.response.send_message("📭 履歴はありません。", ephemeral=True)
            return

        try:
            with open(IMPERSONATE_LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except:
            await interaction.response.send_message("❌ ログの読み込みに失敗しました。", ephemeral=True)
            return

        if not logs:
            await interaction.response.send_message("📭 履歴はありません。", ephemeral=True)
            return

        logs = logs[-limit:]
        logs.reverse() # Newest first

        embed = discord.Embed(title="🕵️ なりすまし使用履歴", color=discord.Color.red())
        
        for entry in logs:
            dt = datetime.fromisoformat(entry["timestamp"])
            time_str = dt.strftime("%Y/%m/%d %H:%M")
            
            embed.add_field(
                name=f"{time_str} - {entry['executor_name']}",
                value=f"Target: **{entry['target_name']}**\nMsg: `{entry['message']}`",
                inline=False
            )
            
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @prank_group.command(name="puppet", description="パペッティア：指定したユーザーに強制的に喋らせます")
    @app_commands.describe(user="操るユーザー", message="言わせる言葉")
    @app_commands.default_permissions(administrator=True)
    async def puppet(self, interaction: discord.Interaction, user: discord.User, message: str):
        await interaction.response.defer(ephemeral=True)
        try:
            channel = interaction.channel
            thread = None
            if isinstance(channel, (discord.Thread, discord.abc.GuildChannel)) and hasattr(channel, 'parent') and isinstance(channel, discord.Thread):
                thread = channel
                channel = channel.parent

            webhook = await channel.create_webhook(name=user.display_name)
            await webhook.send(
                content=message,
                username=user.display_name,
                avatar_url=user.display_avatar.url,
                wait=True,
                thread=thread
            )
            await webhook.delete()
            await interaction.followup.send(f"😈 {user.display_name} を操りました。", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ エラー: {e}", ephemeral=True)

    @prank_group.command(name="ghost_whisper", description="VCに誰もいないのにささやき声を流します")
    @app_commands.describe(message="ささやく内容", channel="ターゲットVC")
    @app_commands.default_permissions(administrator=True)
    async def ghost_whisper(self, interaction: discord.Interaction, message: str, channel: discord.VoiceChannel):
        await interaction.response.defer(ephemeral=True)
        try:
            vc = await channel.connect()
            from gtts import gTTS
            import io
            tts = gTTS(text=message, lang='ja', slow=True)
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            source = discord.FFmpegPCMAudio(fp, pipe=True)
            vc.play(source)
            while vc.is_playing():
                await asyncio.sleep(1)
            await vc.disconnect()
            await interaction.followup.send("👻 ささやき声を届けました...", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ エラー: {e}", ephemeral=True)
            if 'vc' in locals() and vc.is_connected():
                await vc.disconnect()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Mind Control logic
        if message.author.id in self.mind_control_targets:
            replacements = self.mind_control_targets[message.author.id]
            content = message.content
            triggered = False
            for k, v in replacements.items():
                if k in content:
                    content = content.replace(k, v)
                    triggered = True
            
            if triggered:
                try:
                    await message.delete()
                    
                    channel = message.channel
                    thread = None
                    if isinstance(channel, (discord.Thread, discord.abc.GuildChannel)) and hasattr(channel, 'parent') and isinstance(channel, discord.Thread):
                        thread = channel
                        channel = channel.parent

                    webhook = await channel.create_webhook(name=message.author.display_name)
                    kwargs = {
                        "content": content,
                        "username": message.author.display_name,
                        "avatar_url": message.author.display_avatar.url,
                        "wait": True
                    }
                    if thread:
                        kwargs["thread"] = thread
                    
                    await webhook.send(**kwargs)
                    await webhook.delete()
                    return # Stop processing other pranks for this message
                except Exception as e:
                    logger.error(f"Mind control error: {e}")

        # Shadow Clone logic
        if message.author.id in self.shadow_clone_targets:
            try:
                channel = message.channel
                thread = None
                if isinstance(channel, (discord.Thread, discord.abc.GuildChannel)) and hasattr(channel, 'parent') and isinstance(channel, discord.Thread):
                    thread = channel
                    channel = channel.parent

                webhook = await channel.create_webhook(name=message.author.display_name)
                kwargs = {
                    "content": message.content,
                    "username": message.author.display_name,
                    "avatar_url": message.author.display_avatar.url,
                    "wait": True
                }
                if thread:
                    kwargs["thread"] = thread
                
                await webhook.send(**kwargs)
                await webhook.delete()
            except Exception as e:
                logger.error(f"Shadow clone error: {e}")

        # Possession logic (DM -> Channel)
        if isinstance(message.channel, discord.DMChannel):
            if message.author.id in self.possession_map:
                target_channel_id = self.possession_map[message.author.id]
                target_channel = self.bot.get_channel(target_channel_id)
                if target_channel:
                    try:
                        await target_channel.send(message.content)
                        await message.add_reaction("✅")
                    except Exception as e:
                        await message.channel.send(f"❌ 送信エラー: {e}")
                else:
                    await message.channel.send("❌ 対象チャンネルが見つかりません。")
                return

        # Mimic logic
        if message.author.id in self.mimic_targets:
            try:
                await message.channel.send(message.content)
            except:
                pass

        # React Roulette logic
        if message.author.id in self.roulette_targets:
            try:
                emojis = ["😀", "😂", "🥰", "😎", "🤔", "😱", "💩", "🤡", "👻", "👽", "🤖", "🎃", "👍", "👎", "👀", "🔥", "💯", "🍆", "🍑"]
                chosen = random.sample(emojis, 3)
                for emoji in chosen:
                    await message.add_reaction(emoji)
            except:
                pass

    @app_commands.command(name="hasegawa", description="長谷川を召喚します")
    async def hasegawa(self, interaction: discord.Interaction):
        if not interaction.user.voice:
            await interaction.response.send_message("❌ ボイスチャンネルに参加してください！", ephemeral=True)
            return

        channel = interaction.user.voice.channel
        vc = interaction.guild.voice_client

        if not vc:
            try:
                vc = await channel.connect()
            except Exception as e:
                await interaction.response.send_message(f"❌ 接続エラー: {e}", ephemeral=True)
                return
        
        # Hikakin4ne ID: 1100715717038460979
        sound_id = 1100715717038460979
        
        try:
            # Fetch sound
            sound = None
            sounds = await interaction.guild.fetch_soundboard_sounds()
            for s in sounds:
                if s.id == sound_id:
                    sound = s
                    break
            
            if not sound:
                await interaction.response.send_message("❌ サウンド「Hikakin4ne」が見つかりませんでした。", ephemeral=True)
                # If we just connected, disconnect
                if vc and not vc.is_playing(): 
                     await vc.disconnect()
                return

            await interaction.response.send_message("ヒカキン４ねよ雑魚")
            
            # Play sound
            vc.play(discord.FFmpegPCMAudio(sound.url))
            
            # Wait a bit and disconnect if we connected just for this
            # Assuming we want to leave after playing
            await asyncio.sleep(5)
            if vc.is_connected():
                await vc.disconnect()
            
        except Exception as e:
            await interaction.followup.send(f"❌ エラー: {e}", ephemeral=True)
            if vc and vc.is_connected():
                await vc.disconnect()

async def setup(bot):
    await bot.add_cog(PrankCog(bot))
