"""
Tests for POST /api/v1/dashboard/metrics.

Verifies API-key auth, response structure, and threshold behavior.
"""

import pytest
from tests.conftest import DASHBOARD_API_KEY


def _headers(key: str | None = None) -> dict:
    if key is None:
        return {}
    return {"X-API-Key": key}


@pytest.mark.anyio
async def test_dashboard_success(client):
    """Valid request with correct API key → 200."""
    resp = await client.post(
        "/api/v1/dashboard/metrics",
        json={"threshold": 0.5},
        headers=_headers(DASHBOARD_API_KEY),
    )
    assert resp.status_code == 200

    data = resp.json()
    assert 0 <= data["approval_rate"] <= 1
    assert 0 <= data["default_rate_in_approved"] <= 1
    assert 0 <= data["roc_auc"] <= 1
    assert data["total_applications"] == 500
    assert data["total_defaults"] > 0

    # Confusion matrix sanity
    c = data["confusion"]
    total = c["true_positives"] + c["true_negatives"] + c["false_positives"] + c["false_negatives"]
    assert total == 500


@pytest.mark.anyio
async def test_dashboard_no_api_key(client):
    """Missing X-API-Key header → 422."""
    resp = await client.post(
        "/api/v1/dashboard/metrics",
        json={"threshold": 0.5},
    )
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_dashboard_wrong_api_key(client):
    """Wrong API key → 401."""
    resp = await client.post(
        "/api/v1/dashboard/metrics",
        json={"threshold": 0.5},
        headers=_headers("wrong-key"),
    )
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_dashboard_default_threshold(client):
    """Omit threshold → uses default 0.5."""
    resp = await client.post(
        "/api/v1/dashboard/metrics",
        json={},
        headers=_headers(DASHBOARD_API_KEY),
    )
    assert resp.status_code == 200
    assert resp.json()["threshold"] == 0.5


@pytest.mark.anyio
async def test_dashboard_strict_threshold_raises_approval(client):
    """Lower threshold → fewer approvals (more strict filtering)."""
    resp_loose = await client.post(
        "/api/v1/dashboard/metrics",
        json={"threshold": 0.8},
        headers=_headers(DASHBOARD_API_KEY),
    )
    resp_strict = await client.post(
        "/api/v1/dashboard/metrics",
        json={"threshold": 0.2},
        headers=_headers(DASHBOARD_API_KEY),
    )
    assert resp_loose.status_code == 200
    assert resp_strict.status_code == 200
    assert resp_loose.json()["approval_rate"] >= resp_strict.json()["approval_rate"]


@pytest.mark.anyio
async def test_dashboard_loss_reduction_increases_with_strictness(client):
    """Stricter threshold → higher loss reduction."""
    resp_loose = await client.post(
        "/api/v1/dashboard/metrics",
        json={"threshold": 0.8},
        headers=_headers(DASHBOARD_API_KEY),
    )
    resp_strict = await client.post(
        "/api/v1/dashboard/metrics",
        json={"threshold": 0.2},
        headers=_headers(DASHBOARD_API_KEY),
    )
    assert resp_strict.json()["expected_loss_reduction"] >= resp_loose.json()["expected_loss_reduction"]
