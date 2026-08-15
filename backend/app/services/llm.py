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

## 物語・背景・関係性（あなたとユーザーの関係、世界観）
{background}

上記の背景を踏まえ、一貫した人物として自然に振る舞ってください。
背景が未設定の場合は、無理に設定を作らず自然に会話してください。

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


def _build_system_prompt(weights: PersonalityWeights, background: str = "") -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(
        openness=weights.openness,
        conscientiousness=weights.conscientiousness,
        extraversion=weights.extraversion,
        agreeableness=weights.agreeableness,
        neuroticism=weights.neuroticism,
        background=(background.strip() or "（未設定）"),
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


# 使用するモデルの候補（上から順に試し、404等で使えなければ次へ）
# ※ Googleのモデル提供状況は変わるため複数候補を用意している
MODEL_CANDIDATES = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-flash-latest",
    "gemini-1.5-flash-latest",
]


async def generate_response(
    user_message: str,
    history: list[dict],  # [{"role": "user"|"model", "parts": [str]}]
    weights: PersonalityWeights,
    api_key: str,
    background: str = "",
) -> tuple[str, AvatarState]:
    """Gemini APIで応答を生成し、(応答テキスト, アバター状態) を返す"""
    genai.configure(api_key=api_key)
    system_prompt = _build_system_prompt(weights, background)

    last_error: Exception | None = None
    for model_name in MODEL_CANDIDATES:
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_prompt,
            )
            chat = model.start_chat(history=history)
            response = await chat.send_message_async(user_message)
            state, content = _parse_state(response.text)
            return content, state
        except Exception as e:  # 404 等はフォールバックして次のモデルへ
            last_error = e
            if "not found" in str(e).lower() or "404" in str(e):
                continue
            raise

    raise RuntimeError(
        f"利用可能なGeminiモデルが見つかりません。最後のエラー: {last_error}"
    )


BACKGROUND_UPDATE_PROMPT = """あなたは物語の記録者です。
「月夜の狼」というAIキャラクターと、そのユーザーとの関係性・物語・背景を管理しています。

## これまでの背景（現在の記録）
{current}

## 最近の会話
{conversation}

## 指示
最近の会話で明らかになった新しい事実・関係性の変化・出来事を反映し、
背景の記録を更新してください。次のルールに従ってください:
- 日本語で、300字以内の簡潔な地の文にまとめる
- 既存の設定と矛盾しない形で統合する（重要な既存情報は保持）
- 事実が乏しい場合は、既存の背景をほぼそのまま返す
- 見出しや箇条書きは使わず、説明文のみを出力する
- 前置きや「更新しました」等のメタ発言は書かず、背景本文だけを出力する

更新後の背景:"""


async def update_background(
    current_background: str,
    conversation: str,
    api_key: str,
) -> str:
    """最近の会話を踏まえ、背景・関係性の記録を更新して返す"""
    genai.configure(api_key=api_key)
    prompt = BACKGROUND_UPDATE_PROMPT.format(
        current=(current_background.strip() or "（まだ記録なし）"),
        conversation=conversation.strip(),
    )
    last_error: Exception | None = None
    for model_name in MODEL_CANDIDATES:
        try:
            model = genai.GenerativeModel(model_name=model_name)
            response = await model.generate_content_async(prompt)
            text = (response.text or "").strip()
            return text[:4000] if text else current_background
        except Exception as e:
            last_error = e
            if "not found" in str(e).lower() or "404" in str(e):
                continue
            # 背景更新の失敗は致命的でない → 既存を維持
            return current_background
    return current_background


# デフォルト重みのフォールバック
DEFAULT_WEIGHTS = PersonalityWeights(
    openness=0.5,
    conscientiousness=0.5,
    extraversion=0.5,
    agreeableness=0.5,
    neuroticism=0.5,
)
