import random
import discord
from discord.ext import commands

class RandomAbsoluteMember(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="random_absolute_member", help="Selects a random member with the 'absolute member' role and announces the selection.")
    async def random_absolute_member(self, ctx):
        """Selects a random member with the 'absolute member' role and announces the selection."""
        try:
            # Find the 'absolute member' role
            absolute_member_role = discord.utils.get(ctx.guild.roles, name="absolute member")

            if absolute_member_role is None:
                await ctx.send("Error: The 'absolute member' role was not found.")
                return

            # Get all members with the 'absolute member' role
            absolute_members = [member for member in ctx.guild.members if absolute_member_role in member.roles]

            if not absolute_members:
                await ctx.send("Error: No members with the 'absolute member' role were found.")
                return

            # Select a random member
            random_member = random.choice(absolute_members)

            # Announce the selection
            await ctx.send(f"Congratulations to {random_member.mention}! You have been randomly selected as an absolute member.")

        except Exception as e:
            print(f"Error in random_absolute_member command: {e}")
            await ctx.send("An error occurred while processing your request.")


async def setup(bot):
    await bot.add_cog(RandomAbsoluteMember(bot))