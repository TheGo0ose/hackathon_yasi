"""
Aggregated v1 API router.

Mounts all v1 sub-routers under a single prefix.
"""

from fastapi import APIRouter

from app.api.v1.scoring import router as scoring_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.advisor import router as advisor_router

api_v1_router = APIRouter()

api_v1_router.include_router(scoring_router)
api_v1_router.include_router(dashboard_router)
api_v1_router.include_router(advisor_router, prefix="/advisor", tags=["advisor"])
