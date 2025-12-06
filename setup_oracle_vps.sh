#!/bin/bash

# STELLA Bot Setup Script for Oracle Cloud (Ubuntu)
# Usage: ./setup_oracle_vps.sh

echo "🚀 Starting STELLA Bot Setup..."

# 1. Update System
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# 2. Install Dependencies
echo "🛠️ Installing dependencies (Python, FFmpeg, Git)..."
sudo apt install -y python3 python3-pip python3-venv ffmpeg git tmux build-essential libffi-dev python3-dev

# 3. Clone Repository (if not already cloned)
# Assuming the script is run inside the desired directory or we create one
INSTALL_DIR=~/stella_bot

if [ -d "$INSTALL_DIR" ]; then
    echo "📂 Directory $INSTALL_DIR already exists. Pulling latest changes..."
    cd $INSTALL_DIR
    git pull
else
    echo "📂 Cloning repository..."
    # Replace with your actual repo URL
    echo "⚠️ Please enter your GitHub Repository URL (e.g., https://github.com/username/repo.git):"
    read REPO_URL
    git clone $REPO_URL $INSTALL_DIR
    cd $INSTALL_DIR
fi

# 4. Setup Virtual Environment
echo "🐍 Setting up Python Virtual Environment..."
python3 -m venv venv
source venv/bin/activate

# 5. Install Python Requirements
echo "📥 Installing Python libraries..."
pip install --upgrade pip
pip install -r requirements.txt

# 6. Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    echo "⚠️ Please enter your Discord Bot Token:"
    read BOT_TOKEN
    echo "DISCORD_BOT_TOKEN=$BOT_TOKEN" > .env
    echo "DATABASE_URL=postgresql://user:password@localhost/dbname" >> .env
    echo "GEMINI_API_KEY=" >> .env
    echo "OPENAI_API_KEY=" >> .env
    echo "✅ .env file created. Please edit it later to add other keys."
fi

# 7. Create Systemd Service (for 24/7 uptime)
echo "⚙️ Creating Systemd Service..."
SERVICE_FILE=/etc/systemd/system/stella.service
CURRENT_USER=$(whoami)

sudo bash -c "cat > $SERVICE_FILE" <<EOF
[Unit]
Description=STELLA Discord Bot
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable stella
sudo systemctl start stella

echo "🎉 Setup Complete!"
echo "Check status with: sudo systemctl status stella"
echo "View logs with: journalctl -u stella -f"
