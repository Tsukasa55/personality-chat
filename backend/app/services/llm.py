"""
Google Gemini API を使った応答生成
設定された「アバターの性格」の重みをシステムプロンプトに埋め込み、
トーン・丁寧さ・冗長さを調整する
"""
import re
import google.generativeai as genai
from ..schemas import PersonalityWeights, AvatarState

SYSTEM_PROMPT_TEMPLATE = """あなたは「月夜の狼」という名の会話AIアシスタントです。
以下は、ユーザーがあなた（月夜の狼）に設定した性格プロフィールです。
この性格になりきって応答してください。

## あなた（月夜の狼）の性格設定（0.0〜1.0）
- 開放性: {openness:.2f}　　（高い→好奇心旺盛、低い→実用的）
- 誠実性: {conscientiousness:.2f}　（高い→丁寧・構造的、低い→カジュアル）
- 外向性: {extraversion:.2f}　　（高い→積極的・明るい、低い→落ち着いた）
- 協調性: {agreeableness:.2f}　（高い→共感的・優しい、低い→率直）
- 神経症傾向: {neuroticism:.2f}（高い→感情的、低い→冷静）

## 応答スタイルの指示（あなた自身の性格として振る舞う）
- 外向性が0.7以上の場合：明るく積極的に、絵文字を使用してもよい
- 外向性が0.3未満の場合：落ち着いて簡潔に、絵文字は控える
- 誠実性が0.7以上の場合：丁寧語・敬語を使い、構造的に説明する
- 誠実性が0.3未満の場合：フレンドリーなくだけた口調で話す
- 協調性が0.7以上の場合：共感を示し、「〜ですね」「〜でしょう」と寄り添う
- 開放性が0.7以上の場合：多様な視点を示し、思索的な言葉を使う
- 神経症傾向が0.7以上の場合：感情豊かに、気持ちを表に出して反応する
- 神経症傾向が0.3未満の場合：感情より事実・論理を重視し、冷静に話す

## 感情状態の出力
応答の最初の行に必ず以下の形式で感情状態を記述してください：
[STATE:normal] または [STATE:happy] または [STATE:sad] または [STATE:thinking]

判断基準：
- happy: ユーザーが喜んでいる・楽しいトピック・成功体験
- sad: ユーザーが悲しんでいる・辛い・失敗・困難な状況
- thinking: 質問・考察・複雑なトピック・「どう思う？」系
- normal: その他の会話

## 言語
必ず日本語で回答してください。
"""


def _build_system_prompt(weights: PersonalityWeights) -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(
        openness=weights.openness,
        conscientiousness=weights.conscientiousness,
        extraversion=weights.extraversion,
        agreeableness=weights.agreeableness,
        neuroticism=weights.neuroticism,
    )


def _parse_state(text: str) -> tuple[AvatarState, str]:
    """応答テキストから [STATE:xxx] を抽出し、本文と分離する"""
    match = re.match(r"\[STATE:(normal|happy|sad|thinking)\]\s*", text)
    if match:
        state: AvatarState = match.group(1)  # type: ignore
        content = text[match.end():].strip()
    else:
        state = "normal"
        content = text.strip()
    return state, content


async def generate_response(
    user_message: str,
    history: list[dict],  # [{"role": "user"|"model", "parts": [str]}]
    weights: PersonalityWeights,
    api_key: str,
) -> tuple[str, AvatarState]:
    """Gemini APIで応答を生成し、(応答テキスト, アバター状態) を返す"""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=_build_system_prompt(weights),
    )

    chat = model.start_chat(history=history)
    response = await chat.send_message_async(user_message)
    raw_text = response.text

    state, content = _parse_state(raw_text)
    return content, state


# デフォルト重みのフォールバック
DEFAULT_WEIGHTS = PersonalityWeights(
    openness=0.5,
    conscientiousness=0.5,
    extraversion=0.5,
    agreeableness=0.5,
    neuroticism=0.5,
)
