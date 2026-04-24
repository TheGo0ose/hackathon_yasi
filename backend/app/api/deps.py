"""
FastAPI dependency injection providers.

Usage in routers:
    from app.api.deps import ScorerDep, SettingsDep

    @router.post("/predict")
    async def predict(request: ScoringRequest, scorer: ScorerDep):
        ...
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException

from app.config import Settings, settings
from app.ml_inference.base import AbstractScorer


# ── Settings ─────────────────────────────────────────────────

def get_settings() -> Settings:
    """Return the global settings singleton."""
    return settings


SettingsDep = Annotated[Settings, Depends(get_settings)]


# ── Scorer ───────────────────────────────────────────────────

def get_scorer() -> AbstractScorer:
    """
    Return the scorer initialised during app lifespan.

    Import the function from main to avoid circular deps.
    """
    from app.main import get_scorer as _get_scorer
    return _get_scorer()


ScorerDep = Annotated[AbstractScorer, Depends(get_scorer)]


# ── API Key guard (for B2B dashboard) ────────────────────────

def require_api_key(
    x_api_key: str = Header(..., description="Статический API-ключ для B2B-дашборда"),
) -> str:
    """
    Validate the X-API-Key header against the configured secret.

    Raises 401 if the key is missing or incorrect.
    """
    if x_api_key != settings.dashboard_api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key",
        )
    return x_api_key


ApiKeyDep = Annotated[str, Depends(require_api_key)]
