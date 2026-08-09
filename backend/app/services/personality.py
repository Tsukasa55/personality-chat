"""
ビッグファイブ性格診断ロジック
20問 × Likert 1〜5 → 各特性 0.0〜1.0 の重みを計算
"""
from ..schemas import QuizAnswer, PersonalityWeights

# 各質問のマッピング: (特性, 逆転採点かどうか)
# 特性: O=開放性 C=誠実性 E=外向性 A=協調性 N=神経症傾向
QUESTION_MAP: dict[int, tuple[str, bool]] = {
    # 外向性 (Extraversion)
    1:  ("E", False),  # 人と話すのが好きだ
    2:  ("E", True),   # 一人でいる方が心地よい
    3:  ("E", False),  # パーティーや集まりを楽しむ
    4:  ("E", False),  # 自分から積極的に発言する
    # 協調性 (Agreeableness)
    5:  ("A", False),  # 他人の気持ちを気にかける
    6:  ("A", True),   # 口論になることが多い
    7:  ("A", False),  # 困っている人を助けたいと思う
    8:  ("A", False),  # 他者の意見を尊重する
    # 誠実性 (Conscientiousness)
    9:  ("C", False),  # 計画を立てて行動する
    10: ("C", True),   # 物事を後回しにしがちだ
    11: ("C", False),  # 細かいことにも注意を払う
    12: ("C", False),  # 締め切りをきちんと守る
    # 情緒安定性 / 神経症傾向 (Neuroticism)
    13: ("N", False),  # 些細なことで不安になる
    14: ("N", False),  # 気分が落ち込むことが多い
    15: ("N", True),   # ストレスに強い方だ
    16: ("N", False),  # 感情的になりやすい
    # 開放性 (Openness)
    17: ("O", False),  # 新しいアイデアを試すのが好きだ
    18: ("O", False),  # 芸術や音楽に興味がある
    19: ("O", True),   # 変化よりも安定を好む
    20: ("O", False),  # 想像力が豊かだと思う
}

TRAIT_KEYS = {"O", "C", "E", "A", "N"}


def compute_weights(answers: list[QuizAnswer]) -> PersonalityWeights:
    """20問の回答からビッグファイブ重みを計算する"""
    scores: dict[str, list[float]] = {k: [] for k in TRAIT_KEYS}

    for ans in answers:
        trait, reverse = QUESTION_MAP[ans.question_id]
        raw = ans.score
        score = (6 - raw) if reverse else raw
        normalized = (score - 1) / 4.0  # 0.0〜1.0
        scores[trait].append(normalized)

    def avg(lst: list[float]) -> float:
        return sum(lst) / len(lst) if lst else 0.5

    return PersonalityWeights(
        openness=round(avg(scores["O"]), 3),
        conscientiousness=round(avg(scores["C"]), 3),
        extraversion=round(avg(scores["E"]), 3),
        agreeableness=round(avg(scores["A"]), 3),
        neuroticism=round(avg(scores["N"]), 3),
    )


# 診断問題テキスト（フロントエンドにも返す）
QUIZ_QUESTIONS = [
    {"id": 1,  "text": "人と話すのが好きだ",               "trait": "外向性"},
    {"id": 2,  "text": "一人でいる方が心地よい",           "trait": "外向性"},
    {"id": 3,  "text": "パーティーや集まりを楽しむ",       "trait": "外向性"},
    {"id": 4,  "text": "自分から積極的に発言する",         "trait": "外向性"},
    {"id": 5,  "text": "他人の気持ちを気にかける",         "trait": "協調性"},
    {"id": 6,  "text": "口論になることが多い",             "trait": "協調性"},
    {"id": 7,  "text": "困っている人を助けたいと思う",     "trait": "協調性"},
    {"id": 8,  "text": "他者の意見を尊重する",             "trait": "協調性"},
    {"id": 9,  "text": "計画を立てて行動する",             "trait": "誠実性"},
    {"id": 10, "text": "物事を後回しにしがちだ",           "trait": "誠実性"},
    {"id": 11, "text": "細かいことにも注意を払う",         "trait": "誠実性"},
    {"id": 12, "text": "締め切りをきちんと守る",           "trait": "誠実性"},
    {"id": 13, "text": "些細なことで不安になる",           "trait": "情緒安定性"},
    {"id": 14, "text": "気分が落ち込むことが多い",         "trait": "情緒安定性"},
    {"id": 15, "text": "ストレスに強い方だ",               "trait": "情緒安定性"},
    {"id": 16, "text": "感情的になりやすい",               "trait": "情緒安定性"},
    {"id": 17, "text": "新しいアイデアを試すのが好きだ",   "trait": "開放性"},
    {"id": 18, "text": "芸術や音楽に興味がある",           "trait": "開放性"},
    {"id": 19, "text": "変化よりも安定を好む",             "trait": "開放性"},
    {"id": 20, "text": "想像力が豊かだと思う",             "trait": "開放性"},
]
