# 月夜の狼チャット 🐺

ビッグファイブ性格診断に基づいてトーンが変化する、2D アバター付き会話 AI チャットアプリです。

## スクリーンショット

| セットアップ | 性格診断 | チャット |
|---|---|---|
| APIキー入力・狼アバター | 20問 Likert スケール | 性格反映応答 + アバター感情 |

---

## アーキテクチャ

```
frontend (Vue 3 + Vite)          backend (FastAPI + SQLite)
  ├── SetupView      ─────────► POST /auth/register
  ├── QuizView       ─────────► GET  /personality/questions
  │                            POST /personality/submit
  └── ChatView       ─────────► POST /chat/send  (Google Gemini)
                               GET  /chat/history/{user_id}
                               DELETE /chat/history/{user_id}
```

**認証**: 匿名（クライアント生成 UUID）  
**暗号化**: Fernet（ユーザーID + サーバーシークレットから PBKDF2 で鍵導出）  
**LLM**: Google Gemini 1.5 Flash  
**デプロイ**: バックエンド → Render.com 無料枠、フロントエンド → Vercel 無料枠

---

## クイックスタート

### 前提条件

- Python 3.12+
- Node.js 20+
- [Google AI Studio の API キー](https://aistudio.google.com/app/apikey)

### バックエンド

```bash
cd backend
cp .env.example .env          # SECRET_KEY を変更してください
pip install -r requirements.txt
uvicorn app.main:app --reload
# → http://localhost:8000
```

### フロントエンド

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
# → http://localhost:5173
```

### アバター画像の配置

`frontend/public/avatar.png` に狼の画像を配置してください。  
表情ステート（通常・喜び・悲しみ・考え中）はCSSフィルターとSVGオーバーレイで表現されます。

---

## テスト

```bash
cd backend
pytest --tb=short -q
```

テスト内容:
- `test_personality.py`: ビッグファイブ重み計算・クイズAPIエンドポイント・ユーザー登録
- `test_encryption.py`: 暗号化/復号ラウンドトリップ・異ユーザーによる復号不可

---

## ⚡ ワンクリックデプロイ

GitHubにリポジトリをpushしたら、以下の2ステップだけで公開できます。
（`YOUR_GH_USER/YOUR_REPO` は自分のリポジトリに置き換えてください）

### 1. バックエンド → Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/YOUR_GH_USER/YOUR_REPO)

ボタンを押すと `render.yaml` が自動読込され、`SECRET_KEY` の生成・永続ディスク・ヘルスチェックまで設定済みで構築されます。
`ALLOWED_ORIGINS` だけ後で入力（下記手順3）。

### 2. フロントエンド → Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/YOUR_GH_USER/YOUR_REPO&root-directory=frontend&env=VITE_API_URL&envDescription=RenderのバックエンドURL)

Root Directory は `frontend` が自動指定されます。`VITE_API_URL` にRenderのURL（例: `https://personality-chat-api.onrender.com`）を入力。

### 3. 最後に接続（1分）

Vercelが発行したURL（例: `https://your-app.vercel.app`）をRenderの環境変数
`ALLOWED_ORIGINS` に `["https://your-app.vercel.app"]` の形式で入力 → 自動再デプロイで完了。

> 💡 push後のGitHub Actionsで自動デプロイしたい場合のみ、下記のSecrets設定が必要です。ワンクリックデプロイだけなら不要です。

---

## デプロイ手順（詳細）

### バックエンド → Render.com

1. [render.com](https://render.com) でアカウント作成
2. New → Web Service → Connect GitHub repo
3. **Root Directory**: `backend`
4. **Build Command**: `pip install -r requirements.txt`
5. **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Environment Variables を設定:
   - `SECRET_KEY` = ランダムな32文字以上の文字列
   - `ALLOWED_ORIGINS` = `["https://your-app.vercel.app"]`
7. Persistent Disk を追加 → Mount Path: `/data`
8. **Settings → Deploy Hook URL** をコピーして GitHub Secrets `RENDER_DEPLOY_HOOK_URL` に設定

### フロントエンド → Vercel

1. [vercel.com](https://vercel.com) でアカウント作成
2. Import → GitHub repo
3. **Root Directory**: `frontend`
4. Environment Variable: `VITE_API_URL` = `https://your-backend.onrender.com`
5. デプロイ後に表示される URL を Render の `ALLOWED_ORIGINS` に追加
6. GitHub Secrets を設定:
   - `VERCEL_TOKEN`: Vercel アカウント設定から取得
   - `VERCEL_ORG_ID`: `.vercel/project.json` の `orgId`
   - `VERCEL_PROJECT_ID`: `.vercel/project.json` の `projectId`

### GitHub Actions CI/CD

`.github/workflows/ci-cd.yml` が以下を自動実行します:
- **PR 時**: バックエンドテスト + フロントエンドビルド
- **main マージ時**: 上記 + Render デプロイ + Vercel デプロイ

---

## 性格診断モデル

| 特性 | 英語名 | 高い場合 | 低い場合 |
|------|--------|---------|---------|
| 開放性 | Openness | 好奇心旺盛・思索的 | 実用的・慣習的 |
| 誠実性 | Conscientiousness | 丁寧語・構造的 | カジュアル・フレンドリー |
| 外向性 | Extraversion | 明るく積極的 | 落ち着いて簡潔 |
| 協調性 | Agreeableness | 共感・寄り添い | 率直・論理的 |
| 神経症傾向 | Neuroticism | 感情配慮・励まし | 事実重視・淡々 |

20問（各特性4問）× Likert 1〜5 → 逆転採点後に 0.0〜1.0 正規化

詳細スキーマ: [`personality_schema.json`](./personality_schema.json)

---

## LLM プロンプト

`backend/app/services/llm.py` の `SYSTEM_PROMPT_TEMPLATE` を参照。  
応答の先頭に `[STATE:happy]` 等を出力させ、アバター状態を制御します。

---

## プライバシー・セキュリティ

- 会話履歴は Fernet 暗号化して SQLite に保存
- ユーザー削除ボタンで全履歴を即時削除可能
- Google AI API キーはブラウザの localStorage にのみ保存（サーバーに保存しない）
- 匿名 UUID はブラウザ外に漏洩しない

---

## ライセンス

MIT
