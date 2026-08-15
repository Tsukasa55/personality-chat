from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models import Background
from ..schemas import BackgroundOut, BackgroundUpdate
from ..services.encryption import encrypt, decrypt
from ..config import get_settings

router = APIRouter(prefix="/background", tags=["background"])
settings = get_settings()


@router.get("/{user_id}", response_model=BackgroundOut)
async def get_background(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Background).where(Background.user_id == user_id))
    bg = result.scalar_one_or_none()
    if not bg:
        return BackgroundOut(background="", updated_at=None)
    try:
        text = decrypt(bg.content_encrypted, user_id, settings.secret_key)
    except Exception:
        text = ""
    return BackgroundOut(background=text, updated_at=bg.updated_at)


@router.put("/", response_model=BackgroundOut)
async def set_background(payload: BackgroundUpdate, db: AsyncSession = Depends(get_db)):
    enc = encrypt(payload.background, payload.user_id, settings.secret_key)
    result = await db.execute(
        select(Background).where(Background.user_id == payload.user_id)
    )
    bg = result.scalar_one_or_none()
    if bg:
        bg.content_encrypted = enc
    else:
        bg = Background(user_id=payload.user_id, content_encrypted=enc)
        db.add(bg)
    await db.commit()
    await db.refresh(bg)
    return BackgroundOut(background=payload.background, updated_at=bg.updated_at)
