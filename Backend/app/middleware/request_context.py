from __future__ import annotations

import uuid
from zoneinfo import ZoneInfo

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import settings


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Injects:
    - request.state.request_id
    - request.state.client_timezone (IANA)

    Rules:
    - If `X-Request-Id` header is present, use it.
    - Else generate UUID.
    - Timezone from `X-Timezone` header (IANA). If invalid/absent, fallback to DEFAULT_TIMEZONE.

    Adds `X-Request-Id` and `X-Timezone` to every response.
    """

    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        tz = request.headers.get("X-Timezone") or settings.DEFAULT_TIMEZONE
        try:
            # Validate timezone
            ZoneInfo(tz)
        except Exception:
            tz = settings.DEFAULT_TIMEZONE

        request.state.request_id = req_id
        request.state.client_timezone = tz

        response: Response = await call_next(request)
        response.headers["X-Request-Id"] = req_id
        response.headers["X-Timezone"] = tz
        return response
