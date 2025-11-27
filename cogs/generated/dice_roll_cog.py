import discord
from discord.ext import commands
import random

class DiceRoll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="roll", description="Rolls dice. For example, `!roll 2d6` rolls two six-sided dice.")
    async def roll(self, ctx, dice: str):
        """Rolls dice in NdN format."""
        try:
            num_dice, num_sides = map(int, dice.split('d'))
        except Exception:
            await ctx.send("Format must be in NdN!")
            return

        if num_dice > 100:
            await ctx.send("I can only roll up to 100 dice at once.")
            return
        if num_sides > 1000:
            await ctx.send("The maximum sides of dice is 1000.")
            return

        rolls = [random.randint(1, int(num_sides)) for _ in range(int(num_dice))]
        await ctx.send(" + ".join(map(str, rolls)) + f" = {sum(rolls)}")

async def setup(bot):
    await bot.add_cog(DiceRoll(bot))