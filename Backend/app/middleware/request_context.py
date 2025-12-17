from __future__ import annotations

from zoneinfo import ZoneInfo

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.core.response import err


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Injects:
      - request.state.request_id
      - request.state.client_timezone

    Strict rules (Sprint 01):
      - X-Request-Id is REQUIRED (no server-side generation)
      - X-Timezone is REQUIRED and must be valid IANA
      - Both headers are echoed back in every response
    """

    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-Id")
        if not req_id:
            return JSONResponse(
                status_code=400,
                content=err(request, "missing_request_id", "X-Request-Id header is required"),
            )

        tz = request.headers.get("X-Timezone")
        if not tz:
            return JSONResponse(
                status_code=400,
                content=err(request, "invalid_timezone", "X-Timezone header is required"),
                headers={"X-Request-Id": req_id},
            )

        try:
            ZoneInfo(tz)
        except Exception:
            return JSONResponse(
                status_code=400,
                content=err(request, "invalid_timezone", "Invalid X-Timezone header"),
                headers={"X-Request-Id": req_id},
            )

        request.state.request_id = req_id
        request.state.client_timezone = tz

        response: Response = await call_next(request)
        response.headers["X-Request-Id"] = req_id
        response.headers["X-Timezone"] = tz
        return response
