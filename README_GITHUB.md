# STELLA Bot

S.T.E.L.L.A. (Smart Team Enhancement & Leisure Learning Assistant) - A comprehensive Discord bot with AI, team management, and automation features.

## Features

- 🤖 **AI Conversation**: Powered by Google Gemini AI
- 👥 **Profile Management**: User profiles and preferences
- 📚 **Knowledge Base**: Guild-specific knowledge storage
- 📅 **Schedule Management**: Event scheduling and reminders
- 📝 **Summary**: Message and conversation summarization
- 🔄 **Automation**: Custom automation rules
- 🗣️ **Speech Patterns**: Mimics speaking styles

## Quick Start

### Prerequisites

- Python 3.8+
- Discord Bot Token
- Google AI API Key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/stella-bot.git
cd stella-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your tokens
```

4. Run the bot:
```bash
python main.py
```

## Environment Variables

Required:
- `DISCORD_BOT_TOKEN`: Your Discord bot token
- `GOOGLE_AI_API_KEY`: Google Gemini API key

Optional:
- `DATABASE_URL`: PostgreSQL connection URL (for data persistence)
- `OPENAI_API_KEY`: OpenAI API key (for advanced features)

## Deployment

### Render

This bot is configured for easy deployment on Render.com:

1. Fork this repository
2. Create a new Web Service on Render
3. Connect your GitHub repository
4. Add environment variables in Render dashboard
5. Deploy!

### UptimeRobot

To keep the bot running 24/7:

1. Sign up at [UptimeRobot](https://uptimerobot.com/)
2. Add a new monitor with your Render URL
3. Set check interval to 5 minutes

## Commands

- `/ask [question]` - Ask the AI a question
- `/chat [message]` - Have a natural conversation
- `/profile` - Manage your profile
- `/schedule` - Schedule management
- And more!

## License

This project is licensed under the MIT License.

## Support

For issues and questions, please open an issue on GitHub.
