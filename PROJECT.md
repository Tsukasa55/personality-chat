# 月夜の狼チャット — プロジェクト引き継ぎ資料

別スレッド／別セッションで続きを行うための、現状・構成・再開手順のまとめ。
（最終更新: 2026-08-15）

---

## 1. 概要

ビッグファイブ性格モデルで「アバター（月夜の狼）の性格」を設定し、その性格＋物語背景に
基づいてトーンが変化する会話AIチャット。フロントVue3 + バックFastAPI + Google Gemini。

- 性格診断=**ユーザーではなく狼（アバター）の性格を決める**もの（重要な設計前提）
- チャットは新しい発言が下・自分の発言の下に相手の返答
- 「物語・背景」欄に世界観/関係性を記述でき、会話に応じて数ターンごとに自動更新
- 会話履歴・背景はFernetで暗号化してSQLiteに保存、ユーザーが削除可

---

## 2. 本番URL（稼働中）

- フロント: https://personality-chat-one.vercel.app
- バックAPI: https://personality-chat-api.onrender.com
- ヘルスチェック: https://personality-chat-api.onrender.com/health → `{"status":"ok"}`
- 質問一覧: https://personality-chat-api.onrender.com/personality/questions

---

## 3. リポジトリ / ローカル

- **正リポジトリ**: https://github.com/Tsukasa55/personality-chat （main ブランチ）
- ローカル: `C:\Users\tsuka\Desktop\work\develop\personality-chat`
- 注意: `family-budget-app` は**別プロジェクト**。初期に誤って push したが、追加した main ブランチは削除済み。今後このプロジェクトでは触らない。

---

## 4. ホスティング構成

### Vercel（フロントエンド）
- プロジェクト: `personality-chat`（tsukasa55s-projects, Hobby/無料）
- 接続リポ: Tsukasa55/personality-chat
- Root Directory: `frontend`
- ビルド: `vite build`（型チェックvue-tscは外してある）
- 環境変数: `VITE_API_URL = https://personality-chat-api.onrender.com`
- main への push で自動デプロイ

### Render（バックエンド）
- サービス: `personality-chat-api`（無料枠, Oregon）
- 接続リポ: Tsukasa55/personality-chat / branch `main`
- Runtime: **Python 3**（Dockerではない）
- Root Directory: `backend`
- Build: `pip install -r requirements.txt`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- 環境変数:
  - `PYTHON_VERSION = 3.12.7`（← これが無いと最新Pythonでビルド失敗する）
  - `SECRET_KEY`（Render自動生成、暗号鍵の素）
  - `DATABASE_URL = sqlite+aiosqlite:///./chat.db`
  - `ALLOWED_ORIGINS = ["https://personality-chat-one.vercel.app"]`（CORS）
- main への push で自動デプロイ
- ⚠ 無料枠は永続ディスク非対応 → **SQLiteは一時保存。再起動/スリープで会話履歴・背景はリセット**される。永続化するなら無料Neon PostgresへDATABASE_URL変更（未実施）。
- ⚠ 無料枠はアクセスが無いとスリープ。次回起動に約50秒かかる。

---

## 5. LLM

- Google Gemini。APIキーは**ユーザーが最初の画面で入力**（localStorage保存、サーバーに保存しない）。
- モデルは廃止対策でフォールバック順に試す（`backend/app/services/llm.py` の `MODEL_CANDIDATES`）:
  `gemini-2.5-flash` → `gemini-2.0-flash` → `gemini-flash-latest` → `gemini-1.5-flash-latest`
- ※ `gemini-1.5-flash` は廃止済み（過去にこれで404エラーが出た）。

---

## 6. 主要ファイル

