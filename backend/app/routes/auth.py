from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models import User
from ..schemas import UserCreate, UserResponse
import re

router = APIRouter(prefix="/auth", tags=["auth"])

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


@router.post("/register", response_model=UserResponse)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    """匿名ユーザーを登録（UUIDはクライアントが生成）"""
    if not UUID_RE.match(payload.user_id):
        raise HTTPException(400, "Invalid UUID format")

    result = await db.execute(select(User).where(User.id == payload.user_id))
    existing = result.scalar_one_or_none()
    if existing:
        return UserResponse(user_id=existing.id, created_at=existing.created_at)

    user = User(id=payload.user_id)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserResponse(user_id=user.id, created_at=user.created_at)
