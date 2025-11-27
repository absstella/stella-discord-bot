# VOICEVOX Engine Setup Guide

## ローカル環境での起動

### 方法1: Docker Compose（推奨）
```bash
# VOICEVOX Engineを起動
docker-compose -f docker-compose.voicevox.yml up -d

# 確認
curl http://localhost:50021/version

# 停止
docker-compose -f docker-compose.voicevox.yml down
```

### 方法2: Docker直接実行
```bash
docker pull voicevox/voicevox_engine:cpu-ubuntu20.04-latest
docker run --rm -p 50021:50021 voicevox/voicevox_engine:cpu-ubuntu20.04-latest
```

## クラウド環境でのデプロイ

### AWS (ECS/Fargate)
1. ECRにイメージをプッシュ（またはDocker Hubから直接）
2. ECSタスク定義を作成
3. ポート50021を公開
4. Botの環境変数 `VOICEVOX_HOST` を設定

### Google Cloud (Cloud Run)
```bash
# Cloud Runにデプロイ
gcloud run deploy voicevox-engine \
  --image voicevox/voicevox_engine:cpu-ubuntu20.04-latest \
  --port 50021 \
  --platform managed \
  --region asia-northeast1 \
  --allow-unauthenticated
```

### Azure (Container Instances)
```bash
az container create \
  --resource-group myResourceGroup \
  --name voicevox-engine \
  --image voicevox/voicevox_engine:cpu-ubuntu20.04-latest \
  --ports 50021 \
  --dns-name-label voicevox-unique
```

## Botの設定

### 環境変数
`.env`ファイルに追加：
```
VOICEVOX_HOST=localhost
VOICEVOX_PORT=50021
```

クラウド環境では：
```
VOICEVOX_HOST=your-voicevox-service.com
VOICEVOX_PORT=50021
```

## 動作確認

1. VOICEVOX Engineが起動していることを確認：
```bash
curl http://localhost:50021/speakers
```

2. Botを起動
3. `!voice` コマンドで状態確認
4. `!speak こんにちは` でテスト

## トラブルシューティング

### Botが VOICEVOX を検出しない
- VOICEVOX Engineが起動しているか確認
- ポート50021が開いているか確認
- ファイアウォール設定を確認

### 音声が生成されない
- ログを確認: `docker logs voicevox_engine`
- メモリ不足の可能性（最低2GB推奨）

## パフォーマンス

- **CPU版**: 1音声あたり1-3秒
- **GPU版**: 1音声あたり0.5-1秒（NVIDIA GPU必要）

GPU版を使う場合は `docker-compose.voicevox.yml` のコメントを解除してください。
