from config import COMMAND_PREFIX

HELP_DATA = {
    "ai": {
        "title": "AI & Search",
        "description": "AI conversation, web search, and smart assistance features powered by Gemini AI.",
        "commands": [
            {
                "name": "ask <question>",
                "description": "Ask the AI assistant a question with conversation context",
                "usage": f"{COMMAND_PREFIX}ask What is the weather like today?"
            },
            {
                "name": "ask_reset",
                "description": "Reset the AI conversation session and clear history",
                "usage": f"{COMMAND_PREFIX}ask_reset"
            },
            {
                "name": "web_search <query>",
                "description": "Search the web for current information and news",
                "usage": f"{COMMAND_PREFIX}web_search latest technology news"
            },
            {
                "name": "weather <location>",
                "description": "Get current weather information for any location",
                "usage": f"{COMMAND_PREFIX}weather New York"
            },
            {
                "name": "chat_search <query>",
                "description": "Search through your conversation history with the AI",
                "usage": f"{COMMAND_PREFIX}chat_search discussion about games"
            },
            {
                "name": "set_speech_style @user <style>",
                "description": "Set how the AI should speak to a specific user",
                "usage": f"{COMMAND_PREFIX}set_speech_style @user 敬語で話して"
            },
            {
                "name": "set_relationship_request @user <relationship>",
                "description": "Set what kind of relationship the user wants with the AI",
                "usage": f"{COMMAND_PREFIX}set_relationship_request @user お姉さんのように"
            },
            {
                "name": "memory_stats [@user]",
                "description": "Display detailed memory statistics including learned preferences and emotional context",
                "usage": f"{COMMAND_PREFIX}memory_stats @user"
            },
            {
                "name": "interaction_history [@user] [limit]",
                "description": "Show recent interaction history with conversation patterns",
                "usage": f"{COMMAND_PREFIX}interaction_history @user 5"
            },
            {
                "name": "clear_emotions [@user]",
                "description": "Clear emotional context for a user",
                "usage": f"{COMMAND_PREFIX}clear_emotions @user"
            }
        ]
    },
    "music": {
        "title": "Music Player",
        "description": "Full-featured music player with YouTube integration, queue management, and playback controls.",
        "commands": [
            {
                "name": "play <song/url>",
                "description": "Play music from YouTube URL or search for a song",
                "usage": f"{COMMAND_PREFIX}play never gonna give you up"
            },
            {
                "name": "skip",
                "description": "Skip the currently playing song",
                "usage": f"{COMMAND_PREFIX}skip"
            },
            {
                "name": "stop",
                "description": "Stop playback and clear the entire queue",
                "usage": f"{COMMAND_PREFIX}stop"
            },
            {
                "name": "pause",
                "description": "Pause or resume the current song",
                "usage": f"{COMMAND_PREFIX}pause"
            },
            {
                "name": "volume <0-100>",
                "description": "Set playback volume or show current volume",
                "usage": f"{COMMAND_PREFIX}volume 75"
            },
            {
                "name": "queue",
                "description": "Show the current music queue with upcoming songs",
                "usage": f"{COMMAND_PREFIX}queue"
            },
            {
                "name": "disconnect",
                "description": "Disconnect the bot from voice channel",
                "usage": f"{COMMAND_PREFIX}disconnect"
            }
        ]
    },
    "game": {
        "title": "Gaming Utilities",
        "description": "VALORANT utilities, gaming statistics tracking, and leaderboards for competitive play.",
        "commands": [
            {
                "name": "vmap [exclude...]",
                "description": "Pick a random VALORANT map with optional exclusions",
                "usage": f"{COMMAND_PREFIX}vmap Bind Split"
            },
            {
                "name": "vagent [role]",
                "description": "Pick a random VALORANT agent, optionally filtered by role",
                "usage": f"{COMMAND_PREFIX}vagent Duelist"
            },
            {
                "name": "record_win <@user> <kda>",
                "description": "Record a win for a user with their KDA ratio",
                "usage": f"{COMMAND_PREFIX}record_win @user 1.5"
            },
            {
                "name": "record_loss <@user> <kda>",
                "description": "Record a loss for a user with their KDA ratio",
                "usage": f"{COMMAND_PREFIX}record_loss @user 0.8"
            },
            {
                "name": "stats [@user]",
                "description": "Show gaming statistics for yourself or another user",
                "usage": f"{COMMAND_PREFIX}stats @user"
            },
            {
                "name": "leaderboard [stat]",
                "description": "Show gaming leaderboard (wins, winrate, or kda)",
                "usage": f"{COMMAND_PREFIX}leaderboard winrate"
            }
        ]
    },
    "team": {
        "title": "Team Management",
        "description": "Team recruitment, voice channel management, event planning, and community features.",
        "commands": [
            {
                "name": "recruit <game> <members>",
                "description": "Create a team recruitment post with interactive buttons",
                "usage": f"{COMMAND_PREFIX}recruit VALORANT 5"
            },
            {
                "name": "vc <action> [name]",
                "description": "Manage temporary voice channels (create/delete/list)",
                "usage": f"{COMMAND_PREFIX}vc create My Team"
            },
            {
                "name": "teams <count>",
                "description": "Divide voice channel members into random teams",
                "usage": f"{COMMAND_PREFIX}teams 2"
            },
            {
                "name": "poll <question> <options...>",
                "description": "Create an interactive poll with multiple choice options",
                "usage": f"{COMMAND_PREFIX}poll \"Best game?\" VALORANT \"League of Legends\" Minecraft"
            },
            {
                "name": "birthday <action> [date]",
                "description": "Manage birthday notifications (set/remove/list/next)",
                "usage": f"{COMMAND_PREFIX}birthday set 12-25"
            }
        ]
    },
    "utility": {
        "title": "Utility & Tools",
        "description": "General utility commands, reminders, information tools, and bot management features.",
        "commands": [
            {
                "name": "help [category]",
                "description": "Show this help menu or specific category information",
                "usage": f"{COMMAND_PREFIX}help music"
            },
            {
                "name": "ping",
                "description": "Check bot latency and connection status",
                "usage": f"{COMMAND_PREFIX}ping"
            },
            {
                "name": "info",
                "description": "Show detailed bot information and statistics",
                "usage": f"{COMMAND_PREFIX}info"
            },
            {
                "name": "remind <time> <message>",
                "description": "Set a reminder for later (5m, 1h30m, 2d format)",
                "usage": f"{COMMAND_PREFIX}remind 30m Check the oven"
            },
            {
                "name": "quote [message_id] [#channel]",
                "description": "Quote a message by ID or reply to quote",
                "usage": f"{COMMAND_PREFIX}quote 123456789"
            },
            {
                "name": "memo <action> [content]",
                "description": "Manage personal memos (add/list/remove/clear)",
                "usage": f"{COMMAND_PREFIX}memo add \"Meeting notes\" Tomorrow at 3pm"
            },
            {
                "name": "uptime",
                "description": "Show bot uptime and performance statistics",
                "usage": f"{COMMAND_PREFIX}uptime"
            }
        ]
    }
}

