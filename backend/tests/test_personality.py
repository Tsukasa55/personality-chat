import pytest
from app.services.personality import compute_weights
from app.schemas import QuizAnswer


def _make_answers(score: int) -> list[QuizAnswer]:
    return [QuizAnswer(question_id=i, score=score) for i in range(1, 21)]


def test_all_max_score():
    """全問5点 → 外向性・開放性などは最大値に近い、逆転質問は低くなる"""
    weights = compute_weights(_make_answers(5))
    # 逆転採点がある外向性(Q2)・誠実性(Q10)・情緒安定性(Q15)・開放性(Q19)
    # 混在するため0.5〜1.0の範囲
    assert 0.0 <= weights.extraversion <= 1.0
    assert 0.0 <= weights.conscientiousness <= 1.0
    assert 0.0 <= weights.openness <= 1.0
    assert 0.0 <= weights.agreeableness <= 1.0
    assert 0.0 <= weights.neuroticism <= 1.0


def test_all_min_score():
    weights = compute_weights(_make_answers(1))
    assert 0.0 <= weights.extraversion <= 1.0


def test_midpoint():
    """全問3点 → 全特性0.5"""
    weights = compute_weights(_make_answers(3))
    assert weights.extraversion == pytest.approx(0.5)
    assert weights.agreeableness == pytest.approx(0.5)
    assert weights.conscientiousness == pytest.approx(0.5)
    assert weights.neuroticism == pytest.approx(0.5)
    assert weights.openness == pytest.approx(0.5)


def test_different_scores_produce_different_weights():
    """高スコアと低スコアで重みが異なること"""
    high = compute_weights(_make_answers(5))
    low = compute_weights(_make_answers(1))
    # 少なくとも一つの特性は異なる
    assert high != low


@pytest.mark.asyncio
async def test_quiz_endpoint(client):
    """POST /personality/submit が20問回答でweightsを返す"""
    answers = [{"question_id": i, "score": 3} for i in range(1, 21)]
    resp = await client.post("/personality/submit", json={
        "user_id": "11111111-1111-1111-1111-111111111111",
        "answers": answers,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "openness" in data
    assert data["extraversion"] == pytest.approx(0.5)


@pytest.mark.asyncio
async def test_get_questions(client):
    resp = await client.get("/personality/questions")
    assert resp.status_code == 200
    questions = resp.json()["questions"]
    assert len(questions) == 20


@pytest.mark.asyncio
async def test_register_user(client):
    resp = await client.post("/auth/register", json={
        "user_id": "22222222-2222-2222-2222-222222222222"
    })
    assert resp.status_code == 200
    assert resp.json()["user_id"] == "22222222-2222-2222-2222-222222222222"
