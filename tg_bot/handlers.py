"""
Handlers for the RizzScoreAI Telegram bot.

- /start → main menu
- "Быстрый скоринг" → FSM flow (8 steps)
- "AI-советник" → free-form chat with LLM advisor
- "О проекте" → info
- Cancel → back to menu
"""

from __future__ import annotations

import logging

import httpx
from aiogram import F, Router
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ContentType

from config import BACKEND_URL
from keyboards import (
    advisor_keyboard,
    back_to_menu_keyboard,
    cancel_keyboard,
    main_menu_keyboard,
    score_again_keyboard,
)
from states import STEPS, AdvisorChat, ScoringForm

logger = logging.getLogger(__name__)
router = Router()


# ── Risk segment styling ─────────────────────────────────────

_RISK_EMOJI = {
    "low": "🟢",
    "medium": "🟡",
    "high": "🔴",
    "critical": "🔴🔴",
}

_RISK_LABEL = {
    "low": "Низкий риск",
    "medium": "Средний риск",
    "high": "Высокий риск",
    "critical": "Критический риск",
}


# ── /start ───────────────────────────────────────────────────

WELCOME_TEXT = (
    "🎯 <b>RizzScoreAI</b>\n\n"
    "Привет! Я — твой AI-помощник по кредитному скорингу.\n"
    "Оценю кредитоспособность за секунды и дам персональные советы.\n\n"
    "🌐 <b>Открыть скоринг</b> — полный веб-интерфейс с аналитикой\n"
    "📊 <b>Быстрый скоринг</b> — 8 вопросов прямо в чате\n"
    "🎤 <b>Голосовой скоринг</b> — просто расскажи о себе голосом\n"
    "🤖 <b>AI-советник</b> — персональные финансовые рекомендации\n"
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(WELCOME_TEXT, reply_markup=main_menu_keyboard())
    await callback.answer()


# ── About ────────────────────────────────────────────────────

ABOUT_TEXT = (
    "ℹ️ <b>О RizzScoreAI</b>\n\n"
    "ML-платформа кредитного скоринга с AI-советником.\n\n"
    "🧠 <b>Модель:</b> L2 Logistic Regression (NumPy)\n"
    "📈 <b>ROC-AUC:</b> 0.827 на holdout-выборке\n"
    "🔢 <b>Данные:</b> 8 признаков → P(default) + балл FICO\n"
    "💡 <b>XAI:</b> SHAP-вклад каждого фактора\n"
    "🤖 <b>AI-советник:</b> Gemini 2.5 Flash через OpenRouter\n"
    "📊 <b>Калькулятор:</b> аннуитет + дифференцированный + DTI\n"
    "📥 <b>CSV-импорт:</b> пакетный скоринг\n\n"
    "Разработано командой YASI на хакатоне 2026 🚀"
)


@router.callback_query(F.data == "about")
async def cb_about(callback: CallbackQuery) -> None:
    await callback.message.edit_text(ABOUT_TEXT, reply_markup=back_to_menu_keyboard())
    await callback.answer()


# ── Scoring FSM ──────────────────────────────────────────────

@router.callback_query(F.data == "start_scoring")
async def cb_start_scoring(callback: CallbackQuery, state: FSMContext) -> None:
    """Start the scoring flow — ask the first question."""
    await state.clear()
    await state.set_data({"features": {}})
    step = STEPS[0]
    await state.set_state(step["state"])
    await callback.message.edit_text(
        f"📋 <b>Скоринг заявки</b> (1/{len(STEPS)})\n\n{step['prompt']}",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "cancel")
async def cb_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        "❌ Скоринг отменён.", reply_markup=back_to_menu_keyboard()
    )
    await callback.answer()


