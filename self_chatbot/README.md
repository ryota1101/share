# Multi-LLM Chat

複数のLLM（Azure OpenAI / GCP Gemini / AWS Claude 等）を統合的に利用できるチャットアプリケーションです。

## 🚀 クイックスタート

### 1. 環境設定

```bash
# リポジトリをクローン
git clone <repository-url>
cd multi-llm-chat

# セットアップスクリプトを実行
chmod +x setup.sh
./setup.sh

# 環境変数を設定（必須）
cp .env.example .env
# .envファイルを編集してAPIキーを設定
```

### 2. APIキーの設定

`.env`ファイルに以下のAPIキーを設定してください：

```bash
# Azure OpenAI
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# Google Gemini
GCP_GEMINI_API_KEY=your_gemini_api_key_here

# AWS Claude
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_REGION=us-east-1
```

### 3. アプリケーション起動

```bash
# Docker Composeでアプリケーションを起動
docker-compose up --build

# またはバックグラウンドで実行
docker-compose up -d --build
```

### 4. アクセス

- **フロントエンド**: http://localhost:3000
- **バックエンドAPI**: http://localhost:5000
- **データベース**: localhost:5432

## 🏗️ アーキテクチャ

### インフラ構成

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Database      │
│   (Next.js)     │◄──►│   (Flask)       │◄──►│  (PostgreSQL)   │
│   Port: 3000    │    │   Port: 5000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### ディレクトリ構造

```
multi-llm-chat/
├── docker-compose.yml          # Docker Compose設定
├── .env.example               # 環境変数テンプレート
├── init.sql                   # データベース初期化
├── setup.sh                   # セットアップスクリプト
├── config/
│   └── models.yaml           # AIモデル設定
├── backend/                   # Flask API
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app.py                # メインアプリケーション
│   ├── models/               # データベースモデル
│   ├── routes/               # APIルート
│   └── utils/                # ユーティリティ
├── frontend/                  # Next.js アプリ
│   ├── Dockerfile
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── components/           # Reactコンポーネント
│   ├── pages/                # ページファイル
│   └── styles/               # スタイルファイル
└── logs/                      # ログファイル
```

## ⚙️ 設定管理

### AIモデルの追加

`config/models.yaml`を編集することで新しいAIモデルを追加できます：

```yaml
models:
  - name: "new-model"
    display_name: "新しいモデル"
    provider: "provider_name"
    model_id: "actual_model_id"
    capabilities:
      text_input: true
      image_input: false
      image_output: false
      streaming: true
    settings:
      max_tokens: 4000
      temperature: 0.7
      top_p: 1.0
    description: "モデルの説明"
```

### 対応プロバイダー

- **Azure OpenAI**: GPT-4, GPT-4 Turbo, GPT-3.5 Turbo
- **Google Gemini**: Gemini Pro, Gemini Pro Vision
- **AWS Claude**: Claude 3 Opus, Claude 3 Sonnet, Claude 3 Haiku

## 🗄️ データベース

PostgreSQLを使用してチャット履歴を管理します。

### テーブル構造

- `chat_sessions`: チャットセッション情報
- `chat_messages`: メッセージ履歴（テキスト・画像）

### 主な機能

- 履歴の永続化
- セッション管理
- お気に入り機能
- 画像データの保存（Base64）

## 🔧 開発環境

### バックエンド開発

```bash
cd backend
pip install -r requirements.txt
python app.py
```

### フロントエンド開発

```bash
cd frontend
npm install
npm run dev
```

### データベース接続

```bash
# PostgreSQLに接続
docker exec -it multi-llm-chat-db psql -U chatuser -d multi_llm_chat
```

## 🛠️ トラブルシューティング

### 一般的な問題

1. **APIキーエラー**
   - `.env`ファイルでAPIキーが正しく設定されているか確認

2. **データベース接続エラー**
   - PostgreSQLコンテナが正常に起動しているか確認
   - `docker-compose logs db`でログを確認

3. **ポート競合**
   - 3000, 5000, 5432番ポートが他のプロセスで使用されていないか確認

### ログ確認

```bash
# 全サービスのログ
docker-compose logs

# 特定サービスのログ
docker-compose logs frontend
docker-compose logs backend
docker-compose logs db
```

### データベースリセット

```bash
# データベースを完全にリセット
docker-compose down -v
docker-compose up --build
```

## 📝 今後の開発計画

- [ ] バックエンドAPI実装
- [ ] フロントエンドUI実装
- [ ] ストリーミング機能
- [ ] 画像入力/出力対応
- [ ] チャット履歴検索
- [ ] 複数セッション同時利用
- [ ] RAG機能（ファイル処理）

## 📄 ライセンス

MIT License

## 🤝 コントリビューション

Issue や Pull Request を歓迎します！

---

**注意**: 本アプリケーションは個人利用を想定しており、APIキーなどの機密情報は適切に管理してください。