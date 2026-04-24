"""
Handlers for the credit scoring Telegram bot.

- /start → main menu
- "Быстрый скоринг" → FSM flow (8 steps)
- "О проекте" → info
- Cancel → back to menu
"""

from __future__ import annotations

import logging

import httpx
from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import BACKEND_URL
from keyboards import (
    back_to_menu_keyboard,
    cancel_keyboard,
    main_menu_keyboard,
    score_again_keyboard,
)
from states import STEPS, ScoringForm

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
    "🏦 <b>Credit Scoring Bot</b>\n\n"
    "Добро пожаловать! Я помогу оценить кредитоспособность заёмщика.\n\n"
    "• <b>Открыть скоринг</b> — веб-интерфейс с графиками\n"
    "• <b>Быстрый скоринг</b> — ответьте на 8 вопросов прямо в чате\n"
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
    "ℹ️ <b>О проекте</b>\n\n"
    "Система кредитного скоринга на базе ML.\n\n"
    "• Модель: L2 Logistic Regression (NumPy)\n"
    "• ROC-AUC: 0.827 на holdout-выборке\n"
    "• 8 признаков заёмщика → P(default) + FICO Score\n"
    "• XAI: вклад каждого признака в решение\n\n"
    "Разработано на хакатоне 2026 🚀"
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
@router.message(ScoringForm)
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
        await _call_scoring_api(message, data["features"])


# ── API call & result formatting ─────────────────────────────

async def _call_scoring_api(message: Message, features: dict) -> None:
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
