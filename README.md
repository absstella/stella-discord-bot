# S.T.E.L.L.A. 全機能版

エクスポート日時: 2025-06-14 20:11:04

## 機能
- 高度なAI会話システム（Gemini + OpenAI対応）
- ユーザープロファイル管理と関係性分析
- 自動学習とパーソナライゼーション
- チーム管理とスケジュール機能
- 音声認識対応（オプション）
- ゲームとエンターテイメント機能

## セットアップ

1. 依存関係のインストール:
```bash
python setup.py
```

2. 環境変数を設定:
```bash
export DISCORD_BOT_TOKEN="your_discord_token"
export GOOGLE_AI_API_KEY="your_gemini_api_key"
export OPENAI_API_KEY="your_openai_key"  # オプション
```

3. ボットを起動:
```bash
python main.py
```

## 必要な環境変数
- `DISCORD_BOT_TOKEN`: Discord Developer Portalで取得
- `GOOGLE_AI_API_KEY`: Google AI Studioで取得
- `OPENAI_API_KEY`: OpenAI APIキー（オプション）
- `DATABASE_URL`: PostgreSQL接続URL（オプション）

## ファイル構成
- `main.py`: メインエントリーポイント
- `cogs/`: Discord bot機能モジュール
- `utils/`: ユーティリティ関数
- `data/`: 設定データとプロファイル
- `database/`: データベース関連
- `views/`: UI コンポーネント

## サポート
このシステムはReplitで開発されたS.T.E.L.L.A. Discord botの完全版です。
