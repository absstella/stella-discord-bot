# STELLA Bot コマンド一覧

STELLA Botで利用可能な全コマンドの機能別一覧です。（2025/12/04 更新）

## 🤖 基本機能 & AI

| コマンド | タイプ | 説明 |
| :--- | :--- | :--- |
| `/help` | Slash | インタラクティブなヘルプメニューを表示します。 |
| `/ask` | Slash | 対話型AIインターフェース（暗黙的）。 |
| `/image` | Slash | 画像生成を行います。 |
| `/analyze` | Slash | 画像解析を行います（画像を添付して使用）。 |
| `/mood` | Slash | 現在の感情状態を表示します。 |
| `/profile` | Slash | ユーザープロファイルを表示します。 |
| `/remember` | Slash | ユーザー情報を記憶させます。 |
| `/ai_relationship` | Slash | AIとの関係性を表示します。 |

## ⛏️ Minecraft連携

| コマンド | タイプ | 説明 |
| :--- | :--- | :--- |
| `/mcstatus [address]` | Hybrid | サーバーのステータスを確認します。 |
| `/mc chat [message]` | Slash | サーバーにチャットを送信します。 |
| `/mc whitelist [action] [user]` | Slash | ホワイトリストを管理します (add/remove/list)。 |
| `/mc command [cmd]` | Slash | [Admin] 任意のコマンドを実行します。 |

## 🃏 サーバーガチャ

| コマンド | タイプ | 説明 |
| :--- | :--- | :--- |
| `/gacha pull [count]` | Slash | ガチャを引きます（1回/10回）。演出付き！ |
| `/gacha daily` | Slash | 毎日1回、1000 SPを受け取ります。 |
| `/gacha list` | Slash | 獲得したカード/アイテムを確認します。 |
| `/gacha ranking` | Slash | コレクターランキングを表示します。 |
| `/gacha help` | Slash | ポイントの稼ぎ方やシステムの説明を表示します。 |
| `/gacha_battle [opponent]` | Slash | 手持ちのカードでユーザーと対戦します。 |
| `/gacha_add_card` | Slash | [Admin] カスタムカード（内輪ネタなど）を追加します。 |


## 🎮 ゲーム便利機能

| コマンド | タイプ | 説明 |
| :--- | :--- | :--- |
| `/boshu [game] [count] [time]` | Hybrid | ゲームの募集投稿を作成します。 |
| `/teams [count] [mode]` | Hybrid | VCメンバーをチーム分けします。 |
| `/pick_map [game]` | Hybrid | ランダムにマップを選択します (Val, Apex, OW2)。 |
| `/pick_agent [game]` | Hybrid | ランダムにエージェントを選択します。 |
| `/strat [game]` | Hybrid | ランダムな戦略/縛りプレイを提案します。 |
| `/create_tournament [players]` | Hybrid | 簡易トーナメント表を作成します。 |
| `/scrim_poll [dates]` | Hybrid | スクリムの日程調整用投票を作成します。 |
| `/clip [url] [title]` | Hybrid | ゲームクリップを保存します。 |
| `/top_clips` | Hybrid | 最近のゲームクリップを表示します。 |
| `/coach [question]` | Hybrid | AIコーチにゲームのアドバイスを求めます。 |
| `/start_bet [title]` | Hybrid | 勝敗予想ベットを開始します。 |
| `/sens [from] [val] [to]` | Hybrid | ゲーム間の感度を変換します。 |
| `/add_term [word] [meaning]` | Hybrid | サーバーWikiに用語を追加します。 |
| `/whatis [word]` | Hybrid | サーバーWikiで用語を検索します。 |
| `/jinrou create` | Slash | 人狼ゲームを作成します。 |
| `/colosseum challenge [user]` | Slash | ペルソナコロシアムで対戦します。 |
| `/akinator` | Slash | アキネイターゲームを開始します。 |
| `/wordwolf start` | Slash | ワードウルフゲームを開始します。 |

## 🛠️ ユーティリティ & ツール

| コマンド | タイプ | 説明 |
| :--- | :--- | :--- |
| `/schedule create [title] [dates]` | Hybrid | 日程調整投票を作成します。 |
| `/stock market` | Hybrid | メンバー株価市場を表示します。 |
| `/stock buy/sell` | Hybrid | メンバー株を売買します。 |
| `/stock portfolio` | Hybrid | 保有株と資産を表示します。 |
| `/calc [expression]` | Hybrid | 数式を計算します。 |
| `/plot [data]` | Hybrid | データをグラフ化します。 |
| `/exec [code]` | Hybrid | Pythonコードを実行します（制限付き）。 |
| `/join` | Hybrid | VCに参加します。 |
| `/leave` | Hybrid | VCから退出します。 |
| `/speak [text]` | Hybrid | テキストを読み上げます。 |
| `/voice` | Hybrid | 音声設定を表示します。 |

## 🤡 いたずら (Prank)

| コマンド | タイプ | 説明 |
| :--- | :--- | :--- |
| `/prank mimic start/stop` | Slash | オウム返しを開始/停止します。 |
| `/prank roulette start/stop` | Slash | リアクションルーレットを開始/停止します。 |
| `/prank typing start/stop` | Slash | 無限入力中表示を開始/停止します。 |
| `/prank possess start/stop` | Slash | 憑依モード（DMで操作）を開始/停止します。 |
| `/prank shadow_clone start/stop` | Slash | 影分身モードを開始/停止します。 |
| `/prank mind_control add/remove` | Slash | 発言置換（マインドコントロール）を設定します。 |
| `/prank identity copy/steal/reset` | Slash | ニックネームをコピー/奪取/リセットします。 |
| `/impersonate [user] [msg]` | Slash | ユーザーになりすまして発言します（Webhook）。 |
| `/prank fake_error` | Slash | 偽のシステムエラーを表示します。 |
| `/prank ghost_ping` | Slash | ゴーストメンションを送ります。 |
| `/prank fake_nitro` | Slash | 偽のNitroリンクを送ります。 |
| `/prank puppet` | Slash | ユーザーを操って発言させます。 |
| `/prank ghost_whisper` | Slash | VCにささやき声を流します。 |

## 📻 その他

| コマンド | タイプ | 説明 |
| :--- | :--- | :--- |
| `/start_radio` | Slash | ラジオ放送を開始します。 |
| `/scoop` | Slash | タブロイド記事を生成します。 |
| `/parasite start` | Slash | 寄生モードを開始します。 |
| `/observer start` | Slash | 観察モードを開始します。 |
| `/riddle` | Slash | なぞなぞ「ファウストの試練」を開始します。 |
