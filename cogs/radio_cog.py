import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import logging
import random
import os
from gtts import gTTS

logger = logging.getLogger(__name__)

class RadioCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.is_broadcasting = False
        self.current_task = None
        self.radio_channel = None

    @app_commands.command(name="start_radio", description="[ラジオ] STELLAラジオ局を開局します")
    @app_commands.describe(channel="放送するボイスチャンネル")
    async def start_radio(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        """Start the radio broadcast"""
        if self.is_broadcasting:
            await interaction.response.send_message("⚠️ ラジオは既に放送中です。", ephemeral=True)
            return

        await interaction.response.defer()
        
        # Connect to VC
        try:
            if interaction.guild.voice_client:
                await interaction.guild.voice_client.move_to(channel)
                vc = interaction.guild.voice_client
            else:
                vc = await channel.connect()
        except Exception as e:
            await interaction.followup.send(f"❌ 接続エラー: {e}")
            return

        self.is_broadcasting = True
        self.radio_channel = channel
        self.current_task = asyncio.create_task(self.radio_loop(interaction, vc))
        
        await interaction.followup.send(f"🎙️ **STELLAラジオ局** 開局しました！\nチャンネル: {channel.name}")

    @app_commands.command(name="stop_radio", description="[ラジオ] 放送を終了します")
    async def stop_radio(self, interaction: discord.Interaction):
        """Stop the radio broadcast"""
        if not self.is_broadcasting:
            await interaction.response.send_message("❌ ラジオは放送されていません。", ephemeral=True)
            return

        self.is_broadcasting = False
        if self.current_task:
            self.current_task.cancel()
        
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            
        await interaction.response.send_message("🛑 放送を終了しました。また次回！", ephemeral=True)

    async def radio_loop(self, interaction, vc):
        """Main radio loop"""
        try:
            # Get AI Cog for generation
            ai_cog = self.bot.get_cog('AICog')
            voice_cog = self.bot.get_cog('VoiceCog')
            
            while self.is_broadcasting:
                if not vc.is_connected():
                    break

                # 1. Generate Script from Real Chat History
                try:
                    # Fetch recent messages from the text channel where command was invoked
                    # We stored interaction in self.current_interaction if possible, or just use a default channel
                    # For simplicity, let's try to fetch from the channel where the command was used
                    target_channel = interaction.channel
                    messages = []
                    if target_channel:
                         async for msg in target_channel.history(limit=20):
                            if not msg.author.bot and msg.content:
                                messages.append(f"{msg.author.display_name}: {msg.content}")
                    
                    if messages:
                        chat_context = "\n".join(messages)
                        topic_prompt = f"以下のチャットログから、ラジオのトークテーマになりそうな話題を1つピックアップしてください。\n\n{chat_context}"
                    else:
                        chat_context = "特に会話なし"
                        topic_prompt = "最近の天気や季節の話題"

                except Exception as e:
                    logger.error(f"Failed to fetch history: {e}")
                    chat_context = "取得エラー"
                    topic_prompt = "AIの日常について"

                prompt = f"""
                あなたはラジオDJのSTELLAです。
                以下のチャットログ（またはトピック）を元に、リスナー（サーバーメンバー）に向けたラジオトークの台本を書いてください。
                
                チャットログ/トピック:
                {chat_context}
                
                条件:
                1. 実際のメンバーの名前を出して、「〇〇さんがこんなこと言ってましたね〜」と紹介する。
                2. ユーモアと親しみを込めて、少し辛口でもOK。
                3. 1分程度で話せる長さ。
                4. 構成: オープニング -> メイントーク -> 曲紹介（架空） -> エンディング
                
                ※ 台本のみを出力してください。
                """
                
                script = "本日は晴天なり..." 
                if ai_cog and ai_cog.model:
                    try:
                        response = await ai_cog.model.generate_content_async(prompt)
                        script = response.text
                    except Exception as e:
                        logger.error(f"Script generation failed: {e}")
                        script = "えー、只今通信障害が発生しております。音楽をお楽しみください。"

                # 2. Speak Script
                # Split script into chunks if needed, but for now just speak it all
                # We use VoiceCog's logic manually
                
                # Check for VOICEVOX
                use_voicevox = False
                if voice_cog and voice_cog.voicevox_available:
                    use_voicevox = True
                
                filename = f"radio_{interaction.guild_id}.wav" if use_voicevox else f"radio_{interaction.guild_id}.mp3"
                
                try:
                    if use_voicevox:
                        # Random speaker for variety? Or keep it consistent? Let's use Zundamon (3) or Metan (2)
                        speaker_id = 3 
                        success = await voice_cog.voicevox.synthesize(script, speaker_id, filename)
                        if not success:
                            use_voicevox = False # Fallback
                    
                    if not use_voicevox:
                        tts = gTTS(text=script, lang='ja')
                        filename = f"radio_{interaction.guild_id}.mp3"
                        tts.save(filename)
                    
                    # Play audio
                    if vc.is_playing():
                        vc.stop()
                        
                    vc.play(discord.FFmpegPCMAudio(filename), after=lambda e: self.cleanup_file(filename))
                    
                    # Wait for audio to finish
                    while vc.is_playing():
                        await asyncio.sleep(1)
                        if not self.is_broadcasting:
                            vc.stop()
                            return

                except Exception as e:
                    logger.error(f"Radio TTS error: {e}")
                
                # 3. Wait/Intermission
                await asyncio.sleep(5) # Short break between segments

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Radio loop error: {e}")
            self.is_broadcasting = False

    def cleanup_file(self, filename):
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except:
                pass

async def setup(bot):
    await bot.add_cog(RadioCog(bot))
