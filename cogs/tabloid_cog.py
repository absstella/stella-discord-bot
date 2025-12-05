import discord
from discord.ext import commands
from discord import app_commands
import logging
from datetime import datetime, timedelta
import random
import asyncio
import io
import json
import os

logger = logging.getLogger(__name__)

DATA_FILE = "data/tabloids.json"

class TabloidView(discord.ui.View):
    def __init__(self, pages=None, timeout=None):
        super().__init__(timeout=timeout)
        self.pages = pages or []
        self.current_page = 0
        self.message = None
        self.update_buttons()

    def update_buttons(self):
        # If pages are not loaded yet (persistent view case), we can't determine disabled state accurately
        # But usually we load data before calling this in the callback
        if not self.pages:
            self.prev_button.disabled = True
            self.next_button.disabled = True
            self.page_counter.label = "?/?"
        else:
            self.prev_button.disabled = (self.current_page == 0)
            self.next_button.disabled = (self.current_page == len(self.pages) - 1)
            self.page_counter.label = f"{self.current_page + 1}/{len(self.pages)}"

    async def load_data(self, interaction: discord.Interaction):
        """Load pages from file if missing"""
        if self.pages:
            return True

        try:
            if not os.path.exists(DATA_FILE):
                return False
            
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            msg_id = str(interaction.message.id)
            if msg_id in data:
                raw_pages = data[msg_id]
                self.pages = []
                for p in raw_pages:
                    embed = discord.Embed.from_dict(p)
                    self.pages.append(embed)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to load tabloid data: {e}")
            return False

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.primary, custom_id="tabloid_prev")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.pages:
            success = await self.load_data(interaction)
            if not success:
                await interaction.response.send_message("❌ データの読み込みに失敗しました（有効期限切れの可能性があります）。", ephemeral=True)
                return
        
        # Determine current page from footer if possible, or just decrement internal state
        # Since we just loaded or have state, internal state should be 0 if just loaded.
        # But if we are persistent, we might be on page 2.
        # We can try to parse the footer "X/Y" from the message embed
        try:
            if interaction.message.embeds:
                footer_text = interaction.message.components[0].children[1].label # "1/4"
                if footer_text and "/" in footer_text:
                    current_str = footer_text.split("/")[0]
                    self.current_page = int(current_str) - 1
        except:
            pass

        self.current_page = max(0, self.current_page - 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @discord.ui.button(label="1/1", style=discord.ButtonStyle.secondary, disabled=True, custom_id="tabloid_counter")
    async def page_counter(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.primary, custom_id="tabloid_next")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.pages:
            success = await self.load_data(interaction)
            if not success:
                await interaction.response.send_message("❌ データの読み込みに失敗しました（有効期限切れの可能性があります）。", ephemeral=True)
                return

        try:
            if interaction.message.embeds:
                footer_text = interaction.message.components[0].children[1].label # "1/4"
                if footer_text and "/" in footer_text:
                    current_str = footer_text.split("/")[0]
                    self.current_page = int(current_str) - 1
        except:
            pass

        self.current_page = min(len(self.pages) - 1, self.current_page + 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

class TabloidCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ai_cog = None
        self.image_gen_cog = None
        self.ensure_data_file()

    def ensure_data_file(self):
        if not os.path.exists("data"):
            os.makedirs("data")
        if not os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump({}, f)

    def save_tabloid(self, message_id, pages):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert embeds to dicts
            pages_data = [p.to_dict() for p in pages]
            data[str(message_id)] = pages_data
            
            # Optional: Cleanup old entries (keep last 50?)
            if len(data) > 50:
                # Remove oldest
                keys = list(data.keys())
                for k in keys[:-50]:
                    del data[k]

            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save tabloid data: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        self.ai_cog = self.bot.get_cog('AICog')
        self.image_gen_cog = self.bot.get_cog('ImageGenCog')
        # Register persistent view
        self.bot.add_view(TabloidView())

    async def upload_image(self, interaction, file_bytes, filename):
        """Upload image to storage channel and return URL"""
        guild = interaction.guild
        if not guild:
            return None

        channel_name = "stella-image-storage"
        channel = discord.utils.get(guild.text_channels, name=channel_name)
        
        if not channel:
            try:
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                }
                channel = await guild.create_text_channel(channel_name, overwrites=overwrites)
            except Exception as e:
                logger.warning(f"Failed to create storage channel: {e}")
                return None
        
        try:
            # Create a new file object for upload
            file = discord.File(io.BytesIO(file_bytes), filename=filename)
            msg = await channel.send(file=file)
            return msg.attachments[0].url
        except Exception as e:
            logger.error(f"Failed to upload image: {e}")
            return None

    @app_commands.command(name="scoop", description="[週刊誌] サーバーのスクープ記事を生成します")
    @app_commands.describe(
        style="記事のスタイル（スポーツ紙/週刊誌/経済新聞）",
        target="ターゲットにするユーザー",
        interview="捏造インタビューするユーザー"
    )
    @app_commands.choices(style=[
        app_commands.Choice(name="スポーツ紙（派手・煽り）", value="sports"),
        app_commands.Choice(name="週刊誌（暴露・スキャンダル）", value="weekly"),
        app_commands.Choice(name="経済新聞（真面目・分析）", value="business")
    ])
    async def scoop(self, interaction: discord.Interaction, style: str = "weekly", target: discord.Member = None, interview: discord.Member = None):
        """Generate a tabloid scoop from recent chat"""
        await interaction.response.defer()
        
        if not self.ai_cog:
            self.ai_cog = self.bot.get_cog('AICog')
        if not self.image_gen_cog:
            self.image_gen_cog = self.bot.get_cog('ImageGenCog')
            
        if not self.ai_cog or not self.ai_cog.model:
            await interaction.followup.send("❌ AI機能が利用できないため、記事を生成できません。")
            return

        # Fetch recent messages
        messages = []
        try:
            async for msg in interaction.channel.history(limit=50):
                if not msg.author.bot and msg.content:
                    messages.append(f"{msg.author.display_name}: {msg.content}")
        except Exception as e:
            await interaction.followup.send(f"❌ メッセージの取得に失敗しました: {e}")
            return
            
        if not messages:
            await interaction.followup.send("❌ 記事にするメッセージが見つかりませんでした。")
            return
            
        chat_log = "\n".join(messages)
        
        # Determine Target Context
        target_context = ""
        if target:
            target_context = f"ターゲット: {target.display_name}氏を中心に記事を構成してください。"
        
        interview_context = ""
        if interview:
            interview_context = f"インタビュー対象: {interview.display_name}氏への架空のインタビューを含めてください。"

        style_instructions = {
            "sports": "スポーツ新聞風。派手な見出し、感嘆符多用、勢い重視。",
            "weekly": "週刊誌風。スキャンダラス、暴露、煽り、ゴシップ調。",
            "business": "経済新聞風。真面目な文体だが内容はくだらない、分析的、グラフ言及など。"
        }
        
        prompt = f"""
        あなたは「週刊STELLA」の敏腕記者です。
        以下のチャットログと指示を元に、サーバーのスクープ記事を作成してください。
        
        スタイル: {style_instructions.get(style, "週刊誌風")}
        {target_context}
        {interview_context}
        
        以下の4つのセクションを生成してください。各セクションは [SECTION:名前] で区切ってください。
        
        [SECTION:COVER]
        - 雑誌の表紙用
        - 衝撃的な見出し（タイトル） ※必ず先頭に「# 」をつけてMarkdownの見出し1にしてください
        - サブタイトル 2-3個（「## 」をつけて見出し2に）
        - 画像生成用のプロンプト（英語で、被写体や状況を具体的に。例: "Prompt: A chaotic anime style scene..."）
        
        [SECTION:MAIN]
        - メイン記事本文（500〜600文字程度）
        - 読みやすさを最重視してください。
        - 1つの段落は短く（2-3行）。
        - 必要に応じて箇条書きを使用しても構いません。
        - チャットログの内容を面白おかしく脚色し、大げさに書いてください。
        - 最後に「### 編集後記」として一言コメントを入れる
        
        [SECTION:INTERVIEW]
        - {interview.display_name if interview else "関係者"}への独占インタビュー
        - 記者の質問と、対象者の回答（口調を真似る）
        - 衝撃の告白や迷言
        
        [SECTION:EXTRA]
        - Breaking News Ticker（速報テロップ用の一行ニュース 3つ）
        - 嘘広告（サーバー内のネタを使った架空の広告）
        - 今週の運勢（適当な星座と運勢）
        
        チャットログ:
        {chat_log}
        """
        
        try:
            response = await self.ai_cog.model.generate_content_async(prompt)
            content = response.text
            logger.info(f"Tabloid Raw Response: {content}")
            
            # Parse Content
            sections = {}
            current_section = None
            
            # Pre-processing to remove code blocks if present
            clean_content = content.replace("```json", "").replace("```", "")
            
            for line in clean_content.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                # More robust section detection
                if line.startswith('[SECTION:') and line.endswith(']'):
                    current_section = line[9:-1].upper() # Normalize to uppercase
                    sections[current_section] = []
                elif current_section:
                    sections[current_section].append(line)
            
            # Fallback
            if not sections:
                logger.warning("No sections found in Tabloid response. Using raw content as MAIN.")
                sections['MAIN'] = content.split('\n')
                sections['COVER'] = ["特集: 謎のスクープ", "AIが記事の生成に失敗したようです...", "Prompt: A glitchy computer screen"]
            
            # Process Sections
            cover_text = "\n".join(sections.get('COVER', ["記事生成エラー"])).strip()
            main_text = "\n".join(sections.get('MAIN', ["記事生成エラー"])).strip()
            interview_text = "\n".join(sections.get('INTERVIEW', ["インタビュー生成エラー"])).strip()
            extra_text = "\n".join(sections.get('EXTRA', ["情報生成エラー"])).strip()
            
            # Extract Image Prompt from Cover
            image_prompt = "A tabloid magazine cover, chaotic, funny, anime style"
            cover_lines = sections.get('COVER', [])
            for line in cover_lines:
                if "Prompt:" in line or "prompt:" in line or "プロンプト:" in line:
                    # Extract prompt text
                    parts = line.split(':', 1)
                    if len(parts) > 1:
                        image_prompt = parts[1].strip()
                    break
            
            # Generate Image
            image_url = None
            file = None
            if self.image_gen_cog:
                try:
                    logger.info(f"Generating tabloid image with prompt: {image_prompt}")
                    image_data = await self.image_gen_cog.generate_image(image_prompt)
                    if image_data:
                        # Try to upload to storage channel first
                        image_url = await self.upload_image(interaction, image_data, "scoop_cover.png")
                        
                        # If upload failed, fallback to attachment
                        if not image_url:
                            file = discord.File(io.BytesIO(image_data), filename="scoop_cover.png")
                    else:
                        logger.warning("Image generation returned None")
                except Exception as e:
                    logger.error(f"Image generation failed: {e}")

            # Build Pages (Embeds)
            pages = []
            
            # Page 1: Cover
            embed1 = discord.Embed(title="📰 週刊STELLA 最新号", description=cover_text, color=discord.Color.red())
            embed1.set_footer(text=f"発行日: {datetime.now().strftime('%Y/%m/%d')} | Vol.{random.randint(100, 999)}")
            if image_url:
                embed1.set_image(url=image_url)
            elif file:
                embed1.set_image(url="attachment://scoop_cover.png")
            pages.append(embed1)
            
            # Page 2: Main Scoop
            embed2 = discord.Embed(title="🔥 特集スクープ", description=main_text, color=discord.Color.orange())
            pages.append(embed2)
            
            # Page 3: Interview
            embed3 = discord.Embed(title="🎤 独占インタビュー", description=interview_text, color=discord.Color.purple())
            pages.append(embed3)
            
            # Page 4: Extra
            embed4 = discord.Embed(title="📢 広告・その他", description=extra_text, color=discord.Color.blue())
            pages.append(embed4)
            
            view = TabloidView(pages)
            
            if file:
                msg = await interaction.followup.send(embed=pages[0], view=view, file=file)
            else:
                msg = await interaction.followup.send(embed=pages[0], view=view)
            
            view.message = msg
            
            # Save data for persistence
            self.save_tabloid(msg.id, pages)
            
        except Exception as e:
            logger.error(f"Tabloid generation failed: {e}")
            await interaction.followup.send(f"❌ 記事の執筆中にペンが折れました（エラー）: {e}")

    @app_commands.command(name="scoop_tip", description="[週刊誌] 匿名でタレコミを投稿します")
    @app_commands.describe(content="タレコミ内容")
    async def scoop_tip(self, interaction: discord.Interaction, content: str):
        """Submit an anonymous tip"""
        await interaction.response.send_message("🕵️ タレコミを受領しました。編集部で裏取りを行います...", ephemeral=True)
        logger.info(f"Scoop Tip from {interaction.user}: {content}")

    @app_commands.command(name="scoop_lite", description="[週刊誌] サクッと読める短めの記事を生成します（画像あり）")
    async def scoop_lite(self, interaction: discord.Interaction):
        """Generate a lite version of tabloid scoop"""
        await interaction.response.defer()
        
        if not self.ai_cog:
            self.ai_cog = self.bot.get_cog('AICog')
        if not self.image_gen_cog:
            self.image_gen_cog = self.bot.get_cog('ImageGenCog')
            
        if not self.ai_cog or not self.ai_cog.model:
            await interaction.followup.send("❌ AI機能が利用できないため、記事を生成できません。")
            return

        # Fetch recent messages
        messages = []
        try:
            async for msg in interaction.channel.history(limit=30):
                if not msg.author.bot and msg.content:
                    messages.append(f"{msg.author.display_name}: {msg.content}")
        except Exception as e:
            await interaction.followup.send(f"❌ メッセージの取得に失敗しました: {e}")
            return
            
        if not messages:
            await interaction.followup.send("❌ 記事にするメッセージが見つかりませんでした。")
            return
            
        chat_log = "\n".join(messages)
        
        prompt = f"""
        あなたは「週刊STELLA」の記者です。
        以下のチャットログから、短いスクープ記事を作成してください。
        
        条件:
        1. 200〜300文字程度の短い記事にしてください。
        2. 見出し（タイトル）をつけてください。
        3. 画像生成用のプロンプト（英語）を含めてください。
        4. 出力形式は以下の通りにしてください。
        
        [TITLE] 記事のタイトル
        [BODY] 記事の本文
        [PROMPT] 画像生成プロンプト
        
        チャットログ:
        {chat_log}
        """
        
        try:
            response = await self.ai_cog.model.generate_content_async(prompt)
            content = response.text
            logger.info(f"Tabloid Lite Raw Response: {content}")
            
            title = "週刊STELLA スクープ号外"
            body = content
            image_prompt = "A funny tabloid photo"
            
            # Simple parsing
            lines = content.split('\n')
            clean_lines = []
            for line in lines:
                line = line.strip()
                if line.startswith("[TITLE]"):
                    title = line.replace("[TITLE]", "").strip()
                elif line.startswith("[PROMPT]"):
                    image_prompt = line.replace("[PROMPT]", "").strip()
                elif line.startswith("[BODY]"):
                    continue # Skip the tag itself
                elif line:
                    clean_lines.append(line)
            
            body = "\n".join(clean_lines)
            
            # Generate Image
            file = None
            if self.image_gen_cog:
                try:
                    logger.info(f"Generating lite image with prompt: {image_prompt}")
                    image_data = await self.image_gen_cog.generate_image(image_prompt)
                    if image_data:
                        file = discord.File(io.BytesIO(image_data), filename="scoop_lite.png")
                except Exception as e:
                    logger.error(f"Image generation failed: {e}")

            embed = discord.Embed(title=f"📰 {title}", description=body, color=discord.Color.orange())
            embed.set_footer(text=f"発行日: {datetime.now().strftime('%Y/%m/%d')} | Lite版")
            
            if file:
                embed.set_image(url="attachment://scoop_lite.png")
                await interaction.followup.send(embed=embed, file=file)
            else:
                await interaction.followup.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Tabloid Lite generation failed: {e}")
            await interaction.followup.send(f"❌ 記事生成エラー: {e}")

async def setup(bot):
    await bot.add_cog(TabloidCog(bot))
