from sqlalchemy import Column, String, Text, DateTime, Float, Integer
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)  # UUID
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PersonalityProfile(Base):
    __tablename__ = "personality_profiles"

    user_id = Column(String(36), primary_key=True)
    openness = Column(Float, default=0.5)
    conscientiousness = Column(Float, default=0.5)
    extraversion = Column(Float, default=0.5)
    agreeableness = Column(Float, default=0.5)
    neuroticism = Column(Float, default=0.5)  # 情緒安定性の逆
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False, index=True)
    role = Column(String(10), nullable=False)  # "user" or "assistant"
    content_encrypted = Column(Text, nullable=False)  # 暗号化されたメッセージ
    avatar_state = Column(String(20), default="normal")  # normal/happy/sad/thinking
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Background(Base):
    """ユーザーと月夜の狼の物語・背景・関係性（暗号化保存・会話で自動更新）"""
    __tablename__ = "backgrounds"

    user_id = Column(String(36), primary_key=True)
    content_encrypted = Column(Text, nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
