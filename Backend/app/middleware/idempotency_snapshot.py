from __future__ import annotations

import json
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.response import err
from app.db.session import async_session_maker
from app.repositories import idempotency_repo


_MUTATING = {"POST", "PATCH", "DELETE"}


class IdempotencySnapshotMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method not in _MUTATING:
            return await call_next(request)

        # key source: prefer X-Idempotency-Key, fallback X-Request-Id
        key = request.headers.get("X-Idempotency-Key") or request.headers.get("X-Request-Id")
        if not key:
            return JSONResponse(
                status_code=400,
                content=err(request, "missing_request_id", "X-Request-Id or X-Idempotency-Key is required"),
            )

        # user_id needed: we only do snapshot AFTER auth runs for protected routes.
        # For public auth routes you can still snapshot by user_id=None, but requirement is for Tasks.
        user_id = getattr(request.state, "user_id", None)
        if user_id is None:
            # If endpoint is public, just pass through (Auth endpoints can have their own strategy).
            return await call_next(request)

        method = request.method
        path = request.url.path

        async with async_session_maker() as db:
            existing = await idempotency_repo.get(db, user_id=user_id, key=key, method=method, path=path)
            if existing and existing.status_code is not None and existing.response_body is not None:
                headers = dict(existing.response_headers or {})
                headers.setdefault("X-Request-Id", request.headers.get("X-Request-Id", ""))
                headers.setdefault("X-Idempotency-Key", request.headers.get("X-Idempotency-Key", ""))
                return JSONResponse(status_code=existing.status_code, content=existing.response_body, headers=headers)

            # claim (insert stub)
            claimed = await idempotency_repo.claim(db, user_id=user_id, key=key, method=method, path=path)
            # If duplicate but no snapshot yet -> allow one in-flight request to finish.
            # For MVP: we don't block; second request will run and store same snapshot.
            await db.commit()

        # execute handler
        response = await call_next(request)

        # capture JSON response bodies only (project responses are JSON via ok/err)
        body_bytes = b""
        async for chunk in response.body_iterator:
            body_bytes += chunk

        # re-create response because body_iterator is consumed
        try:
            body_obj: Any = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except Exception:
            body_obj = {}

        new_headers = dict(response.headers)
        # keep request_id echo
        if "X-Request-Id" in request.headers:
            new_headers["X-Request-Id"] = request.headers["X-Request-Id"]

        async with async_session_maker() as db:
            await idempotency_repo.store_response(
                db,
                user_id=user_id,
                key=key,
                method=method,
                path=path,
                status_code=response.status_code,
                response_body=body_obj if isinstance(body_obj, dict) else {"data": body_obj},
                response_headers={
                    # store only safe headers needed for clients (extend if needed)
                    "X-Request-Id": new_headers.get("X-Request-Id", ""),
                },
            )
            await db.commit()

        return Response(content=body_bytes, status_code=response.status_code, headers=new_headers, media_type=response.media_type)
