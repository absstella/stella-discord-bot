# Oracle Cloud Deployment Guide for STELLA

**Oracle Cloud Free Tier** を使って、STELLA Botを完全無料で24時間稼働させるための手順書です。

## 手順1: アカウント作成とインスタンス構築

1.  **アカウント作成**:
    *   [Oracle Cloud Free Tier](https://www.oracle.com/jp/cloud/free/) からアカウントを作成します。
    *   ※クレジットカード登録が必要ですが、有料枠を使わない限り請求は来ません。
    *   **ホームリージョン**（データの置き場所）は、自分が住んでいる場所に近いところ（例: Japan East (Tokyo)）を選んでください。**後から変更できません。**

2.  **VMインスタンス（サーバー）の作成**:
    *   ログイン後、「コンピュート・インスタンスの作成」をクリック。
    *   **名前**: 好きな名前（例: `stella-bot-server`）
    *   **Image and Shape (重要)**:
        *   **Image**: `Canonical Ubuntu` (バージョンは 22.04 または 24.04) を選択。
        *   **Shape**: `Ampere` (VM.Standard.A1.Flex) を選択。
            *   これが**最強の無料枠**です（4 OCPU, 24GB RAM）。
            *   もし「Out of capacity」と言われたら、AMD (VM.Standard.E2.1.Micro) を選んでください（性能は落ちますがBotには十分です）。
    *   **Add SSH keys (超重要)**:
        *   `Save private key` をクリックして、`.key` ファイルをダウンロードし、**絶対に無くさないように保存してください**。これがサーバーの鍵です。
    *   「Create」をクリックして完了！

## 手順2: サーバーへの接続

Windowsの場合、PowerShellまたは「Termius」などのアプリを使います。

1.  **IPアドレスの確認**:
    *   Oracle Cloudの画面で、作成したインスタンスの `Public IP Address` をコピーします。
2.  **接続 (PowerShellの場合)**:
    *   ダウンロードした鍵ファイル（例: `ssh-key-2024.key`）がある場所で以下を実行：
    ```powershell
    # 鍵の権限設定が必要な場合があります
    ssh -i "path/to/your/key.key" ubuntu@<IPアドレス>
    ```
    *   「Are you sure...?」と聞かれたら `yes` と入力。

## 手順3: Botのセットアップ

サーバーに入れたら（黒い画面で `ubuntu@...` と表示されたら）、以下の手順でBotを動かします。

1.  **セットアップスクリプトの作成**:
    *   以下のコマンドをコピー＆ペーストして実行します。
    ```bash
    nano setup.sh
    ```
    *   開いた画面に、このプロジェクトにある `setup_oracle_vps.sh` の中身を全てコピーして貼り付けます。
    *   `Ctrl + O` → `Enter` で保存、`Ctrl + X` で終了。

2.  **スクリプトの実行**:
    ```bash
    chmod +x setup.sh
    ./setup.sh
    ```
    *   途中、GitHubのリポジトリURLやBot Tokenを聞かれるので入力してください。

3.  **完了！**:
    *   スクリプトが完了すると、Botが自動的に起動し、24時間稼働状態になります。
    *   ログを見るには: `journalctl -u stella -f`

## 補足: ファイルの更新方法

Botのコードを更新したいときは、サーバーに入って以下を実行するだけです：

```bash
cd ~/stella_bot
git pull
sudo systemctl restart stella
```
