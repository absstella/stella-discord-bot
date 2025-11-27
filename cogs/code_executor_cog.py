"""
Code Executor Cog
AI Assistant with code execution, calculations, and data visualization
"""

import logging
import discord
from discord.ext import commands
import sympy
import io
import sys
from contextlib import redirect_stdout
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

logger = logging.getLogger(__name__)

class CodeExecutorCog(commands.Cog):
    """AI Assistant with code execution capabilities"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(name='calc', aliases=['calculate', '計算'])
    async def calculate(self, ctx, *, expression: str):
        """数式を計算します"""
        try:
            # Use sympy for safe mathematical evaluation
            result = sympy.sympify(expression)
            evaluated = result.evalf()
            
            embed = discord.Embed(
                title="🧮 計算結果",
                color=0x00ff00
            )
            embed.add_field(name="式", value=f"`{expression}`", inline=False)
            embed.add_field(name="結果", value=f"`{evaluated}`", inline=False)
            
            # Show simplified form if different
            simplified = sympy.simplify(result)
            if str(simplified) != str(result):
                embed.add_field(name="簡略化", value=f"`{simplified}`", inline=False)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ 計算エラー: {str(e)}")
    
    @commands.hybrid_command(name='plot', aliases=['graph', 'グラフ'])
    async def plot(self, ctx, *, data: str):
        """データをグラフ化します（例: 1,2,3,4,5）"""
        try:
            # Parse data
            values = [float(x.strip()) for x in data.split(',')]
            
            # Create plot
            plt.figure(figsize=(10, 6))
            plt.plot(values, marker='o', linestyle='-', linewidth=2, markersize=8)
            plt.title('Data Visualization', fontsize=16)
            plt.xlabel('Index', fontsize=12)
            plt.ylabel('Value', fontsize=12)
            plt.grid(True, alpha=0.3)
            
            # Save to buffer
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            plt.close()
            
            # Send as file
            file = discord.File(buffer, filename='plot.png')
            embed = discord.Embed(
                title="📊 データグラフ",
                description=f"データポイント数: {len(values)}",
                color=0x00ff00
            )
            embed.set_image(url="attachment://plot.png")
            
            await ctx.send(embed=embed, file=file)
            
        except Exception as e:
            await ctx.send(f"❌ グラフ生成エラー: {str(e)}")
    
    @commands.hybrid_command(name='exec', aliases=['run', '実行'])
    async def execute_code(self, ctx, *, code: str):
        """Pythonコードを実行します（制限付き）"""
        # Remove code block markers if present
        if code.startswith('```python'):
            code = code[9:]
        if code.startswith('```'):
            code = code[3:]
        if code.endswith('```'):
            code = code[:-3]
        code = code.strip()
        
        # Safety check
        forbidden = ['import os', 'import sys', 'open(', 'exec(', 'eval(', '__']
        for keyword in forbidden:
            if keyword in code.lower():
                await ctx.send(f"❌ セキュリティ上の理由により、`{keyword}` は使用できません")
                return
        
        try:
            # Capture output
            output_buffer = io.StringIO()
            
            with redirect_stdout(output_buffer):
                # Execute in limited namespace
                namespace = {
                    'print': print,
                    'range': range,
                    'len': len,
                    'sum': sum,
                    'max': max,
                    'min': min,
                    'abs': abs,
                    'round': round,
                }
                exec(code, namespace)
            
            output = output_buffer.getvalue()
            
            if not output:
                output = "（出力なし）"
            
            # Limit output length
            if len(output) > 1900:
                output = output[:1900] + "\n... (出力が長すぎるため省略)"
            
            embed = discord.Embed(
                title="💻 コード実行結果",
                color=0x00ff00
            )
            embed.add_field(name="コード", value=f"```python\n{code[:500]}\n```", inline=False)
            embed.add_field(name="出力", value=f"```\n{output}\n```", inline=False)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ 実行エラー: {str(e)}")
    
    @commands.hybrid_command(name='math', aliases=['数学'])
    async def math_help(self, ctx):
        """数学・計算機能のヘルプ"""
        embed = discord.Embed(
            title="🧮 数学・計算機能",
            description="STELLAの計算・グラフ機能",
            color=0x00ff00
        )
        
        embed.add_field(
            name="計算",
            value="`!calc 2+2`\n`!calc sqrt(16)`\n`!calc sin(pi/2)`",
            inline=False
        )
        
        embed.add_field(
            name="グラフ",
            value="`!plot 1,2,3,4,5`\n`!plot 10,20,15,25,30`",
            inline=False
        )
        
        embed.add_field(
            name="コード実行",
            value="`!exec print('Hello')`\n`!exec for i in range(5): print(i)`",
            inline=False
        )
        
        embed.set_footer(text="⚠️ コード実行は制限付きです")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CodeExecutorCog(bot))
