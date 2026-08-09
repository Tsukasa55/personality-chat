from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models import PersonalityProfile
from ..schemas import QuizSubmit, PersonalityWeights
from ..services.personality import compute_weights, QUIZ_QUESTIONS

router = APIRouter(prefix="/personality", tags=["personality"])


@router.get("/questions")
async def get_questions():
    """20問の診断質問を返す"""
    return {"questions": QUIZ_QUESTIONS}


@router.post("/submit", response_model=PersonalityWeights)
async def submit_quiz(payload: QuizSubmit, db: AsyncSession = Depends(get_db)):
    """20問の回答を受け取り、ビッグファイブ重みを計算・保存する"""
    ids = {a.question_id for a in payload.answers}
    if ids != set(range(1, 21)):
        raise HTTPException(400, "質問 1〜20 の全回答が必要です")

    weights = compute_weights(payload.answers)

    result = await db.execute(
        select(PersonalityProfile).where(PersonalityProfile.user_id == payload.user_id)
    )
    profile = result.scalar_one_or_none()

    if profile:
        profile.openness = weights.openness
        profile.conscientiousness = weights.conscientiousness
        profile.extraversion = weights.extraversion
        profile.agreeableness = weights.agreeableness
        profile.neuroticism = weights.neuroticism
    else:
        profile = PersonalityProfile(
            user_id=payload.user_id,
            **weights.model_dump(),
        )
        db.add(profile)

    await db.commit()
    return weights


@router.get("/{user_id}", response_model=PersonalityWeights)
async def get_profile(user_id: str, db: AsyncSession = Depends(get_db)):
    """ユーザーの性格プロフィールを取得する"""
    result = await db.execute(
        select(PersonalityProfile).where(PersonalityProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "プロフィールが見つかりません。先に診断を完了してください。")
    return PersonalityWeights(
        openness=profile.openness,
        conscientiousness=profile.conscientiousness,
        extraversion=profile.extraversion,
        agreeableness=profile.agreeableness,
        neuroticism=profile.neuroticism,
    )
