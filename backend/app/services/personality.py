"""
ビッグファイブ性格モデル ロジック
20問 × Likert 1〜5 → 各特性 0.0〜1.0 の重みを計算
※ ここで測るのは「アバター（月夜の狼）にどんな性格でいてほしいか」であり、
   その重みが応答トーンの調整に使われる。
"""
from ..schemas import QuizAnswer, PersonalityWeights

# 各質問のマッピング: (特性, 逆転採点かどうか)
# 特性: O=開放性 C=誠実性 E=外向性 A=協調性 N=神経症傾向
QUESTION_MAP: dict[int, tuple[str, bool]] = {
    # 外向性 (Extraversion)
    1:  ("E", False),  # よく話す、おしゃべりな性格がいい
    2:  ("E", True),   # 口数が少なく、物静かな方がいい
    3:  ("E", False),  # 明るく、にぎやかに接してほしい
    4:  ("E", False),  # 自分から積極的に話しかけてほしい
    # 協調性 (Agreeableness)
    5:  ("A", False),  # こちらの気持ちに寄り添ってほしい
    6:  ("A", True),   # 遠慮なく、ズバッと指摘してほしい
    7:  ("A", False),  # 困ったときは親身に助けてほしい
    8:  ("A", False),  # こちらの意見を尊重してほしい
    # 誠実性 (Conscientiousness)
    9:  ("C", False),  # 順序立てて丁寧に説明してほしい
    10: ("C", True),   # 細かいことは気にせず気楽な方がいい
    11: ("C", False),  # 細部まできっちり対応してほしい
    12: ("C", False),  # 約束したことはきちんと守ってほしい
    # 情緒安定性 / 神経症傾向 (Neuroticism)
    13: ("N", False),  # 感情豊かに反応してほしい
    14: ("N", False),  # 気持ちを素直に表してほしい
    15: ("N", True),   # どんなときも冷静で動じない方がいい
    16: ("N", False),  # こちらの感情に敏感に応じてほしい
    # 開放性 (Openness)
    17: ("O", False),  # 新しい発想やアイデアを楽しんでほしい
    18: ("O", False),  # 芸術や創造的な話題も好きでいてほしい
    19: ("O", True),   # 奇抜さより堅実さを大切にしてほしい
    20: ("O", False),  # 想像力豊かに話してほしい
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


# 設定用の質問テキスト（フロントエンドにも返す）
# 「こんな月夜の狼と話したい」という観点で答えてもらう
QUIZ_QUESTIONS = [
    {"id": 1,  "text": "よく話す、おしゃべりな性格がいい",       "trait": "外向性"},
    {"id": 2,  "text": "口数が少なく、物静かな方がいい",         "trait": "外向性"},
    {"id": 3,  "text": "明るく、にぎやかに接してほしい",         "trait": "外向性"},
    {"id": 4,  "text": "自分から積極的に話しかけてほしい",       "trait": "外向性"},
    {"id": 5,  "text": "こちらの気持ちに寄り添ってほしい",       "trait": "協調性"},
    {"id": 6,  "text": "遠慮なく、ズバッと指摘してほしい",       "trait": "協調性"},
    {"id": 7,  "text": "困ったときは親身に助けてほしい",         "trait": "協調性"},
    {"id": 8,  "text": "こちらの意見を尊重してほしい",           "trait": "協調性"},
    {"id": 9,  "text": "順序立てて丁寧に説明してほしい",         "trait": "誠実性"},
    {"id": 10, "text": "細かいことは気にせず気楽な方がいい",     "trait": "誠実性"},
    {"id": 11, "text": "細部まできっちり対応してほしい",         "trait": "誠実性"},
    {"id": 12, "text": "約束したことはきちんと守ってほしい",     "trait": "誠実性"},
    {"id": 13, "text": "感情豊かに反応してほしい",               "trait": "情緒安定性"},
    {"id": 14, "text": "気持ちを素直に表してほしい",             "trait": "情緒安定性"},
    {"id": 15, "text": "どんなときも冷静で動じない方がいい",     "trait": "情緒安定性"},
    {"id": 16, "text": "こちらの感情に敏感に応じてほしい",       "trait": "情緒安定性"},
    {"id": 17, "text": "新しい発想やアイデアを楽しんでほしい",   "trait": "開放性"},
    {"id": 18, "text": "芸術や創造的な話題も好きでいてほしい",   "trait": "開放性"},
    {"id": 19, "text": "奇抜さより堅実さを大切にしてほしい",     "trait": "開放性"},
    {"id": 20, "text": "想像力豊かに話してほしい",               "trait": "開放性"},
]
