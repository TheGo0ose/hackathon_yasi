"""
Scoring FSM — step-by-step collection of 8 features in chat.

Each step asks for one feature, validates the input, and moves to the next.
After all 8 features are collected, calls the backend API and shows the result.
"""

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class ScoringForm(StatesGroup):
    """FSM states for the scoring flow."""

    age = State()
    monthly_income = State()
    employment_years = State()
    loan_amount = State()
    loan_term_months = State()
    interest_rate = State()
    past_due_30d = State()
    inquiries_6m = State()


# Step definitions: (state, field_key, prompt, parser, validation_error_msg)
STEPS = [
    {
        "state": ScoringForm.age,
        "key": "age",
        "prompt": "👤 <b>Возраст заёмщика</b>\n\nВведите возраст (от 18 до 100 лет):",
        "parse": lambda t: int(t),
        "validate": lambda v: 18 <= v <= 100,
        "error": "Возраст должен быть целым числом от 18 до 100.",
    },
    {
        "state": ScoringForm.monthly_income,
        "key": "monthly_income",
        "prompt": "💰 <b>Ежемесячный доход (₽)</b>\n\nВведите сумму дохода в рублях:",
        "parse": lambda t: float(t.replace(",", ".").replace(" ", "")),
        "validate": lambda v: v > 0,
        "error": "Доход должен быть положительным числом.",
    },
    {
        "state": ScoringForm.employment_years,
        "key": "employment_years",
        "prompt": "🏢 <b>Стаж работы (лет)</b>\n\nВведите стаж на текущем месте работы:",
        "parse": lambda t: float(t.replace(",", ".")),
        "validate": lambda v: 0 <= v <= 50,
        "error": "Стаж должен быть от 0 до 50 лет.",
    },
    {
        "state": ScoringForm.loan_amount,
        "key": "loan_amount",
        "prompt": "🏦 <b>Сумма кредита (₽)</b>\n\nВведите запрашиваемую сумму кредита:",
        "parse": lambda t: float(t.replace(",", ".").replace(" ", "")),
        "validate": lambda v: v > 0,
        "error": "Сумма кредита должна быть положительным числом.",
    },
    {
        "state": ScoringForm.loan_term_months,
        "key": "loan_term_months",
        "prompt": "📅 <b>Срок кредита (месяцев)</b>\n\nВведите срок кредита (от 6 до 120 месяцев):",
        "parse": lambda t: int(t),
        "validate": lambda v: 6 <= v <= 120,
        "error": "Срок должен быть целым числом от 6 до 120.",
    },
    {
        "state": ScoringForm.interest_rate,
        "key": "interest_rate",
        "prompt": "📈 <b>Процентная ставка (%)</b>\n\nВведите годовую процентную ставку:",
        "parse": lambda t: float(t.replace(",", ".").replace("%", "")),
        "validate": lambda v: 0 < v <= 100,
        "error": "Ставка должна быть от 0 до 100%.",
    },
    {
        "state": ScoringForm.past_due_30d,
        "key": "past_due_30d",
        "prompt": "⚠️ <b>Просрочки 30+ дней</b>\n\nСколько раз были просрочки более 30 дней в кредитной истории?",
        "parse": lambda t: int(t),
        "validate": lambda v: v >= 0,
        "error": "Количество просрочек не может быть отрицательным.",
    },
    {
        "state": ScoringForm.inquiries_6m,
        "key": "inquiries_6m",
        "prompt": "🔍 <b>Кредитные запросы за 6 мес.</b>\n\nСколько запросов на кредит было за последние 6 месяцев?",
        "parse": lambda t: int(t),
        "validate": lambda v: v >= 0,
        "error": "Количество запросов не может быть отрицательным.",
    },
]
