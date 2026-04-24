"""
Tests for POST /api/v1/scoring/predict.

Verifies request validation, response structure, mock scoring logic,
and edge cases.
"""

import pytest
from tests.conftest import VALID_APPLICATION, HIGH_RISK_APPLICATION


@pytest.mark.anyio
async def test_predict_success(client):
    """Valid application → 200 with full response structure."""
    resp = await client.post("/api/v1/scoring/predict", json=VALID_APPLICATION)
    assert resp.status_code == 200

    data = resp.json()
    assert data["decision"] in ("APPROVED", "DECLINED")
    assert 0 <= data["probability_of_default"] <= 1
    assert 300 <= data["credit_score"] <= 850
    assert data["risk_segment"]["label"] in ("low", "medium", "high", "critical")
    assert data["risk_segment"]["color"].startswith("#")
    assert isinstance(data["model_version"], str) and len(data["model_version"]) > 0
    assert 0 < data["threshold_used"] < 1

    # SHAP structure
    shap = data["shap_values"]
    assert "base_value" in shap
    assert len(shap["feature_contributions"]) == 8


@pytest.mark.anyio
async def test_predict_high_risk(client):
    """High-risk application → higher probability, likely DECLINED."""
    resp = await client.post("/api/v1/scoring/predict", json=HIGH_RISK_APPLICATION)
    assert resp.status_code == 200

    data = resp.json()
    assert data["probability_of_default"] > 0.25
    assert data["decision"] == "DECLINED"
    assert data["risk_segment"]["label"] in ("medium", "high", "critical")


@pytest.mark.anyio
async def test_predict_deterministic(client):
    """Same input → same output (mock is deterministic)."""
    resp1 = await client.post("/api/v1/scoring/predict", json=VALID_APPLICATION)
    resp2 = await client.post("/api/v1/scoring/predict", json=VALID_APPLICATION)
    assert resp1.json()["probability_of_default"] == resp2.json()["probability_of_default"]
    assert resp1.json()["credit_score"] == resp2.json()["credit_score"]


@pytest.mark.anyio
async def test_predict_missing_field(client):
    """Missing required field → 422."""
    incomplete = {k: v for k, v in VALID_APPLICATION.items() if k != "age"}
    resp = await client.post("/api/v1/scoring/predict", json=incomplete)
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_predict_invalid_age(client):
    """Age < 18 → 422 validation error."""
    bad = {**VALID_APPLICATION, "age": 10}
    resp = await client.post("/api/v1/scoring/predict", json=bad)
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_predict_negative_income(client):
    """Negative income → 422 validation error."""
    bad = {**VALID_APPLICATION, "monthly_income": -5000}
    resp = await client.post("/api/v1/scoring/predict", json=bad)
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_predict_with_optional_fields(client):
    """Optional alt-data fields should be accepted and not break scoring."""
    extended = {
        **VALID_APPLICATION,
        "has_property": True,
        "has_vehicle": False,
        "education_level": "высшее",
        "marital_status": "женат",
    }
    resp = await client.post("/api/v1/scoring/predict", json=extended)
    assert resp.status_code == 200
