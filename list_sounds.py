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
        print(f"Guild: {guild.name} ({guild.id})")
        sounds = await guild.fetch_soundboard_sounds()
        for sound in sounds:
            print(f"  Sound: {sound.name} (ID: {sound.id})")
    await client.close()

client.run(os.getenv('DISCORD_BOT_TOKEN'))
