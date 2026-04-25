"""
Voice scoring endpoint — accepts audio, extracts features via Gemini, scores.
"""

import base64
import json
import logging
from typing import Dict, Any

from fastapi import APIRouter, UploadFile, File, HTTPException
from openai import AsyncOpenAI

from app.config import settings
from app.main import get_scorer
from app.services.scoring_service import ScoringService
from app.schemas.scoring import ScoringResponse

logger = logging.getLogger(__name__)
router = APIRouter()

EXTRACTION_PROMPT = """
Ты — парсер голосовых заявок на кредит. Пользователь рассказывает о себе голосом.
Извлеки из аудио РОВНО 8 параметров. Если какой-то параметр не упомянут, используй разумное значение по умолчанию.

ОБЯЗАТЕЛЬНЫЕ ПОЛЯ (JSON):
{
  "age": <int, возраст, 18-100>,
  "monthly_income": <float, ежемесячный доход в рублях>,
  "employment_years": <float, стаж работы в годах>,
  "loan_amount": <float, желаемая сумма кредита в рублях>,
  "loan_term_months": <int, срок кредита в месяцах, 6-120>,
  "interest_rate": <float, процентная ставка, если не указана — поставь 15.0>,
  "past_due_30d": <int, количество просрочек 30+ дней, если не упомянуты — 0>,
  "inquiries_6m": <int, кредитные запросы за 6 мес, если не упомянуты — 1>
}

ПРАВИЛА:
- Если человек говорит "зарплата 80 тысяч" → monthly_income: 80000
- Если говорит "хочу миллион" → loan_amount: 1000000
- Если говорит "работаю 5 лет" → employment_years: 5.0
- Если говорит "на 3 года" → loan_term_months: 36
- Возвращай ТОЛЬКО JSON, без markdown, без пояснений.
- Если аудио непонятное или не про кредит, верни JSON с полем "error": "текст ошибки".
"""


async def extract_features_from_audio(audio_bytes: bytes, mime_type: str) -> Dict[str, Any]:
    """Send audio to Gemini Flash and extract scoring features."""
    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.openrouter_api_key,
    )

    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

    response = await client.chat.completions.create(
        model="google/gemini-2.5-flash",
        messages=[
            {"role": "system", "content": EXTRACTION_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": audio_b64,
                            "format": "ogg",
                        },
                    },
                    {
                        "type": "text",
                        "text": "Извлеки параметры кредитной заявки из этого голосового сообщения."
                    },
                ],
            },
        ],
        max_tokens=300,
    )

    raw = response.choices[0].message.content.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

    logger.info("Gemini extracted: %s", raw)
    return json.loads(raw)


@router.post("/voice", response_model=ScoringResponse, tags=["scoring"])
async def voice_scoring(audio: UploadFile = File(...)):
    """
    Accept a voice message, extract credit application data via Gemini,
    and return a full scoring result.
    """
    # Read audio bytes
    audio_bytes = await audio.read()
    if len(audio_bytes) < 100:
        raise HTTPException(400, "Audio file is too small or empty")
    if len(audio_bytes) > 10 * 1024 * 1024:  # 10 MB limit
        raise HTTPException(400, "Audio file too large (max 10 MB)")

    mime = audio.content_type or "audio/ogg"
    logger.info("Voice scoring: %d bytes, mime=%s", len(audio_bytes), mime)

    # 1. Extract features via Gemini
    try:
        features = await extract_features_from_audio(audio_bytes, mime)
    except json.JSONDecodeError as e:
        raise HTTPException(422, f"Gemini returned invalid JSON: {e}")
    except Exception as e:
        logger.error("Gemini audio extraction failed: %s", e)
        raise HTTPException(502, f"AI voice processing error: {e}")

    if "error" in features:
        raise HTTPException(422, f"Could not extract data: {features['error']}")

    # 2. Score
    try:
        scorer = get_scorer()
        service = ScoringService(scorer)
        from app.schemas.scoring import ScoringRequest
        request = ScoringRequest(**features)
        result = service.score(request)
        # Attach extracted features for transparency
        result_dict = result.model_dump()
        result_dict["extracted_features"] = features
        return result_dict
    except Exception as e:
        logger.error("Scoring after voice extraction failed: %s", e)
        raise HTTPException(500, f"Scoring error: {e}")
