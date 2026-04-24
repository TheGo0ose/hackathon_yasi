"""
Scoring router — POST /api/v1/scoring/predict

Accepts loan application data, runs it through the scoring pipeline,
and returns a decision + probability + SHAP values.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import ScorerDep, SettingsDep
from app.schemas.scoring import ScoringRequest, ScoringResponse
from app.services.scoring_service import ScoringService

router = APIRouter(prefix="/scoring", tags=["scoring"])


@router.post(
    "/predict",
    response_model=ScoringResponse,
    summary="Скоринг кредитной заявки",
    description=(
        "Принимает 8 признаков заёмщика, возвращает бинарное решение "
        "(APPROVED / DECLINED), вероятность дефолта, кредитный скоринговый балл, "
        "риск-сегмент и SHAP-значения для отрисовки графиков влияния признаков."
    ),
)
async def predict(
    request: ScoringRequest,
    scorer: ScorerDep,
    settings: SettingsDep,
) -> ScoringResponse:
    service = ScoringService(scorer)
    return service.score(request, threshold=settings.default_threshold)
