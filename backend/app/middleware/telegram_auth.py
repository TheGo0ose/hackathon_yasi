"""
Telegram Mini App authentication middleware.

Validates the cryptographic signature (HMAC-SHA256) of ``initData``
sent by the Telegram Web App client.

Protocol reference:
    https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app

Flow:
    1. Client sends ``X-Telegram-Init-Data`` header with the raw initData string.
    2. This middleware intercepts every ``/api/`` request.
    3. If the header is present → validate signature + freshness.
    4. If the header is absent → pass through (request comes from web/desktop).
    5. On validation failure → 401 Unauthorized.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from urllib.parse import parse_qs, unquote

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class TelegramAuthMiddleware(BaseHTTPMiddleware):
    """
    Starlette middleware that validates Telegram Mini App ``initData``.

    Args:
        app:               The ASGI application.
        bot_token:         Telegram Bot API token (from BotFather).
        max_age_seconds:   Maximum allowed age of ``auth_date`` (default: 24h).
        bypass_prefixes:   URL prefixes that skip validation entirely.
    """

    def __init__(
        self,
        app,
        bot_token: str,
        max_age_seconds: int = 86_400,
        bypass_prefixes: tuple[str, ...] = ("/docs", "/redoc", "/openapi.json"),
    ) -> None:
        super().__init__(app)
        self._bot_token = bot_token
        self._max_age = max_age_seconds
        self._bypass = bypass_prefixes

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip non-API routes and documentation
        if not path.startswith("/api/") or path.startswith(self._bypass):
            return await call_next(request)

        # Extract the header
        init_data = request.headers.get("X-Telegram-Init-Data")

        # No header → not a Telegram request, let it through
        # (web/desktop clients use other auth or no auth)
        if not init_data:
            return await call_next(request)

        # Validate the cryptographic signature
        is_valid, error_msg, user_data = self._validate_init_data(init_data)

        if not is_valid:
            logger.warning(
                "Telegram auth failed for %s %s: %s",
                request.method, path, error_msg,
            )
            return JSONResponse(
                status_code=401,
                content={"detail": f"Telegram auth failed: {error_msg}"},
            )

        # Attach parsed Telegram user info to request state
        # so downstream handlers can access it via request.state.tg_user
        request.state.tg_user = user_data
        logger.debug("Telegram auth OK for user %s", user_data.get("id"))

        return await call_next(request)

    def _validate_init_data(
        self, init_data: str
    ) -> tuple[bool, str, dict]:
        """
        Validate initData per Telegram's algorithm.

        Returns:
            (is_valid, error_message, parsed_user_dict)
        """
        try:
            # 1. Parse query-string into key-value pairs
            parsed = parse_qs(init_data, keep_blank_values=True)

            # 2. Extract and remove 'hash'
            hash_list = parsed.pop("hash", [None])
            received_hash = hash_list[0] if hash_list else None
            if not received_hash:
                return False, "missing hash parameter", {}

            # 3. Check auth_date freshness (replay attack protection)
            auth_date_list = parsed.get("auth_date", ["0"])
            try:
                auth_date = int(auth_date_list[0])
            except (ValueError, IndexError):
                return False, "invalid auth_date", {}

            age = time.time() - auth_date
            if age > self._max_age:
                return False, f"initData expired ({int(age)}s > {self._max_age}s)", {}

            if auth_date == 0:
                return False, "auth_date is zero", {}

            # 4. Build the data-check-string:
            #    - sort pairs alphabetically by key
            #    - join as "key=value\nkey=value"
            data_check_string = "\n".join(
                f"{key}={unquote(values[0])}"
                for key, values in sorted(parsed.items())
            )

            # 5. Compute secret key: HMAC-SHA256("WebAppData", bot_token)
            secret_key = hmac.new(
                key=b"WebAppData",
                msg=self._bot_token.encode("utf-8"),
                digestmod=hashlib.sha256,
            ).digest()

            # 6. Compute expected hash: HMAC-SHA256(secret_key, data_check_string)
            calculated_hash = hmac.new(
                key=secret_key,
                msg=data_check_string.encode("utf-8"),
                digestmod=hashlib.sha256,
            ).hexdigest()

            # 7. Constant-time comparison
            if not hmac.compare_digest(calculated_hash, received_hash):
                return False, "signature mismatch", {}

            # 8. Parse user JSON if present
            user_data = {}
            user_json = parsed.get("user", [None])
            if user_json and user_json[0]:
                try:
                    user_data = json.loads(unquote(user_json[0]))
                except (json.JSONDecodeError, TypeError):
                    pass  # user field is optional

            return True, "", user_data

        except Exception as exc:
            logger.exception("Unexpected error in Telegram auth validation")
            return False, f"internal error: {exc}", {}
