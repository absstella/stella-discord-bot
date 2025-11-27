"""
Custom Reaction Cog
Automated emoji reactions based on keywords
"""

import logging
import discord
from discord.ext import commands
import json
import os
import re
from typing import Dict, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ReactionCog(commands.Cog):
    """Custom auto-reaction system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.reactions_file = "data/custom_reactions.json"
        self.reactions: Dict[int, List[Dict]] = {}  # guild_id -> reactions
        self.cooldowns: Dict[str, datetime] = {}  # key -> last_trigger_time
        self.load_reactions()
    
    def load_reactions(self):
        """Load reactions from file"""
        try:
            if os.path.exists(self.reactions_file):
                with open(self.reactions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Convert string keys to int
                    self.reactions = {int(k): v for k, v in data.items()}
                logger.info(f"Loaded {len(self.reactions)} guild reaction configs")
        except Exception as e:
            logger.error(f"Error loading reactions: {e}")
            self.reactions = {}
    
    def save_reactions(self):
        """Save reactions to file"""
        try:
            os.makedirs(os.path.dirname(self.reactions_file), exist_ok=True)
            with open(self.reactions_file, 'w', encoding='utf-8') as f:
                # Convert int keys to string for JSON
                data = {str(k): v for k, v in self.reactions.items()}
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info("Saved reaction configs")
        except Exception as e:
            logger.error(f"Error saving reactions: {e}")
    
    def check_cooldown(self, key: str, cooldown_seconds: int = 60) -> bool:
        """Check if reaction is on cooldown"""
        if key in self.cooldowns:
            elapsed = (datetime.now() - self.cooldowns[key]).total_seconds()
            return elapsed < cooldown_seconds
        return False
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Auto-react to messages based on keywords"""
        if message.author.bot:
            return
        
        if not message.guild:
            return
        
        guild_id = message.guild.id
        if guild_id not in self.reactions:
            return
        
        content = message.content.lower()
        
        for reaction_config in self.reactions[guild_id]:
            keyword = reaction_config['keyword'].lower()
            emoji = reaction_config['emoji']
            use_regex = reaction_config.get('regex', False)
            
            # Check if keyword matches
            matched = False
            if use_regex:
                try:
                    if re.search(keyword, content, re.IGNORECASE):
                        matched = True
                except re.error:
                    logger.error(f"Invalid regex pattern: {keyword}")
                    continue
            else:
                if keyword in content:
                    matched = True
            
            if matched:
                # Check cooldown
                cooldown_key = f"{guild_id}_{keyword}_{message.channel.id}"
                if self.check_cooldown(cooldown_key):
                    continue
                
                try:
                    await message.add_reaction(emoji)
                    self.cooldowns[cooldown_key] = datetime.now()
                    logger.info(f"Added reaction {emoji} to message in {message.guild.name}")
                except Exception as e:
                    logger.error(f"Failed to add reaction: {e}")
    
    @commands.hybrid_command(name='react')
    async def react_command(self, ctx):
        """カスタムリアクション管理のヘルプ"""
        embed = discord.Embed(
            title="🎨 カスタムリアクション",
            description="キーワードに自動的に絵文字でリアクションします",
            color=0xff9900
        )
        
        embed.add_field(
            name="リアクション追加",
            value="`!react add [キーワード] [絵文字]`\n例: `!react add ありがとう 🙏`",
            inline=False
        )
        
        embed.add_field(
            name="リアクション削除",
            value="`!react remove [キーワード]`",
            inline=False
        )
        
        embed.add_field(
            name="リアクション一覧",
            value="`!react list`",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='react_add')
    async def react_add(self, ctx, keyword: str, emoji: str):
        """リアクションを追加します"""
        guild_id = ctx.guild.id
        
        if guild_id not in self.reactions:
            self.reactions[guild_id] = []
        
        # Check if keyword already exists
        for reaction in self.reactions[guild_id]:
            if reaction['keyword'].lower() == keyword.lower():
                await ctx.send(f"❌ キーワード「{keyword}」は既に登録されています")
                return
        
        # Add new reaction
        self.reactions[guild_id].append({
            'keyword': keyword,
            'emoji': emoji,
            'regex': False,
            'added_by': ctx.author.id,
            'added_at': datetime.now().isoformat()
        })
        
        self.save_reactions()
        await ctx.send(f"✅ リアクションを追加しました: 「{keyword}」→ {emoji}")
    
    @commands.hybrid_command(name='react_remove')
    async def react_remove(self, ctx, keyword: str):
        """リアクションを削除します"""
        guild_id = ctx.guild.id
        
        if guild_id not in self.reactions:
            await ctx.send("❌ このサーバーにはリアクションが登録されていません")
            return
        
        # Find and remove reaction
        for i, reaction in enumerate(self.reactions[guild_id]):
            if reaction['keyword'].lower() == keyword.lower():
                removed = self.reactions[guild_id].pop(i)
                self.save_reactions()
                await ctx.send(f"✅ リアクションを削除しました: 「{keyword}」→ {removed['emoji']}")
                return
        
        await ctx.send(f"❌ キーワード「{keyword}」は登録されていません")
    
    @commands.hybrid_command(name='react_list')
    async def react_list(self, ctx):
        """登録されているリアクション一覧を表示します"""
        guild_id = ctx.guild.id
        
        if guild_id not in self.reactions or not self.reactions[guild_id]:
            await ctx.send("このサーバーにはリアクションが登録されていません")
            return
        
        embed = discord.Embed(
            title="🎨 登録済みリアクション",
            color=0x00ff00
        )
        
        for reaction in self.reactions[guild_id][:25]:  # Limit to 25
            keyword = reaction['keyword']
            emoji = reaction['emoji']
            regex_mark = " (正規表現)" if reaction.get('regex') else ""
            embed.add_field(
                name=f"{keyword}{regex_mark}",
                value=emoji,
                inline=True
            )
        
        if len(self.reactions[guild_id]) > 25:
            embed.set_footer(text=f"...他{len(self.reactions[guild_id]) - 25}個")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ReactionCog(bot))
