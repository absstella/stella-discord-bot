import os
import asyncio
import logging
from typing import Dict, List, Optional
import discord
from discord.ext import commands
from datetime import datetime, timedelta
import google.generativeai as genai
from config import *

logger = logging.getLogger(__name__)

class SummaryCog(commands.Cog):
    """要約・議事録機能"""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Initialize Gemini for summarization
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
            logger.warning("Gemini API key not found for summarization")

    @commands.hybrid_command(name='summarize')
    async def summarize_messages(self, ctx, message_count: int = 50):
        """メッセージを要約 (/summarize 100)"""
        try:
            if not self.model:
                await ctx.send("❌ 要約機能が利用できません。")
                return
            
            if message_count < 5 or message_count > 200:
                await ctx.send("❌ メッセージ数は5-200の範囲で指定してください。")
                return
            
            await ctx.defer()  # 処理時間が長い可能性があるため
            
            # メッセージ履歴を取得
            messages = []
            async for message in ctx.channel.history(limit=message_count + 1):
                if message.id != ctx.message.id and not message.author.bot:
                    if message.content.strip():  # 空のメッセージは除外
                        messages.append({
                            'author': message.author.display_name,
                            'content': message.content,
                            'timestamp': message.created_at.strftime('%H:%M')
                        })
            
            if not messages:
                await ctx.send("❌ 要約するメッセージが見つかりません。")
                return
            
            messages.reverse()  # 時系列順に並び替え
            
            # 会話内容を構築
            conversation_text = "\n".join([
                f"[{msg['timestamp']}] {msg['author']}: {msg['content']}"
                for msg in messages
            ])
            
            # 要約プロンプト
            summary_prompt = f"""
            以下のDiscordチャンネルでの会話を日本語で要約してください。
            
            要約の形式:
            1. 主要な話題とポイント
            2. 重要な決定事項や結論
            3. 参加者の主な発言内容
            4. その他の注目すべき内容
            
            簡潔で分かりやすく、実用的な要約を作成してください。
            
            会話内容:
            {conversation_text}
            """
            
            response = self.model.generate_content(summary_prompt)
            
            if not response.text:
                await ctx.send("❌ 要約の生成に失敗しました。")
                return
            
            embed = discord.Embed(
                title="📝 会話要約",
                description=response.text.strip(),
                color=0x00ff9f,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="📊 要約情報",
                value=f"**対象メッセージ:** {len(messages)}件\n"
                      f"**参加者数:** {len(set(msg['author'] for msg in messages))}人\n"
                      f"**時間範囲:** {messages[0]['timestamp']} - {messages[-1]['timestamp']}",
                inline=False
            )
            
            embed.set_footer(text=f"要約者: {ctx.author.display_name}")
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Summarize error: {e}")
            await ctx.send(f"❌ 要約エラー: {str(e)}")

    @commands.hybrid_command(name='meeting_notes')
    async def create_meeting_notes(self, ctx, message_count: int = 100):
        """議事録を作成 (/meeting_notes 150)"""
        try:
            if not self.model:
                await ctx.send("❌ 議事録機能が利用できません。")
                return
            
            if message_count < 10 or message_count > 300:
                await ctx.send("❌ メッセージ数は10-300の範囲で指定してください。")
                return
            
            await ctx.defer()
            
            # メッセージ履歴を取得
            messages = []
            async for message in ctx.channel.history(limit=message_count + 1):
                if message.id != ctx.message.id and not message.author.bot:
                    if message.content.strip():
                        messages.append({
                            'author': message.author.display_name,
                            'content': message.content,
                            'timestamp': message.created_at.strftime('%m/%d %H:%M')
                        })
            
            if not messages:
                await ctx.send("❌ 議事録を作成するメッセージが見つかりません。")
                return
            
            messages.reverse()
            
            # 会話内容を構築
            conversation_text = "\n".join([
                f"[{msg['timestamp']}] {msg['author']}: {msg['content']}"
                for msg in messages
            ])
            
            # 議事録プロンプト
            meeting_prompt = f"""
            以下のDiscordチャンネルでの会話を基に、正式な議事録を日本語で作成してください。
            
            議事録の形式:
            # 議事録
            
            ## 基本情報
            - 日時: [開始時刻 - 終了時刻]
            - 参加者: [参加者一覧]
            - 場所: {ctx.channel.name}チャンネル
            
            ## 議題・討議内容
            [主要な話題や議論のポイントを箇条書きで]
            
            ## 決定事項
            [合意された内容や決定事項を箇条書きで]
            
            ## アクションアイテム
            [今後の行動予定や担当者が決まった事項]
            
            ## その他
            [補足事項や特記事項]
            
            会話内容:
            {conversation_text}
            """
            
            response = self.model.generate_content(meeting_prompt)
            
            if not response.text:
                await ctx.send("❌ 議事録の生成に失敗しました。")
                return
            
            # 長い議事録は複数のメッセージに分割
            meeting_notes = response.text.strip()
            
            if len(meeting_notes) <= 2000:
                embed = discord.Embed(
                    title="📋 議事録",
                    description=meeting_notes,
                    color=0x4169e1,
                    timestamp=datetime.utcnow()
                )
                embed.set_footer(text=f"作成者: {ctx.author.display_name}")
                await ctx.send(embed=embed)
            else:
                # 長い場合はファイルとして送信
                filename = f"meeting_notes_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(meeting_notes)
                
                embed = discord.Embed(
                    title="📋 議事録",
                    description="議事録が長いため、ファイルとして出力しました。",
                    color=0x4169e1,
                    timestamp=datetime.utcnow()
                )
                
                embed.add_field(
                    name="📊 統計情報",
                    value=f"**対象メッセージ:** {len(messages)}件\n"
                          f"**参加者数:** {len(set(msg['author'] for msg in messages))}人",
                    inline=False
                )
                
                await ctx.send(embed=embed, file=discord.File(filename))
                
                # ファイルを削除
                try:
                    os.remove(filename)
                except:
                    pass
            
        except Exception as e:
            logger.error(f"Meeting notes error: {e}")
            await ctx.send(f"❌ 議事録作成エラー: {str(e)}")

    @commands.hybrid_command(name='extract_decisions')
    async def extract_decisions(self, ctx, message_count: int = 80):
        """決定事項を抽出 (/extract_decisions 100)"""
        try:
            if not self.model:
                await ctx.send("❌ 決定事項抽出機能が利用できません。")
                return
            
            if message_count < 5 or message_count > 200:
                await ctx.send("❌ メッセージ数は5-200の範囲で指定してください。")
                return
            
            await ctx.defer()
            
            # メッセージ履歴を取得
            messages = []
            async for message in ctx.channel.history(limit=message_count + 1):
                if message.id != ctx.message.id and not message.author.bot:
                    if message.content.strip():
                        messages.append({
                            'author': message.author.display_name,
                            'content': message.content,
                            'timestamp': message.created_at.strftime('%H:%M')
                        })
            
            if not messages:
                await ctx.send("❌ 分析するメッセージが見つかりません。")
                return
            
            messages.reverse()
            
            conversation_text = "\n".join([
                f"[{msg['timestamp']}] {msg['author']}: {msg['content']}"
                for msg in messages
            ])
            
            # 決定事項抽出プロンプト
            decisions_prompt = f"""
            以下の会話から決定事項、合意内容、重要な結論を抽出してください。
            
            抽出する内容:
            1. 明確に決定された事項
            2. 合意に達した内容
            3. 今後のアクション項目
            4. 重要な方針や方向性
            
            各項目について、誰が何を決定したかも含めて、箇条書きで整理してください。
            決定事項がない場合は「決定事項なし」と回答してください。
            
            会話内容:
            {conversation_text}
            """
            
            response = self.model.generate_content(decisions_prompt)
            
            if not response.text:
                await ctx.send("❌ 決定事項の抽出に失敗しました。")
                return
            
            embed = discord.Embed(
                title="✅ 決定事項・合意内容",
                description=response.text.strip(),
                color=0x28a745,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="📊 分析対象",
                value=f"**メッセージ数:** {len(messages)}件\n"
                      f"**参加者数:** {len(set(msg['author'] for msg in messages))}人",
                inline=False
            )
            
            embed.set_footer(text=f"抽出者: {ctx.author.display_name}")
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Extract decisions error: {e}")
            await ctx.send(f"❌ 決定事項抽出エラー: {str(e)}")

    @commands.hybrid_command(name='topic_analysis')
    async def analyze_topics(self, ctx, message_count: int = 100):
        """話題分析 (/topic_analysis 150)"""
        try:
            if not self.model:
                await ctx.send("❌ 話題分析機能が利用できません。")
                return
            
            if message_count < 10 or message_count > 300:
                await ctx.send("❌ メッセージ数は10-300の範囲で指定してください。")
                return
            
            await ctx.defer()
            
            # メッセージ履歴を取得
            messages = []
            async for message in ctx.channel.history(limit=message_count + 1):
                if message.id != ctx.message.id and not message.author.bot:
                    if message.content.strip():
                        messages.append({
                            'author': message.author.display_name,
                            'content': message.content,
                            'timestamp': message.created_at.strftime('%H:%M')
                        })
            
            if not messages:
                await ctx.send("❌ 分析するメッセージが見つかりません。")
                return
            
            messages.reverse()
            
            conversation_text = "\n".join([
                f"[{msg['timestamp']}] {msg['author']}: {msg['content']}"
                for msg in messages
            ])
            
            # 話題分析プロンプト
            topic_prompt = f"""
            以下の会話の話題を分析し、以下の形式で回答してください:
            
            ## 主要話題
            1. [話題1] - 言及回数、参加者
            2. [話題2] - 言及回数、参加者
            
            ## 話題の変遷
            [時系列での話題の流れ]
            
            ## 最も活発だった話題
            [最も多く議論された内容]
            
            ## 参加者の貢献度
            [各参加者の発言傾向や貢献内容]
            
            会話内容:
            {conversation_text}
            """
            
            response = self.model.generate_content(topic_prompt)
            
            if not response.text:
                await ctx.send("❌ 話題分析に失敗しました。")
                return
            
            embed = discord.Embed(
                title="📈 話題分析結果",
                description=response.text.strip(),
                color=0x17a2b8,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="📊 分析データ",
                value=f"**総メッセージ数:** {len(messages)}件\n"
                      f"**参加者数:** {len(set(msg['author'] for msg in messages))}人\n"
                      f"**時間範囲:** {messages[0]['timestamp']} - {messages[-1]['timestamp']}",
                inline=False
            )
            
            embed.set_footer(text=f"分析者: {ctx.author.display_name}")
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Topic analysis error: {e}")
            await ctx.send(f"❌ 話題分析エラー: {str(e)}")

    @commands.hybrid_command(name='sentiment_analysis')
    async def analyze_sentiment(self, ctx, message_count: int = 50):
        """感情分析 (/sentiment_analysis 80)"""
        try:
            if not self.model:
                await ctx.send("❌ 感情分析機能が利用できません。")
                return
            
            if message_count < 5 or message_count > 200:
                await ctx.send("❌ メッセージ数は5-200の範囲で指定してください。")
                return
            
            await ctx.defer()
            
            # メッセージ履歴を取得
            messages = []
            async for message in ctx.channel.history(limit=message_count + 1):
                if message.id != ctx.message.id and not message.author.bot:
                    if message.content.strip():
                        messages.append({
                            'author': message.author.display_name,
                            'content': message.content,
                            'timestamp': message.created_at.strftime('%H:%M')
                        })
            
            if not messages:
                await ctx.send("❌ 分析するメッセージが見つかりません。")
                return
            
            messages.reverse()
            
            conversation_text = "\n".join([
                f"[{msg['timestamp']}] {msg['author']}: {msg['content']}"
                for msg in messages
            ])
            
            # 感情分析プロンプト
            sentiment_prompt = f"""
            以下の会話の感情的な雰囲気や感情の変化を分析してください:
            
            ## 全体的な雰囲気
            [ポジティブ/ネガティブ/ニュートラルの評価と理由]
            
            ## 感情の変化
            [時系列での感情の変遷]
            
            ## 参加者別の感情傾向
            [各参加者の感情的な傾向]
            
            ## 注目すべき感情の瞬間
            [特に感情が高まった場面や転換点]
            
            ## 改善提案
            [より良いコミュニケーションのための提案があれば]
            
            会話内容:
            {conversation_text}
            """
            
            response = self.model.generate_content(sentiment_prompt)
            
            if not response.text:
                await ctx.send("❌ 感情分析に失敗しました。")
                return
            
            embed = discord.Embed(
                title="💭 感情分析結果",
                description=response.text.strip(),
                color=0xe91e63,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="📊 分析対象",
                value=f"**メッセージ数:** {len(messages)}件\n"
                      f"**参加者数:** {len(set(msg['author'] for msg in messages))}人",
                inline=False
            )
            
            embed.set_footer(text=f"分析者: {ctx.author.display_name}")
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            await ctx.send(f"❌ 感情分析エラー: {str(e)}")

async def setup(bot):
    await bot.add_cog(SummaryCog(bot))