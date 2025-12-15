from __future__ import annotations

from typing import Any

from fastapi import Request


def ok(request: Request, payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, "request_id": request.state.request_id}


def err(request: Request, code: str, message: str, details: Any | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {
        "error": {"code": code, "message": message},
        "request_id": request.state.request_id,
    }
    if details is not None:
        body["error"]["details"] = details
    return body
