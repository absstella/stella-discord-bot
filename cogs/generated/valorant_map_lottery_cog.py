import json
import random
import os

import discord
from discord.ext import commands


class ValorantMapLottery(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data"
        self.map_file = os.path.join(self.data_dir, "valorant_maps.json")
        self.maps = self.load_maps()

        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)


    def load_maps(self):
        """Loads the Valorant map pool from a JSON file."""
        try:
            with open(self.map_file, "r") as f:
                maps = json.load(f)
        except FileNotFoundError:
            # Initialize with default maps if the file doesn't exist
            maps = ["Ascent", "Bind", "Breeze", "Fracture", "Haven", "Icebox", "Lotus", "Pearl", "Split", "Sunset"]
            self.save_maps(maps)  # Save the default maps to the file
        except json.JSONDecodeError:
            print("Error decoding valorant_maps.json.  Using default maps.")
            maps = ["Ascent", "Bind", "Breeze", "Fracture", "Haven", "Icebox", "Lotus", "Pearl", "Split", "Sunset"]
            self.save_maps(maps)
        return maps


    def save_maps(self, maps):
        """Saves the Valorant map pool to a JSON file."""
        try:
            with open(self.map_file, "w") as f:
                json.dump(maps, f, indent=4)
        except Exception as e:
            print(f"Error saving maps to {self.map_file}: {e}")


    @commands.command(name="map", description="Draws a random map from the current Valorant map pool.")
    async def map(self, ctx):
        """Draws a random Valorant map."""
        if not self.maps:
            await ctx.send("The map pool is empty. An admin needs to add maps using `!add_map`.")
            return

        selected_map = random.choice(self.maps)
        await ctx.send(f"Let's play on **{selected_map}**!")


    @commands.command(name="add_map", description="Adds a map to the map pool. (Requires Admin permissions)")
    @commands.has_permissions(administrator=True)
    async def add_map(self, ctx, map_name: str):
        """Adds a map to the Valorant map pool."""
        map_name = map_name.title()  # Capitalize the map name

        if map_name in self.maps:
            await ctx.send(f"**{map_name}** is already in the map pool.")
            return

        self.maps.append(map_name)
        self.save_maps(self.maps)
        await ctx.send(f"**{map_name}** has been added to the map pool.")


    @commands.command(name="remove_map", description="Removes a map from the map pool. (Requires Admin permissions)")
    @commands.has_permissions(administrator=True)
    async def remove_map(self, ctx, map_name: str):
        """Removes a map from the Valorant map pool."""
        map_name = map_name.title() # Capitalize the map name

        if map_name not in self.maps:
            await ctx.send(f"**{map_name}** is not in the map pool.")
            return

        self.maps.remove(map_name)
        self.save_maps(self.maps)
        await ctx.send(f"**{map_name}** has been removed from the map pool.")


    @commands.command(name="map_list", description="Displays the current map pool.")
    async def map_list(self, ctx):
        """Displays the current Valorant map pool."""
        if not self.maps:
            await ctx.send("The map pool is empty.")
            return

        map_list_str = "\n".join(f"- {map_name}" for map_name in self.maps)
        await ctx.send(f"Current map pool:\n{map_list_str}")


    @add_map.error
    @remove_map.error
    async def admin_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You need administrator permissions to use this command.")
        else:
            print(f"An error occurred: {error}")
            await ctx.send("An error occurred while processing the command.")



async def setup(bot):
    await bot.add_cog(ValorantMapLottery(bot))