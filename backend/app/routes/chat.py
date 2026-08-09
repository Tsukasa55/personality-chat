from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from ..database import get_db
from ..models import Message, PersonalityProfile
from ..schemas import ChatRequest, ChatResponse, MessageOut, HistoryResponse, DeleteResponse
from ..services.llm import generate_response, DEFAULT_WEIGHTS
from ..services.encryption import encrypt, decrypt
from ..services.personality import compute_weights
from ..config import get_settings
from ..schemas import PersonalityWeights

router = APIRouter(prefix="/chat", tags=["chat"])
settings = get_settings()


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


async def _load_history(user_id: str, db: AsyncSession, limit: int = 20) -> list[Message]:
    result = await db.execute(
        select(Message)
        .where(Message.user_id == user_id)
        .order_by(Message.created_at.desc())
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

    # 直近の履歴を取得してGemini形式に変換
    history_msgs = await _load_history(payload.user_id, db, limit=20)
    gemini_history = []
    for m in history_msgs:
        try:
            content = decrypt(m.content_encrypted, payload.user_id, settings.secret_key)
        except Exception:
            continue
        role = "model" if m.role == "assistant" else "user"
        gemini_history.append({"role": role, "parts": [content]})

    # LLM 応答生成
    try:
        reply_text, avatar_state = await generate_response(
            payload.message, gemini_history, weights, payload.google_api_key
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

    # 最新履歴を返す
    all_msgs = await _load_history(payload.user_id, db, limit=40)
    history_out = _decrypt_messages(all_msgs, payload.user_id)

    return ChatResponse(reply=reply_text, avatar_state=avatar_state, history=history_out)


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