# Universal handler for all scoring states
@router.message(StateFilter(
    ScoringForm.age, ScoringForm.monthly_income, ScoringForm.employment_years,
    ScoringForm.loan_amount, ScoringForm.loan_term_months, ScoringForm.interest_rate,
    ScoringForm.past_due_30d, ScoringForm.inquiries_6m,
))
async def handle_scoring_step(message: Message, state: FSMContext) -> None:
    """Process current step input, validate, and advance to next step or finish."""
    current_state = await state.get_state()

    # Find current step index
    step_idx = None
    for i, step in enumerate(STEPS):
        if step["state"].state == current_state:
            step_idx = i
            break

    if step_idx is None:
        await message.answer("Что-то пошло не так. Начните заново: /start")
        await state.clear()
        return

    step = STEPS[step_idx]

    # Parse and validate
    try:
        value = step["parse"](message.text.strip())
        if not step["validate"](value):
            raise ValueError()
    except (ValueError, TypeError, AttributeError):
        await message.answer(
            f"⚠️ {step['error']}\n\nПопробуйте ещё раз:",
            reply_markup=cancel_keyboard(),
        )
        return

    # Save the value
    data = await state.get_data()
    data["features"][step["key"]] = value
    await state.set_data(data)

    # Next step or finish
    next_idx = step_idx + 1
    if next_idx < len(STEPS):
        next_step = STEPS[next_idx]
        await state.set_state(next_step["state"])
        await message.answer(
            f"📋 <b>Скоринг заявки</b> ({next_idx + 1}/{len(STEPS)})\n\n{next_step['prompt']}",
            reply_markup=cancel_keyboard(),
        )
    else:
        # All steps done — call the API
        await state.clear()
        await message.answer("⏳ Выполняю скоринг...")
        await _call_scoring_api(message, state, data["features"])


# ── API call & result formatting ─────────────────────────────

