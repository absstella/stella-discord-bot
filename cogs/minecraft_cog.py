"""
Minecraft Integration Cog
Server status checking and player monitoring
"""

import logging
import discord
from discord.ext import commands
from mcstatus import JavaServer
from typing import Optional

logger = logging.getLogger(__name__)

class MinecraftCog(commands.Cog):
    """Minecraft server integration"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(name='mcstatus', aliases=['mc', 'minecraft'])
    async def mcstatus(self, ctx, server_address: str = "localhost"):
        """Minecraftサーバーのステータスを確認します"""
        await ctx.send(f"🔍 サーバー `{server_address}` を確認中...")
        
        try:
            server = JavaServer.lookup(server_address)
            status = server.status()
            
            embed = discord.Embed(
                title=f"🎮 Minecraft Server Status",
                description=f"**{server_address}**",
                color=0x00ff00
            )
            
            embed.add_field(name="プレイヤー", value=f"{status.players.online}/{status.players.max}", inline=True)
            embed.add_field(name="バージョン", value=status.version.name, inline=True)
            embed.add_field(name="レイテンシ", value=f"{status.latency:.2f}ms", inline=True)
            
            if status.description:
                embed.add_field(name="説明", value=str(status.description), inline=False)
            
            if status.players.sample:
                players = ", ".join([p.name for p in status.players.sample[:10]])
                if len(status.players.sample) > 10:
                    players += f" ...他{len(status.players.sample) - 10}人"
                embed.add_field(name="オンラインプレイヤー", value=players, inline=False)
            
            embed.set_footer(text="S.T.E.L.L.A. Minecraft Integration")
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Minecraft status check error: {e}")
            await ctx.send(f"❌ サーバーへの接続に失敗しました: {str(e)}")

async def setup(bot):
    await bot.add_cog(MinecraftCog(bot))
