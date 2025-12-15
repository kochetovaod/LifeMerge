from __future__ import annotations

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.response import err
from app.db.session import get_db
from app.models.idempotency import IdempotencyKey
from app.models.user import User


async def enforce_idempotency(
    request: Request,
    current_user: User,
    db: AsyncSession,
    request_id: str | None,
    idempotency_key: str | None,
) -> None:
    key = idempotency_key or request_id
    if not key:
        raise HTTPException(status_code=400, detail=err(request, "validation_error", "request_id or X-Idempotency-Key is required"))

    rec = IdempotencyKey(user_id=current_user.id, key=key, method=request.method, path=request.url.path)
    db.add(rec)
    try:
        await db.flush()
    except IntegrityError:
        # repeated request; in full impl we'd return stored response
        raise HTTPException(status_code=409, detail=err(request, "idempotency_conflict", "Duplicate request_id/X-Idempotency-Key"))


async def idempotency_dependency(
    request: Request,
    current_user: User,
    db: AsyncSession = Depends(get_db),
    x_idempotency_key: str | None = Header(default=None, alias="X-Idempotency-Key"),
) -> None:
    # request_id typically supplied in body, but FastAPI can't access it generically here.
    # Each handler should pass the body.request_id into enforce_idempotency.
    await enforce_idempotency(request, current_user, db, request_id=None, idempotency_key=x_idempotency_key)