# Additional help information
HELP_FOOTER_TEXT = "S.T.E.L.L.A. v2.0 | Smart Team Enhancement & Leisure Learning Assistant"

GENERAL_HELP_INFO = {
    "prefix": COMMAND_PREFIX,
    "support_server": "https://discord.gg/your-support-server",
    "documentation": "https://your-documentation-site.com",
    "github": "https://github.com/your-repo",
    "features": [
        "🤖 AI-powered conversations with memory",
        "🎵 High-quality music streaming from YouTube",
        "🎮 VALORANT utilities and gaming stats",
        "👥 Team management and recruitment tools",
        "🛠️ Comprehensive utility commands",
        "📊 Performance monitoring and analytics",
        "🔒 Privacy-focused with GDPR compliance",
        "⚡ Fast and reliable with 99% uptime"
    ]
}

# Command aliases mapping
COMMAND_ALIASES = {
    "ask": ["ai", "chat"],
    "ask_reset": ["reset_chat", "clear_session"],
    "web_search": ["search", "google"],
    "play": ["p"],
    "skip": ["s"],
    "disconnect": ["dc", "leave"],
    "queue": ["q"],
    "volume": ["vol"],
    "vmap": ["valorant_map", "map"],
    "vagent": ["valorant_agent", "agent"],
    "stats": ["statistics"],
    "leaderboard": ["lb", "top"],
    "recruit": ["lfg", "looking"],
    "voice": ["vc"],
    "teams": ["divide", "split"],
    "help": ["h"],
    "info": ["about", "stats"],
    "remind": ["reminder"],
    "record_win": ["win"],
    "record_loss": ["loss"]
}

# Quick start guide
QUICK_START_GUIDE = {
    "getting_started": [
        f"1. Use `{COMMAND_PREFIX}help` to see all available commands",
        f"2. Try `{COMMAND_PREFIX}play <song>` to start playing music",
        f"3. Use `{COMMAND_PREFIX}ask <question>` to chat with the AI",
        f"4. Create teams with `{COMMAND_PREFIX}recruit <game> <size>`",
        f"5. Get VALORANT utilities with `{COMMAND_PREFIX}vmap` and `{COMMAND_PREFIX}vagent`"
    ],
    "tips": [
        "💡 All commands work in both servers and DMs",
        "💡 Use reaction buttons for easier interaction",
        "💡 The AI remembers context within each channel",
        "💡 Music queue supports YouTube playlists",
        "💡 Gaming stats are tracked automatically"
    ]
}
