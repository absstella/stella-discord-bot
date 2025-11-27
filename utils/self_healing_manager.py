"""
Self-Healing Manager
Analyzes errors and proposes fixes using Gemini
"""

import logging
import traceback
import os
import google.generativeai as genai
import discord
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class SelfHealingManager:
    def __init__(self, bot):
        self.bot = bot
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        else:
            self.model = None

    async def handle_error(self, ctx, error: Exception, context_info: str = ""):
        """Analyze error and propose fix to owner"""
        if not self.model:
            return

        # Get full traceback
        tb_str = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        
        logger.error(f"SelfHealingManager analyzing error: {error}")
        
        # Generate fix proposal
        prompt = f"""
        以下のPythonエラーを分析し、修正コードを提案してください。
        
        エラー内容:
        {str(error)}
        
        トレースバック:
        {tb_str}
        
        コンテキスト:
        {context_info}
        
        指示:
        1. エラーの原因を特定してください。
        2. 修正するための具体的なPythonコードを提示してください。
        3. コードは ```python ... ``` ブロックで囲んでください。
        """
        
        try:
            response = await self.model.generate_content_async(prompt)
            fix_proposal = response.text
            
            # Notify owner
            await self._notify_owner(ctx, error, fix_proposal)
            
        except Exception as e:
            logger.error(f"SelfHealingManager failed to generate fix: {e}")

    async def _notify_owner(self, ctx, error, fix_proposal):
        """Send fix proposal to bot owner"""
        # Find owner (assuming first owner if multiple, or specific ID)
        app_info = await self.bot.application_info()
        owner = app_info.owner
        
        if owner:
            embed = discord.Embed(
                title="🚨 エラー発生と修正提案 (Self-Healing)",
                description=f"コマンド `{ctx.command}` の実行中にエラーが発生しました。",
                color=0xff0000
            )
            
            embed.add_field(name="エラー", value=str(error)[:1000], inline=False)
            
            # Split proposal if too long
            if len(fix_proposal) > 1000:
                embed.add_field(name="修正提案 (抜粋)", value=fix_proposal[:1000] + "...", inline=False)
            else:
                embed.add_field(name="修正提案", value=fix_proposal, inline=False)
                
            await owner.send(embed=embed)
            
            # Send full proposal as text file if long
            if len(fix_proposal) > 1000:
                import io
                f = io.StringIO(fix_proposal)
                await owner.send(file=discord.File(f, filename="fix_proposal.md"))
