"""
Tests for the Telegram Mini App authentication middleware.

Verifies HMAC-SHA256 signature validation, expiry checks,
and pass-through behavior for non-Telegram requests.
"""

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest

# The test bot token (matches .env.example)
TEST_BOT_TOKEN = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"


def _build_init_data(
    bot_token: str = TEST_BOT_TOKEN,
    auth_date: int | None = None,
    user: dict | None = None,
    tamper_hash: bool = False,
) -> str:
    """
    Build a valid Telegram initData string with correct HMAC signature.

    Args:
        bot_token:   Bot token used to compute the secret.
        auth_date:   Unix timestamp (default: now).
        user:        User dict to include (default: test user).
        tamper_hash: If True, corrupt the hash to simulate tampering.
    """
    if auth_date is None:
        auth_date = int(time.time())
    if user is None:
        user = {"id": 12345, "first_name": "Test", "username": "testuser"}

    params = {
        "auth_date": str(auth_date),
        "user": json.dumps(user, separators=(",", ":")),
        "query_id": "AAHdF6IaAAAAAADdF6ICZQ",
    }

    # Build data-check-string (sorted key=value pairs joined by \n)
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(params.items())
    )

    # Secret key = HMAC-SHA256("WebAppData", bot_token)
    secret_key = hmac.new(
        b"WebAppData", bot_token.encode(), hashlib.sha256
    ).digest()

    # Hash = HMAC-SHA256(secret_key, data_check_string)
    hash_value = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if tamper_hash:
        hash_value = "0" * 64  # obviously wrong

    params["hash"] = hash_value
    return urlencode(params)


# ── Test cases ───────────────────────────────────────────────

@pytest.mark.anyio
async def test_no_telegram_header_passes_through(client):
    """Requests without X-Telegram-Init-Data should pass through."""
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200


@pytest.mark.anyio
async def test_valid_init_data_passes(client):
    """Valid Telegram initData → request goes through to the endpoint."""
    init_data = _build_init_data()
    resp = await client.get(
        "/api/v1/health",
        headers={"X-Telegram-Init-Data": init_data},
    )
    assert resp.status_code == 200


@pytest.mark.anyio
async def test_tampered_hash_rejected(client):
    """Tampered hash → 401."""
    init_data = _build_init_data(tamper_hash=True)
    resp = await client.get(
        "/api/v1/health",
        headers={"X-Telegram-Init-Data": init_data},
    )
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_expired_init_data_rejected(client):
    """auth_date older than 24h → 401."""
    old_date = int(time.time()) - 100_000  # ~27 hours ago
    init_data = _build_init_data(auth_date=old_date)
    resp = await client.get(
        "/api/v1/health",
        headers={"X-Telegram-Init-Data": init_data},
    )
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_wrong_bot_token_rejected(client):
    """initData signed with a different bot token → 401."""
    init_data = _build_init_data(bot_token="999999:WRONG-TOKEN")
    resp = await client.get(
        "/api/v1/health",
        headers={"X-Telegram-Init-Data": init_data},
    )
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_missing_hash_rejected(client):
    """initData without hash parameter → 401."""
    init_data = urlencode({"auth_date": str(int(time.time())), "user": "{}"})
    resp = await client.get(
        "/api/v1/health",
        headers={"X-Telegram-Init-Data": init_data},
    )
    assert resp.status_code == 401