```
backend/
  app/
    main.py                 # FastAPIエントリ、CORS、ルート登録、init_db
    config.py               # 設定（SECRET_KEY, DATABASE_URL, ALLOWED_ORIGINS…）
    database.py             # 非同期SQLAlchemy、init_dbでcreate_all
    models.py               # User / PersonalityProfile / Message / Background
    schemas.py              # Pydanticスキーマ
    routes/
      auth.py               # 匿名登録(UUID)
      personality.py        # 質問取得 / 診断送信 / プロフィール取得
      chat.py               # /chat/send 送受信・履歴・削除・背景自動更新
      background.py         # /background GET・PUT（手動編集）
    services/
      personality.py        # 20問→ビッグファイブ重み。QUIZ_QUESTIONSは狼の性格を選ぶ文言
      llm.py                # Gemini応答生成＋背景自動更新（update_background）
      encryption.py         # Fernet（user_id+SECRET_KEYからPBKDF2で鍵導出）
  requirements.txt
  Dockerfile                # 使用していない（RenderはPython3ランタイム）
  render.yaml               # Blueprint（現在はサービス直接設定で運用）
frontend/
  src/
    main.ts, App.vue
    api.ts                  # APIクライアント
    stores/ (user.ts, chat.ts)
    views/ (SetupView.vue, QuizView.vue, ChatView.vue)
    components/ (WolfAvatar.vue, MessageBubble.vue)
  public/avatar.png         # 狼アバター画像
  vercel.json               # SPAルーティング
personality_schema.json     # 性格重みのJSONスキーマ
README.md
```

---

## 7. 実装済み機能

- 匿名認証（クライアント生成UUID）
- 性格診断20問（Likert1〜5、逆転採点あり）→ 5特性を0.0〜1.0で保存
- 診断結果をシステムプロンプトに反映（トーン・丁寧さ・冗長さ・感情表現を制御）
- アバター表情4状態（通常/喜び/悲しみ/考え中）を応答の[STATE:xxx]で切替
- チャット並び順: id昇順（時系列、新しいものが下）
- 物語・背景の自由記述欄（手動編集・保存、暗号化保存）
- 背景の自動更新: アシスタント応答が3の倍数のとき、直近会話からLLMが背景を書き直し
- 会話履歴の暗号化保存・全削除
- GitHub Actions CI/CD（`.github/workflows/ci-cd.yml`）※ Render/VercelはUI連携で自動デプロイ

---

## 8. ローカル実行

```bash
# バックエンド
cd backend
cp .env.example .env        # SECRET_KEY を設定
pip install -r requirements.txt
uvicorn app.main:app --reload    # http://localhost:8000

# フロントエンド（別ターミナル）
cd frontend
cp .env.example .env             # VITE_API_URL=http://localhost:8000
npm install
npm run dev                      # http://localhost:5173
```

---

## 9. デプロイ手順（変更を本番反映）

`main` に push するだけで Render（バック）と Vercel（フロント）が自動デプロイ。

```bash
cd C:\Users\tsuka\Desktop\work\develop\personality-chat
git add -A
git commit -m "変更内容"
git push
```

---

## 10. 既知の注意点・ハマりどころ

- **git のロックファイル**: 過去に `.git/index.lock` / `.git/HEAD.lock` が残って
  コミットが失敗することがあった。出たら `del .git\index.lock .git\HEAD.lock` してから再実行。
- **CoworkサンドボックスからのgitはNG**: マウントfsの権限で lock 削除や push（認証なし）が不可。
  git のコミット/pushは**自分のPCのターミナルで**行う。ファイル編集はどちらでも可。
- **無料Render**: SQLite一時保存＝再起動で履歴消失。永続化はNeon Postgresへ移行が候補。
- **APIキー**: 各ユーザーが自分のGoogle AI APIキーを入力する設計。
- **モデル名**: Gemini提供状況は変わる。404が出たら `MODEL_CANDIDATES` を更新。

---

## 11. 次にやりたいこと（保留中）

- 相手（狼）の見た目を**動くアバター**に（表情差分アニメ or Live2D）。優先度低。
- （任意）会話履歴の永続化（無料Neon Postgres）。
- （任意）背景更新の頻度やプロンプトの調整。

---

## 12. 別スレッドで再開するときの一言テンプレ

> `C:\Users\tsuka\Desktop\work\develop\personality-chat` の「月夜の狼チャット」の続き。
> リポは Tsukasa55/personality-chat、本番は Vercel(front)+Render(back)。
> PROJECT.md に構成と注意点まとめ済み。今日は◯◯をしたい。
