import random
import discord
from discord.ext import commands

class ValorantAgentLottery(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.agent_list = [
            "Breach", "Raze", "Phoenix", "Jett", "Reyna", "Sova", "Sage", "Viper",
            "Brimstone", "Omen", "Killjoy", "Cypher", "Skye", "Yoru", "Astra",
            "KAY/O", "Chamber", "Neon", "Fade", "Harbor", "Gekko", "Deadlock", "Iso"
        ]

    @commands.command(name="agent_lottery", description="Draws a random Valorant agent.")
    async def agent_lottery(self, ctx):
        """Draws a random Valorant agent."""
        try:
            agent = random.choice(self.agent_list)
            await ctx.send(f"Your Valorant agent is: **{agent}**")
        except Exception as e:
            print(f"Error in agent_lottery command: {e}")
            await ctx.send("An error occurred while selecting an agent. Please try again later.")

async def setup(bot):
    await bot.add_cog(ValorantAgentLottery(bot))