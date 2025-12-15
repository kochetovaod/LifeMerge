from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.response import err
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=401, detail=err(request, "unauthorized", "Missing bearer token"))

    try:
        payload = decode_token(creds.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail=err(request, "unauthorized", "Invalid token"))

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail=err(request, "unauthorized", "Invalid token type"))

    raw_uid = payload.get("uid")
    if not raw_uid:
        raise HTTPException(status_code=401, detail=err(request, "unauthorized", "Invalid token payload"))

    try:
        uid = uuid.UUID(str(raw_uid))
    except Exception:
        raise HTTPException(status_code=401, detail=err(request, "unauthorized", "Invalid token payload"))

    res = await db.execute(select(User).where(User.id == uid, User.deleted == False))  # noqa: E712
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail=err(request, "unauthorized", "User not found"))
    return user
