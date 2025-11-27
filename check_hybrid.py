
from discord.ext import commands
try:
    print(f"hybrid_command exists: {hasattr(commands, 'hybrid_command')}")
except Exception as e:
    print(f"Error: {e}")
