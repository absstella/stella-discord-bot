import discord
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.guilds = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    for guild in client.guilds:
        if guild.name == "AbsCL": # Target guild
            sounds = await guild.fetch_soundboard_sounds()
            for sound in sounds:
                if sound.id == 1100715717038460979: # Hikakin4ne
                    print(f"Sound found: {sound.name}")
                    print(f"Attributes: {dir(sound)}")
                    print(f"URL: {sound.url}")
                    break
    await client.close()

client.run(os.getenv('DISCORD_BOT_TOKEN'))
