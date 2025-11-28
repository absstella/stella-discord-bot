# STELLA Bot - GitHub & Render Deployment Guide

## 📋 次のステップ

### 1. GitHubリポジトリの作成

1. [GitHub](https://github.com)にアクセスしてログイン
2. 右上の「+」→「New repository」をクリック
3. リポジトリ名を入力（例: `stella-discord-bot`）
4. 「Public」または「Private」を選択
5. **「Initialize this repository with a README」のチェックを外す**（既にローカルにファイルがあるため）
6. 「Create repository」をクリック

### 2. ローカルリポジトリをGitHubにプッシュ

GitHubでリポジトリを作成したら、以下のコマンドを実行:

```powershell
cd "c:/Users/swamp/OneDrive/デスクトップ/stella_all_in_one_20250614_201902/stella_bot"

# GitHubリポジトリのURLを設定（YOUR_USERNAMEとREPO_NAMEを置き換える）
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# メインブランチにリネーム
git branch -M main

# GitHubにプッシュ
git push -u origin main
```

### 3. Renderでのデプロイ

1. [Render](https://render.com)にアクセスしてログイン（GitHubアカウントでサインアップ推奨）
2. ダッシュボードで「New +」→「Web Service」をクリック
3. 「Connect a repository」でGitHubリポジトリを選択
4. 以下の設定を入力:
   - **Name**: `stella-bot`（任意）
   - **Region**: `Oregon (US West)`（無料プランで利用可能）
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Instance Type**: `Free`

5. 「Environment Variables」セクションで以下を追加:
   - `DISCORD_BOT_TOKEN`: `YOUR_DISCORD_BOT_TOKEN`
   - `GEMINI_API_KEY`: `YOUR_GEMINI_API_KEY`

6. 「Create Web Service」をクリック

### 4. UptimeRobotでの監視設定

1. [UptimeRobot](https://uptimerobot.com)にアクセスしてサインアップ
2. 「Add New Monitor」をクリック
3. 以下の設定を入力:
   - **Monitor Type**: `HTTP(s)`
   - **Friendly Name**: `STELLA Bot`
   - **URL**: Renderのデプロイ後に表示されるURL（例: `https://stella-bot.onrender.com`）
   - **Monitoring Interval**: `5 minutes`

4. 「Create Monitor」をクリック

### 5. Replitでの24時間稼働設定 (現在の環境)

ReplitでBotを常時起動させるには、以下の手順を行います。

1.  **Webサーバーの確認**:
    - 既に `keep_alive.py` が組み込まれており、Bot起動時にWebサーバーも立ち上がります。
    - Replitの画面右上に「WebView」という小さなウィンドウが表示され、URL（例: `https://stella-discord-bot--swampchihaya.repl.co`）が表示されているはずです。このURLをコピーします。

2.  **UptimeRobotの設定**:
    - [UptimeRobot](https://uptimerobot.com)にログイン。
    - 「Add New Monitor」をクリック。
    - **Monitor Type**: `HTTP(s)`
    - **Friendly Name**: `STELLA Replit`
    - **URL**: 先ほどコピーしたReplitのURL
    - **Monitoring Interval**: `5 minutes`
    - 「Create Monitor」をクリック。

これで、UptimeRobotが5分ごとにReplitのWebサーバーにアクセスし、Botがスリープするのを防ぎます。


## ⚠️ 重要な注意事項

### Renderの無料プランの制限
- **自動スリープ**: 15分間アクティビティがないとスリープ状態になります
- **起動時間**: スリープから復帰するのに数十秒かかります
- **月間稼働時間**: 750時間/月（約31日）まで無料

### UptimeRobotの役割
- 5分ごとにBotにアクセスしてスリープを防ぐ
- ダウンタイムを検知してアラートを送信
- アップタイム統計を記録

### Discord Botの設定
Discord Developer Portalで以下を確認:
- Bot TokenがコピーされていることRenderの環境変数に正しく設定されていること
- Botがサーバーに招待されていること
- 必要な権限（Message Content Intent）が有効になっていること

## 🎉 完了後の確認

1. **Renderのログを確認**:
   - デプロイが成功しているか
   - エラーがないか
   - Botがオンラインになっているか

2. **Discordで動作確認**:
   - Botがオンライン状態か
   - `/ask`コマンドが動作するか

3. **UptimeRobotで監視確認**:
   - モニターが正常に動作しているか
   - アップタイムが記録されているか

## 📞 トラブルシューティング

### Renderでデプロイが失敗する場合
- ログを確認して依存関係のエラーがないか確認
- 環境変数が正しく設定されているか確認
- `requirements.txt`が正しいか確認

### Botがオンラインにならない場合
- Discord Bot Tokenが正しいか確認
- Renderのログでエラーメッセージを確認
- Discord Developer PortalでMessage Content Intentが有効か確認

### UptimeRobotが動作しない場合
- RenderのURLが正しいか確認
- Renderのサービスが起動しているか確認
