"""
Dashboard router — POST /api/v1/dashboard/metrics

B2B endpoint protected by a static API key.
Recalculates business metrics for a given decision threshold.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import ApiKeyDep, ScorerDep
from app.schemas.dashboard import DashboardRequest, DashboardResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.post(
    "/metrics",
    response_model=DashboardResponse,
    summary="Бизнес-метрики при заданном пороге",
    description=(
        "Пересчитывает метрики качества и бизнес-KPI (approval rate, "
        "expected loss reduction, confusion matrix) на полном датасете "
        "(500 заявок) при заданном пороге отсечения.  "
        "Требует заголовок X-API-Key."
    ),
)
async def dashboard_metrics(
    request: DashboardRequest,
    _api_key: ApiKeyDep,
    scorer: ScorerDep,
) -> DashboardResponse:
    service = DashboardService(scorer)
    return service.compute_metrics(request)
