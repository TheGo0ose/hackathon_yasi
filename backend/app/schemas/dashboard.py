"""
Dashboard schemas — API contracts for the /dashboard/metrics endpoint.

The B2B dashboard allows adjusting the decision threshold and
seeing how business metrics change in response.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ── Request ──────────────────────────────────────────────────

class DashboardRequest(BaseModel):
    """Threshold adjustment request from the B2B dashboard."""

    threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description=(
            "Порог отсечения P(default).  "
            "Заявки с P(default) >= threshold будут отклонены."
        ),
        json_schema_extra={"example": 0.5},
    )


# ── Response components ──────────────────────────────────────

class ConfusionMetrics(BaseModel):
    """Classic confusion matrix counts."""

    true_positives: int = Field(..., description="Верно предсказанные дефолты")
    true_negatives: int = Field(..., description="Верно предсказанные не-дефолты")
    false_positives: int = Field(..., description="Ложно предсказанные дефолты (упущенная прибыль)")
    false_negatives: int = Field(..., description="Пропущенные дефолты (убыток)")


# ── Main response ────────────────────────────────────────────

class DashboardResponse(BaseModel):
    """
    Business metrics recalculated for the given threshold.

    All metrics are computed over the full dataset (500 applications).
    """

    threshold: float = Field(..., description="Использованный порог")

    # Business KPIs
    approval_rate: float = Field(
        ...,
        description="Доля одобренных заявок (P(default) < threshold)",
    )
    default_rate_in_approved: float = Field(
        ...,
        description="Доля реальных дефолтов среди одобренных (risk exposure)",
    )
    expected_loss_reduction: float = Field(
        ...,
        description=(
            "Снижение потерь (%) по сравнению со стратегией 'одобрить всех'"
        ),
    )

    # ML Quality metrics
    roc_auc: float = Field(..., description="ROC-AUC модели на полном датасете")
    pr_auc: float = Field(..., description="PR-AUC модели на полном датасете")
    accuracy: float = Field(..., description="Accuracy при данном пороге")
    precision: float = Field(..., description="Precision при данном пороге")
    recall: float = Field(..., description="Recall при данном пороге")
    f1_score: float = Field(..., description="F1-score при данном пороге")

    # Confusion matrix
    confusion: ConfusionMetrics

    # Dataset info
    total_applications: int = Field(..., description="Общее число заявок в датасете")
    total_defaults: int = Field(..., description="Общее число дефолтов в датасете")
