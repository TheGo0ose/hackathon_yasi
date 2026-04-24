"""
Scoring schemas — API contracts for the /scoring/predict endpoint.

These models are the single source of truth for:
  - what the frontend sends  (ScoringRequest)
  - what the backend returns (ScoringResponse)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Optional

from pydantic import BaseModel, Field


# ── Request ──────────────────────────────────────────────────

class ScoringRequest(BaseModel):
    """
    Loan application data submitted for scoring.

    8 mandatory features (matching the training dataset) plus
    optional alternative data fields for future model versions.
    """

    # === 8 core features (required) ===
    age: int = Field(
        ..., ge=18, le=100,
        description="Возраст заёмщика (полных лет)",
        json_schema_extra={"example": 29},
    )
    monthly_income: float = Field(
        ..., gt=0,
        description="Ежемесячный доход (₽)",
        json_schema_extra={"example": 320_000.0},
    )
    employment_years: float = Field(
        ..., ge=0, le=50,
        description="Стаж работы на текущем месте (лет)",
        json_schema_extra={"example": 3.5},
    )
    loan_amount: float = Field(
        ..., gt=0,
        description="Запрашиваемая сумма кредита (₽)",
        json_schema_extra={"example": 650_000.0},
    )
    loan_term_months: int = Field(
        ..., ge=6, le=120,
        description="Срок кредита (месяцев)",
        json_schema_extra={"example": 48},
    )
    interest_rate: float = Field(
        ..., gt=0, le=100,
        description="Процентная ставка (%)",
        json_schema_extra={"example": 33.0},
    )
    past_due_30d: int = Field(
        ..., ge=0,
        description="Количество просрочек 30+ дней в кредитной истории",
        json_schema_extra={"example": 2},
    )
    inquiries_6m: int = Field(
        ..., ge=0,
        description="Количество кредитных запросов за последние 6 месяцев",
        json_schema_extra={"example": 4},
    )

    # === Optional alternative data ===
    has_property: Optional[bool] = Field(
        None, description="Наличие недвижимости в собственности",
    )
    has_vehicle: Optional[bool] = Field(
        None, description="Наличие автомобиля",
    )
    education_level: Optional[str] = Field(
        None, description="Уровень образования (среднее / высшее / магистратура)",
    )
    marital_status: Optional[str] = Field(
        None, description="Семейное положение (холост / женат / разведён)",
    )

    def to_feature_dict(self) -> Dict[str, float]:
        """
        Extract only the 8 model features as a flat dict.

        This is what gets passed to ``AbstractScorer.predict()``.
        """
        return {
            "age": float(self.age),
            "monthly_income": self.monthly_income,
            "employment_years": self.employment_years,
            "loan_amount": self.loan_amount,
            "loan_term_months": float(self.loan_term_months),
            "interest_rate": self.interest_rate,
            "past_due_30d": float(self.past_due_30d),
            "inquiries_6m": float(self.inquiries_6m),
        }


# ── Response components ──────────────────────────────────────

class ShapValues(BaseModel):
    """SHAP explanation — used by the frontend to render waterfall / bar charts."""

    base_value: float = Field(
        ...,
        description="Базовое значение модели — средний P(default) на обучающей выборке",
    )
    feature_contributions: Dict[str, float] = Field(
        ...,
        description=(
            "Вклад каждого признака в предсказание (SHAP value).  "
            "Положительное значение → увеличивает вероятность дефолта, "
            "отрицательное → уменьшает."
        ),
    )


class RiskSegment(BaseModel):
    """Risk category for visual styling in the UI."""

    label: str = Field(..., description="low / medium / high / critical")
    color: str = Field(..., description="HEX-цвет для UI-отображения")
    description: str = Field(..., description="Человекочитаемое описание сегмента")


# ── Main response ────────────────────────────────────────────

class ScoringResponse(BaseModel):
    """
    Full scoring result returned to the client.

    Contains the binary decision, probability, credit score,
    risk segment, and XAI data for chart rendering.
    """

    # Core result
    decision: str = Field(
        ...,
        description="APPROVED — кредит одобрен, DECLINED — отказ",
    )
    probability_of_default: float = Field(
        ..., ge=0, le=1,
        description="Вероятность дефолта P(default) ∈ [0, 1]",
    )
    credit_score: int = Field(
        ..., ge=300, le=850,
        description="Кредитный скоринговый балл (шкала FICO: 300–850)",
    )
    risk_segment: RiskSegment

    # XAI
    shap_values: ShapValues

    # Meta
    model_version: str = Field(..., description="Версия используемой модели")
    scored_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Время выполнения скоринга (UTC)",
    )
    threshold_used: float = Field(
        default=0.5,
        description="Порог P(default), использованный для бинарного решения",
    )

    model_config = {"protected_namespaces": ()}
