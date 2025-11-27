"""
Voice Interaction Cog
Text-to-Speech functionality for Discord voice channels
Supports both gTTS and VOICEVOX
"""

import logging
import discord
from discord.ext import commands
from gtts import gTTS
import os
import asyncio
from typing import Optional
from utils.voicevox_client import VOICEVOXClient

logger = logging.getLogger(__name__)

class VoiceCog(commands.Cog):
    """Voice channel interaction"""
    
    def __init__(self, bot):
        self.bot = bot
        self.voice_clients = {}
        self.voicevox = VOICEVOXClient()
        self.voicevox_available = False
        # Check VOICEVOX availability on init
        asyncio.create_task(self._check_voicevox())
    
    async def _check_voicevox(self):
        """Check if VOICEVOX is available"""
        self.voicevox_available = await self.voicevox.check_availability()
        if self.voicevox_available:
            logger.info("VOICEVOX is available and will be used for TTS")
        else:
            logger.info("VOICEVOX not available, falling back to gTTS")
    
    @commands.hybrid_command(name='join', aliases=['vc'])
    async def join(self, ctx):
        """ボイスチャンネルに参加します"""
        if not ctx.author.voice:
            await ctx.send("❌ 先にボイスチャンネルに参加してください！")
            return
        
        channel = ctx.author.voice.channel
        
        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()
        
        await ctx.send(f"✅ {channel.name} に参加しました！")
    
    @commands.hybrid_command(name='leave', aliases=['dc', 'disconnect'])
    async def leave(self, ctx):
        """ボイスチャンネルから退出します"""
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("👋 ボイスチャンネルから退出しました")
        else:
            await ctx.send("❌ ボイスチャンネルに接続していません")
    
    @commands.hybrid_command(name='speak', aliases=['say', 'tts'])
    async def speak(self, ctx, *, text: str):
        """テキストを読み上げます（オプション: --speaker 3 でキャラ変更、--slow で遅く）"""
        if not ctx.voice_client:
            await ctx.send("❌ 先に `!join` でボイスチャンネルに参加してください")
            return
        
        if ctx.voice_client.is_playing():
            await ctx.send("⏸️ 現在再生中です。少々お待ちください...")
            return
        
        # Parse options
        slow = False
        lang = 'ja'
        speaker_id = 3  # Default: ずんだもん
        use_voicevox = self.voicevox_available
        
        if '--speaker' in text:
            parts = text.split('--speaker')
            if len(parts) > 1:
                try:
                    speaker_id = int(parts[1].split()[0])
                    text = parts[0] + ' '.join(parts[1].split()[1:])
                except:
                    pass
        
        if '--gtts' in text:
            use_voicevox = False
            text = text.replace('--gtts', '').strip()
        
        if '--slow' in text:
            slow = True
            text = text.replace('--slow', '').strip()
        elif '--fast' in text:
            slow = False
            text = text.replace('--fast', '').strip()
        
        if '--en' in text:
            lang = 'en'
            use_voicevox = False  # VOICEVOX is Japanese only
            text = text.replace('--en', '').strip()
        
        try:
            filename = f"tts_{ctx.author.id}.wav" if use_voicevox else f"tts_{ctx.author.id}.mp3"
            
            # Use VOICEVOX if available and requested
            if use_voicevox and lang == 'ja':
                success = await self.voicevox.synthesize(text, speaker_id, filename)
                if not success:
                    await ctx.send("⚠️ VOICEVOX合成に失敗しました。gTTSにフォールバックします...")
                    use_voicevox = False
            
            # Fallback to gTTS
            if not use_voicevox:
                tts = gTTS(text=text, lang=lang, slow=slow)
                filename = f"tts_{ctx.author.id}.mp3"
                tts.save(filename)
            
            # Play audio
            ctx.voice_client.play(
                discord.FFmpegPCMAudio(filename),
                after=lambda e: os.remove(filename) if os.path.exists(filename) else None
            )
            
            engine = "VOICEVOX" if use_voicevox else "gTTS"
            speed_text = "ゆっくり" if slow else "通常"
            lang_text = "英語" if lang == 'en' else "日本語"
            speaker_text = f" (Speaker {speaker_id})" if use_voicevox else ""
            await ctx.send(f"🔊 読み上げ中 [{engine}{speaker_text}] ({lang_text}, {speed_text}): {text[:50]}...")
            
        except Exception as e:
            logger.error(f"TTS error: {e}")
            await ctx.send(f"❌ 読み上げ中にエラーが発生しました: {str(e)}")
    
    @commands.hybrid_command(name='voice', aliases=['voicesettings'])
    async def voice_settings(self, ctx):
        """音声設定のヘルプを表示します"""
        embed = discord.Embed(
            title="🎙️ 音声設定",
            description="読み上げ機能のオプション",
            color=0x00ff00
        )
        
        voicevox_status = "✅ 利用可能" if self.voicevox_available else "❌ 未起動"
        embed.add_field(
            name="VOICEVOX状態",
            value=voicevox_status,
            inline=False
        )
        
        embed.add_field(
            name="基本的な使い方",
            value="`!speak こんにちは`",
            inline=False
        )
        
        if self.voicevox_available:
            embed.add_field(
                name="キャラクター変更 (VOICEVOX)",
                value="`!speak --speaker 3 ずんだもんだよ`\n`!speak --speaker 1 四国めたんです`",
                inline=False
            )
        
        embed.add_field(
            name="速度変更",
            value="`!speak --slow ゆっくり話します`\n`!speak --fast 速く話します`",
            inline=False
        )
        
        embed.add_field(
            name="言語変更",
            value="`!speak --en Hello, I am STELLA`",
            inline=False
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(VoiceCog(bot))
