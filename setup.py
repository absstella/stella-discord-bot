#!/usr/bin/env python3
'''
S.T.E.L.L.A. 全機能版セットアップスクリプト
'''

import subprocess
import sys
import os

def install_requirements():
    '''依存関係をインストール'''
    print("依存関係をインストール中...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def setup_environment():
    '''環境設定'''
    print("\n=== S.T.E.L.L.A. 全機能版セットアップ ===")
    print("\n必要な環境変数:")
    print("- DISCORD_BOT_TOKEN: Discord Bot Token")
    print("- GOOGLE_AI_API_KEY: Google Gemini API Key")
    print("- OPENAI_API_KEY: OpenAI API Key (オプション)")
    print("- DATABASE_URL: PostgreSQL接続URL (オプション)")
    
    print("\n使用方法:")
    print("1. 環境変数を設定")
    print("2. python main.py でボットを起動")
    
if __name__ == "__main__":
    try:
        install_requirements()
        setup_environment()
        print("\n✅ セットアップ完了！")
    except Exception as e:
        print(f"❌ エラー: {e}")
