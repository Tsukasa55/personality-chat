from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime


# ── 匿名認証 ──────────────────────────────────────────────
class UserCreate(BaseModel):
    user_id: str = Field(..., description="クライアント生成UUID")


class UserResponse(BaseModel):
    user_id: str
    created_at: datetime


# ── 性格診断 ──────────────────────────────────────────────
class QuizAnswer(BaseModel):
    question_id: int
    score: int = Field(..., ge=1, le=5)


class QuizSubmit(BaseModel):
    user_id: str
    answers: list[QuizAnswer] = Field(..., min_length=20, max_length=20)


class PersonalityWeights(BaseModel):
    openness: float        # 開放性
    conscientiousness: float  # 誠実性
    extraversion: float    # 外向性
    agreeableness: float   # 協調性
    neuroticism: float     # 情緒安定性（低いほど安定）


# ── チャット ──────────────────────────────────────────────
AvatarState = Literal["normal", "happy", "sad", "thinking"]


class ChatRequest(BaseModel):
    user_id: str
    message: str = Field(..., min_length=1, max_length=2000)
    google_api_key: str = Field(..., min_length=1)


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    avatar_state: AvatarState
    created_at: datetime

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    reply: str
    avatar_state: AvatarState
    history: list[MessageOut]
    background: str = ""          # 現在の物語・背景
    background_updated: bool = False  # このターンで背景が自動更新されたか


# ── 背景・物語 ────────────────────────────────────────────
class BackgroundOut(BaseModel):
    background: str
    updated_at: datetime | None = None


class BackgroundUpdate(BaseModel):
    user_id: str
    background: str = Field(default="", max_length=4000)


# ── 履歴 ──────────────────────────────────────────────────
class HistoryResponse(BaseModel):
    messages: list[MessageOut]


class DeleteResponse(BaseModel):
    deleted: int
