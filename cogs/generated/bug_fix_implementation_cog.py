import discord
from discord.ext import commands
import json
import os
import random

class BugFix(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bug_data_file = "data/bugs.json"
        self.bugs = self.load_bugs()

        # Ensure the 'data' directory exists
        if not os.path.exists("data"):
            os.makedirs("data")

    def load_bugs(self):
        """Loads bug data from the JSON file."""
        try:
            with open(self.bug_data_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            print(f"Error decoding JSON in {self.bug_data_file}.  Starting with an empty bug list.")
            return {}

    def save_bugs(self):
        """Saves bug data to the JSON file."""
        try:
            with open(self.bug_data_file, "w") as f:
                json.dump(self.bugs, f, indent=4)
        except Exception as e:
            print(f"Error saving bug data to {self.bug_data_file}: {e}")


    @commands.command(name="bugfix")
    async def bugfix(self, ctx, bug_id: str, *, fix_description: str):
        """Documents and assigns a description to a specific bug ID."""
        try:
            if bug_id in self.bugs:
                self.bugs[bug_id]["fix_description"] = fix_description
                self.bugs[bug_id]["status"] = "fixing"
                self.save_bugs()
                await ctx.send(f"Bug ID {bug_id} marked as fixing with description: {fix_description}")
            else:
                await ctx.send(f"Bug ID {bug_id} not found.  Use !reportbug first to create the bug report.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")


    @commands.command(name="reportbug")
    async def reportbug(self, ctx, *, bug_description: str):
        """Allows users to report bugs, automatically generating a bug ID."""
        try:
            bug_id = self.generate_bug_id()
            self.bugs[bug_id] = {
                "reporter": ctx.author.id,
                "description": bug_description,
                "status": "reported",
                "fix_description": None
            }
            self.save_bugs()
            await ctx.send(f"Bug reported with ID: {bug_id}.  Please use this ID to track the bug.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command(name="resolvebug")
    async def resolvebug(self, ctx, bug_id: str):
        """Marks a bug as resolved."""
        try:
            if bug_id in self.bugs:
                self.bugs[bug_id]["status"] = "resolved"
                self.save_bugs()
                await ctx.send(f"Bug ID {bug_id} marked as resolved.")
            else:
                await ctx.send(f"Bug ID {bug_id} not found.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    def generate_bug_id(self):
        """Generates a unique bug ID."""
        while True:
            bug_id = "BUG-" + str(random.randint(1000, 9999))
            if bug_id not in self.bugs:
                return bug_id

async def setup(bot):
    await bot.add_cog(BugFix(bot))