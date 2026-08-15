from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from ..database import get_db
from ..models import Message, PersonalityProfile, Background
from ..schemas import ChatRequest, ChatResponse, MessageOut, HistoryResponse, DeleteResponse
from ..services.llm import generate_response, update_background, DEFAULT_WEIGHTS
from ..services.encryption import encrypt, decrypt
from ..config import get_settings
from ..schemas import PersonalityWeights

router = APIRouter(prefix="/chat", tags=["chat"])
settings = get_settings()

# 何往復ごとに背景を自動更新するか（アシスタント応答数が この倍数 のとき更新）
BACKGROUND_UPDATE_EVERY = 3


async def _get_weights(user_id: str, db: AsyncSession) -> PersonalityWeights:
    result = await db.execute(
        select(PersonalityProfile).where(PersonalityProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        return DEFAULT_WEIGHTS
    return PersonalityWeights(
        openness=profile.openness,
        conscientiousness=profile.conscientiousness,
        extraversion=profile.extraversion,
        agreeableness=profile.agreeableness,
        neuroticism=profile.neuroticism,
    )


async def _get_background(user_id: str, db: AsyncSession) -> Background | None:
    result = await db.execute(
        select(Background).where(Background.user_id == user_id)
    )
    return result.scalar_one_or_none()


def _decrypt_background(bg: Background | None, user_id: str) -> str:
    if not bg:
        return ""
    try:
        return decrypt(bg.content_encrypted, user_id, settings.secret_key)
    except Exception:
        return ""


async def _save_background(user_id: str, text: str, db: AsyncSession):
    enc = encrypt(text, user_id, settings.secret_key)
    bg = await _get_background(user_id, db)
    if bg:
        bg.content_encrypted = enc
    else:
        db.add(Background(user_id=user_id, content_encrypted=enc))
    await db.commit()


async def _load_history(user_id: str, db: AsyncSession, limit: int = 20) -> list[Message]:
    # id 昇順（＝時系列: 古い→新しい）で返す。新しい発言が常に下に並ぶ。
    result = await db.execute(
        select(Message)
        .where(Message.user_id == user_id)
        .order_by(Message.id.desc())
        .limit(limit)
    )
    rows = list(reversed(result.scalars().all()))
    return rows


def _decrypt_messages(msgs: list[Message], user_id: str) -> list[MessageOut]:
    out = []
    for m in msgs:
        try:
            content = decrypt(m.content_encrypted, user_id, settings.secret_key)
        except Exception:
            content = "[復号エラー]"
        out.append(MessageOut(
            id=m.id,
            role=m.role,
            content=content,
            avatar_state=m.avatar_state,
            created_at=m.created_at,
        ))
    return out


@router.post("/send", response_model=ChatResponse)
async def send_message(payload: ChatRequest, db: AsyncSession = Depends(get_db)):
    weights = await _get_weights(payload.user_id, db)
    bg_row = await _get_background(payload.user_id, db)
    background = _decrypt_background(bg_row, payload.user_id)

    # 直近の履歴を取得してGemini形式に変換（時系列）
    history_msgs = await _load_history(payload.user_id, db, limit=20)
    gemini_history = []
    for m in history_msgs:
        try:
            content = decrypt(m.content_encrypted, payload.user_id, settings.secret_key)
        except Exception:
            continue
        role = "model" if m.role == "assistant" else "user"
        gemini_history.append({"role": role, "parts": [content]})

    # LLM 応答生成（背景も渡す）
    try:
        reply_text, avatar_state = await generate_response(
            payload.message, gemini_history, weights, payload.google_api_key, background
        )
    except Exception as e:
        raise HTTPException(502, f"LLM エラー: {str(e)}")

    # ユーザーメッセージを保存
    user_msg = Message(
        user_id=payload.user_id,
        role="user",
        content_encrypted=encrypt(payload.message, payload.user_id, settings.secret_key),
        avatar_state="normal",
    )
    db.add(user_msg)

    # アシスタント応答を保存
    asst_msg = Message(
        user_id=payload.user_id,
        role="assistant",
        content_encrypted=encrypt(reply_text, payload.user_id, settings.secret_key),
        avatar_state=avatar_state,
    )
    db.add(asst_msg)
    await db.commit()

    # ── 背景の自動更新（数ターンごと） ──
    background_updated = False
    asst_count = await db.scalar(
        select(func.count(Message.id)).where(
            Message.user_id == payload.user_id, Message.role == "assistant"
        )
    )
    if asst_count and asst_count % BACKGROUND_UPDATE_EVERY == 0:
        recent = await _load_history(payload.user_id, db, limit=8)
        convo_lines = []
        for m in recent:
            try:
                c = decrypt(m.content_encrypted, payload.user_id, settings.secret_key)
            except Exception:
                continue
            who = "月夜の狼" if m.role == "assistant" else "ユーザー"
            convo_lines.append(f"{who}: {c}")
        try:
            new_bg = await update_background(
                background, "\n".join(convo_lines), payload.google_api_key
            )
            if new_bg and new_bg.strip() and new_bg.strip() != background.strip():
                await _save_background(payload.user_id, new_bg.strip(), db)
                background = new_bg.strip()
                background_updated = True
        except Exception:
            pass  # 背景更新の失敗は無視（会話は成立している）

    # 最新履歴を返す
    all_msgs = await _load_history(payload.user_id, db, limit=100)
    history_out = _decrypt_messages(all_msgs, payload.user_id)

    return ChatResponse(
        reply=reply_text,
        avatar_state=avatar_state,
        history=history_out,
        background=background,
        background_updated=background_updated,
    )


@router.get("/history/{user_id}", response_model=HistoryResponse)
async def get_history(user_id: str, db: AsyncSession = Depends(get_db)):
    msgs = await _load_history(user_id, db, limit=100)
    return HistoryResponse(messages=_decrypt_messages(msgs, user_id))


@router.delete("/history/{user_id}", response_model=DeleteResponse)
async def delete_history(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        delete(Message).where(Message.user_id == user_id)
    )
    await db.commit()
    return DeleteResponse(deleted=result.rowcount)
