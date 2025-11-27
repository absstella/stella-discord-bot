import json
import random
import os

import discord
from discord.ext import commands

class ValowWeaponLottery(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.weapon_list = self.load_weapon_list()

    def load_weapon_list(self):
        """武器リストをJSONファイルからロードします。"""
        try:
            data_dir = "data"
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            
            file_path = os.path.join(data_dir, "valow_weapon_list.json")
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: valow_weapon_list.json not found in {data_dir}.  Please create the file.")
            return []
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in valow_weapon_list.json.  Please check the file.")
            return []
        except Exception as e:
            print(f"Error loading weapon list: {e}")
            return []

    @commands.command(name="valow武器抽選", aliases=["valow武器"])
    async def valow_weapon_lottery(self, ctx):
        """Valowの武器リストからランダムに武器を抽選します。"""
        if not self.weapon_list:
            await ctx.send("武器リストがロードされていません。")
            return

        try:
            weapon = random.choice(self.weapon_list)
            await ctx.send(f"{ctx.author.mention} が引いた武器は **{weapon}** です！")
        except Exception as e:
            print(f"Error during weapon lottery: {e}")
            await ctx.send("武器の抽選中にエラーが発生しました。")

async def setup(bot):
    await bot.add_cog(ValowWeaponLottery(bot))