async def _call_scoring_api(message: Message, state: FSMContext, features: dict) -> None:
    """Call the backend scoring API and format the result."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{BACKEND_URL}/api/v1/scoring/predict",
                json=features,
            )
            resp.raise_for_status()
            result = resp.json()
    except httpx.HTTPStatusError as e:
        logger.error("Backend returned %s: %s", e.response.status_code, e.response.text)
        await message.answer(
            "❌ Ошибка валидации данных. Проверьте введённые значения.",
            reply_markup=back_to_menu_keyboard(),
        )
        return
    except Exception as e:
        logger.error("Backend call failed: %s", e)
        await message.answer(
            "❌ Сервер скоринга недоступен. Попробуйте позже.",
            reply_markup=back_to_menu_keyboard(),
        )
        return

    # Store last scoring result in FSM data for advisor
    await state.set_data({
        "last_scoring_result": result,
        "last_scoring_features": features,
        "advisor_history": [],
    })

    # Format the result
    text = _format_scoring_result(result, features)
    await message.answer(text, reply_markup=score_again_keyboard())


def _format_scoring_result(result: dict, features: dict) -> str:
    """Build a beautiful text message from the scoring API response."""
    decision = result["decision"]
    prob = result["probability_of_default"]
    score = result["credit_score"]
    segment = result["risk_segment"]
    threshold = result["threshold_used"]

    risk_emoji = _RISK_EMOJI.get(segment["label"], "⚪")
    risk_label = _RISK_LABEL.get(segment["label"], segment["label"])

    # Decision emoji
    if decision == "APPROVED":
        decision_line = "✅ <b>ОДОБРЕНО</b>"
    else:
        decision_line = "❌ <b>ОТКАЗ</b>"

    # Score bar (visual)
    score_pct = (score - 300) / 550  # 300-850 range
    filled = int(score_pct * 10)
    bar = "█" * filled + "░" * (10 - filled)

    # Feature summary
    feature_lines = []
    labels = {
        "age": "Возраст",
        "monthly_income": "Доход",
        "employment_years": "Стаж",
        "loan_amount": "Сумма кредита",
        "loan_term_months": "Срок",
        "interest_rate": "Ставка",
        "past_due_30d": "Просрочки",
        "inquiries_6m": "Запросы",
    }
    for key, label in labels.items():
        val = features.get(key, "—")
        if key == "monthly_income" or key == "loan_amount":
            feature_lines.append(f"  {label}: {val:,.0f} ₽")
        elif key == "interest_rate":
            feature_lines.append(f"  {label}: {val}%")
        elif key == "loan_term_months":
            feature_lines.append(f"  {label}: {val} мес.")
        elif key == "employment_years":
            feature_lines.append(f"  {label}: {val} лет")
        else:
            feature_lines.append(f"  {label}: {val}")

    features_block = "\n".join(feature_lines)

    text = (
        f"🏦 <b>Результат скоринга</b>\n\n"
        f"{decision_line}\n\n"
        f"📊 <b>Кредитный скор:</b> {score}/850\n"
        f"  [{bar}]\n\n"
        f"{risk_emoji} <b>Риск:</b> {risk_label}\n"
        f"📉 <b>P(default):</b> {prob * 100:.1f}%\n"
        f"🎯 <b>Порог:</b> {threshold * 100:.0f}%\n\n"
        f"<b>Данные заявки:</b>\n{features_block}"
    )

    return text


# ── AI Advisor ───────────────────────────────────────────────

ADVISOR_WELCOME = (
    "💬 <b>AI-советник по кредитам</b>\n\n"
    "Я — ваш персональный финансовый консультант.\n"
    "Задайте мне любой вопрос о кредитах, скоринге или финансах.\n\n"
    "💡 <i>Совет: сначала пройдите скоринг — тогда советы будут персональными!</i>\n\n"
    "Напишите ваш вопрос:"
)

ADVISOR_WITH_CONTEXT = (
    "💬 <b>AI-советник по кредитам</b>\n\n"
    "Я вижу результат вашего скоринга и могу дать персональные рекомендации.\n\n"
    "Спросите меня, например:\n"
    '• «Как улучшить мой кредитный скор?»\n'
    '• «Почему мне отказали?»\n'
    '• «Что делать с просрочками?»\n\n'
    "Напишите ваш вопрос:"
)


@router.callback_query(F.data == "start_advisor")
async def cb_start_advisor(callback: CallbackQuery, state: FSMContext) -> None:
    """Start advisor chat — general mode (no scoring context)."""
    data = await state.get_data()
    has_context = "last_scoring_result" in data

    await state.set_state(AdvisorChat.chatting)
    if not has_context:
        await state.set_data({"advisor_history": []})

    text = ADVISOR_WITH_CONTEXT if has_context else ADVISOR_WELCOME
    await callback.message.edit_text(text, reply_markup=advisor_keyboard())
    await callback.answer()


@router.callback_query(F.data == "advisor_after_score")
async def cb_advisor_after_score(callback: CallbackQuery, state: FSMContext) -> None:
    """Start advisor chat right after scoring — scoring context is available."""
    await state.set_state(AdvisorChat.chatting)
    await callback.message.edit_text(
        ADVISOR_WITH_CONTEXT, reply_markup=advisor_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "exit_advisor")
async def cb_exit_advisor(callback: CallbackQuery, state: FSMContext) -> None:
    """Exit advisor chat and return to main menu."""
    await state.clear()
    await callback.message.edit_text(WELCOME_TEXT, reply_markup=main_menu_keyboard())
    await callback.answer()


@router.message(AdvisorChat.chatting)
async def handle_advisor_message(message: Message, state: FSMContext) -> None:
    """Handle a user message in the advisor chat — call backend LLM endpoint."""
    data = await state.get_data()

    # Build ML context for the advisor
    ml_context = _build_ml_context(data)

    # Get chat history
    history = data.get("advisor_history", [])

    # Show typing indicator
    await message.answer("🤔 Анализирую...")

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{BACKEND_URL}/api/v1/advisor/chat",
                json={
                    "ml_context": ml_context,
                    "chat_history": history,
                    "user_message": message.text,
                },
            )
            resp.raise_for_status()
            reply = resp.json()["reply"]
    except Exception as e:
        logger.error("Advisor API call failed: %s", e)
        await message.answer(
            "❌ AI-советник временно недоступен. Попробуйте позже.",
            reply_markup=advisor_keyboard(),
        )
        return

    # Update history
    history.append({"role": "user", "content": message.text})
    history.append({"role": "assistant", "content": reply})

    # Keep only last 10 messages to avoid token overflow
    if len(history) > 20:
        history = history[-20:]

    data["advisor_history"] = history
    await state.set_data(data)

    # Send reply
    await message.answer(
        f"💬 <b>AI-советник:</b>\n\n{reply}",
        reply_markup=advisor_keyboard(),
    )


def _build_ml_context(data: dict) -> dict:
    """Build ML context dict from stored scoring results for the advisor."""
    result = data.get("last_scoring_result")
    features = data.get("last_scoring_features")

    if not result:
        return {
            "has_scoring": False,
            "note": "Пользователь ещё не проходил скоринг.",
        }

    # Extract top contributing features (positive = risky)
    contributions = result.get("shap_values", {}).get("feature_contributions", {})
    sorted_contribs = sorted(contributions.items(), key=lambda x: -x[1])

    feature_labels = {
        "age": "Возраст",
        "monthly_income": "Ежемесячный доход",
        "employment_years": "Стаж работы",
        "loan_amount": "Сумма кредита",
        "loan_term_months": "Срок кредита",
        "interest_rate": "Процентная ставка",
        "past_due_30d": "Просрочки 30+ дней",
        "inquiries_6m": "Кредитные запросы за 6 мес.",
    }

    return {
        "has_scoring": True,
        "decision": result["decision"],
        "probability_of_default": result["probability_of_default"],
        "credit_score": result["credit_score"],
        "risk_segment": result["risk_segment"]["label"],
        "threshold": result["threshold_used"],
        "features": {
            feature_labels.get(k, k): v
            for k, v in (features or {}).items()
        },
        "contributions": [
            {
                "feature": feature_labels.get(name, name),
                "raw_feature_name": name,
                "value": features.get(name, None) if features else None,
                "contribution": contrib,
                "direction": "увеличивает риск" if contrib > 0 else "снижает риск",
            }
            for name, contrib in sorted_contribs
        ],
    }


# ── Voice scoring ────────────────────────────────────────────

_FEATURE_LABELS_RU = {
    "age": "Возраст",
    "monthly_income": "Доход",
    "employment_years": "Стаж",
    "loan_amount": "Сумма кредита",
    "loan_term_months": "Срок (мес.)",
    "interest_rate": "Ставка (%)",
    "past_due_30d": "Просрочки",
    "inquiries_6m": "Запросы (6 мес.)",
}


@router.message(F.voice)
async def handle_voice(message: Message, state: FSMContext) -> None:
    """Handle voice messages — extract features via Gemini and score."""
    await message.answer("🎤 Обрабатываю голосовое сообщение...")

    try:
        # 1. Download voice file from Telegram
        voice = message.voice
        file = await message.bot.get_file(voice.file_id)
        from io import BytesIO
        voice_bytes = BytesIO()
        await message.bot.download_file(file.file_path, voice_bytes)
        voice_bytes.seek(0)

        # 2. Send to backend /api/v1/scoring/voice
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{BACKEND_URL}/api/v1/scoring/voice",
                files={"audio": ("voice.ogg", voice_bytes.read(), "audio/ogg")},
            )

        if resp.status_code == 422:
            error_detail = resp.json().get("detail", "Не удалось распознать данные")
            await message.answer(
                f"⚠️ {error_detail}\n\n"
                "Попробуйте сказать чётче, например:\n"
                "«Мне 28 лет, зарплата 80 тысяч, работаю 3 года, "
                "хочу кредит 500 тысяч на 2 года»",
                reply_markup=back_to_menu_keyboard(),
            )
            return

        resp.raise_for_status()
        result = resp.json()

    except Exception as e:
        logger.error("Voice scoring error: %s", e)
        await message.answer(
            "❌ Ошибка обработки голоса. Попробуйте ещё раз или используйте текстовый скоринг.",
            reply_markup=back_to_menu_keyboard(),
        )
        return

    # 3. Format extracted features
    extracted = result.get("extracted_features", {})
    features_text = "\n".join(
        f"  • {_FEATURE_LABELS_RU.get(k, k)}: <b>{v}</b>"
        for k, v in extracted.items()
        if k in _FEATURE_LABELS_RU
    )

    header = (
        "🎤 <b>Голосовой скоринг</b>\n\n"
        "📋 Распознанные данные:\n"
        f"{features_text}\n\n"
    )

    # 4. Format scoring result (reuse existing formatter)
    scoring_text = _format_scoring_result(result, extracted)

    await state.set_data({
        "last_scoring_result": result,
        "last_scoring_features": extracted,
        "advisor_history": [],
    })

    await message.answer(header + scoring_text, reply_markup=score_again_keyboard())
