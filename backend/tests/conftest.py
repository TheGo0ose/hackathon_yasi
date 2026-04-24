"""
Shared test fixtures for the Credit Scoring API test suite.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app, lifespan


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """
    Async HTTP client wired directly to the FastAPI app.
    Triggers lifespan events so the scorer is initialised.
    """
    async with lifespan(app):
        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


# ── Reusable test data ───────────────────────────────────────

VALID_APPLICATION = {
    "age": 29,
    "monthly_income": 320_000.0,
    "employment_years": 3.5,
    "loan_amount": 650_000.0,
    "loan_term_months": 48,
    "interest_rate": 33.0,
    "past_due_30d": 2,
    "inquiries_6m": 4,
}

HIGH_RISK_APPLICATION = {
    "age": 21,
    "monthly_income": 15_000.0,
    "employment_years": 0.5,
    "loan_amount": 900_000.0,
    "loan_term_months": 60,
    "interest_rate": 38.0,
    "past_due_30d": 5,
    "inquiries_6m": 8,
}

DASHBOARD_API_KEY = "hackathon-secret-key-2026"
