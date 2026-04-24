"""
Scoring router — POST /api/v1/scoring/predict  (single)
                  POST /api/v1/scoring/batch   (bulk CSV import)
"""

from __future__ import annotations

from typing import List

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


@router.post(
    "/batch",
    response_model=List[ScoringResponse],
    summary="Пакетный скоринг (CSV-импорт)",
    description="Принимает массив заявок, возвращает массив результатов.",
)
async def batch_predict(
    requests: List[ScoringRequest],
    scorer: ScorerDep,
    settings: SettingsDep,
) -> List[ScoringResponse]:
    service = ScoringService(scorer)
    return [
        service.score(req, threshold=settings.default_threshold)
        for req in requests
    ]
