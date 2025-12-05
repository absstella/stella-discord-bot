import discord
from discord.ext import commands
import json
import os

class MamaResponder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_id_to_monitor = None
        self.load_data()

    def load_data(self):
        """Loads the user ID to monitor from data/mama_responder.json."""
        try:
            if not os.path.exists("data"):
                os.makedirs("data")
            with open("data/mama_responder.json", "r") as f:
                data = json.load(f)
                self.user_id_to_monitor = data.get("user_id_to_monitor")
        except FileNotFoundError:
            print("mama_responder.json not found, using default values.")
        except json.JSONDecodeError:
            print("Error decoding mama_responder.json. Please check the file.")
        except Exception as e:
            print(f"Error loading data: {e}")

    def save_data(self):
        """Saves the user ID to monitor to data/mama_responder.json."""
        try:
            data = {"user_id_to_monitor": self.user_id_to_monitor}
            with open("data/mama_responder.json", "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving data: {e}")


    @commands.Cog.listener()
    async def on_message(self, message):
        """Listens for messages and responds to the specified user."""
        if message.author.id == self.user_id_to_monitor and message.content == "ママー！":
            try:
                await message.channel.send("はいはい、ママでちゅよ♡")
            except discord.errors.Forbidden:
                print(f"Missing permissions to send messages in channel {message.channel.id}")
            except Exception as e:
                print(f"Error sending message: {e}")


async def setup(bot):
    await bot.add_cog(MamaResponder(bot))