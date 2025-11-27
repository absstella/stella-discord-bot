import os

# Bot Configuration
COMMAND_PREFIX = "!"
BOT_NAME = "S.T.E.L.L.A."
BOT_VERSION = "2.0"

# Discord Configuration
MAX_MESSAGE_LENGTH = 2000
EMBED_COLOR = 0x00ff9f
ERROR_COLOR = 0xff0000
WARNING_COLOR = 0xffaa00
SUCCESS_COLOR = 0x00ff00

# Music Configuration
MAX_QUEUE_SIZE = 50
DEFAULT_VOLUME = 50
SEARCH_CACHE_SIZE = 100
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'extractorname': 'youtube',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# AI Configuration
AI_MODEL = "gemini-2.0-flash"
GENERATION_CONFIG = {
    "temperature": 0.7,
    "top_p": 0.8,
    "top_k": 40,
    "max_output_tokens": 2048,
}

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost/stella')

# Google Drive Configuration
GOOGLE_DRIVE_FOLDER = "S.T.E.L.L.A.会話記憶"

# Team Management Configuration
TEMP_VC_CATEGORY = "一時的なボイスチャンネル"
RECRUITMENT_TIMEOUT = 300  # 5 minutes

# Utility Configuration
REMINDER_CHECK_INTERVAL = 60  # seconds
BIRTHDAY_CHECK_TIME = "09:00"
QUOTE_CACHE_SIZE = 50

# Performance Configuration
CLEANUP_INTERVAL = 300  # 5 minutes
MAX_MEMORY_MB = 512
HEALTH_CHECK_PORT = 8000

# API Keys (from environment variables)
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID')
GOOGLE_DRIVE_SERVICE_ACCOUNT = os.getenv('GOOGLE_DRIVE_SERVICE_ACCOUNT')

# Google Drive Configuration
GOOGLE_DRIVE_FOLDER = "Conversations"  # Default folder name

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = 'stella.log'
