"""
FastAPI application entry point.

Run:
    uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.ml_inference import MockScorer, RealScorer
from app.ml_inference.base import AbstractScorer

# ── Logging ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ── Scorer singleton (set during lifespan) ───────────────────
_scorer: AbstractScorer | None = None


def get_scorer() -> AbstractScorer:
    """Return the global scorer instance.  Used by dependency injection."""
    if _scorer is None:
        raise RuntimeError("Scorer has not been initialised — app not started?")
    return _scorer


# ── Lifespan ─────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Startup:  initialise the scorer (mock or real).
    Shutdown: nothing to clean up for now.
    """
    global _scorer

    if settings.use_mock_scorer:
        logger.info("Using MockScorer (USE_MOCK_SCORER=true)")
        scorer = MockScorer()
        scorer.load_model("")  # no-op for mock
    else:
        logger.info("Loading real model from %s", settings.model_path)
        scorer = RealScorer()
        scorer.load_model(settings.model_path)

    _scorer = scorer
    logger.info(
        "Scorer ready  ·  version=%s  ·  base_value=%.3f",
        scorer.get_model_version(),
        scorer.get_base_value(),
    )

    yield  # ← application runs here

    logger.info("Shutting down")


# ── App factory ──────────────────────────────────────────────
app = FastAPI(
    title="Credit Scoring API",
    description=(
        "REST API для кредитного скоринга.  "
        "Принимает 8 признаков заявки, возвращает решение, "
        "вероятность дефолта и XAI-метрики (SHAP)."
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── CORS ─────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Telegram Mini App auth ───────────────────────────────────
from app.middleware.telegram_auth import TelegramAuthMiddleware  # noqa: E402

app.add_middleware(
    TelegramAuthMiddleware,
    bot_token=settings.bot_token,
)


# ── Health endpoint ──────────────────────────────────────────
@app.get("/api/v1/health", tags=["system"])
async def health():
    """Healthcheck — confirms the API is live and which scorer is active."""
    scorer = get_scorer()
    return {
        "status": "ok",
        "model_version": scorer.get_model_version(),
        "scorer_type": "mock" if settings.use_mock_scorer else "real",
    }


# ── Router registration ──────────────────────────────────────
from app.api.v1.router import api_v1_router  # noqa: E402

app.include_router(api_v1_router, prefix="/api/v1")
