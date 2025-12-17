from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.idempotency import IdempotencyKey


async def get(
    db: AsyncSession,
    *,
    user_id,
    key: str,
    method: str,
    path: str,
) -> IdempotencyKey | None:
    res = await db.execute(
        select(IdempotencyKey).where(
            IdempotencyKey.user_id == user_id,
            IdempotencyKey.key == key,
            IdempotencyKey.method == method,
            IdempotencyKey.path == path,
        )
    )
    return res.scalar_one_or_none()


async def claim(
    db: AsyncSession,
    *,
    user_id,
    key: str,
    method: str,
    path: str,
) -> bool:
    """
    Creates idempotency record if not exists.
    Returns:
      True  -> claimed by this request (new record inserted)
      False -> already exists (duplicate)
    """
    rec = IdempotencyKey(user_id=user_id, key=key, method=method, path=path)
    db.add(rec)
    try:
        await db.flush()
        return True
    except IntegrityError:
        return False


async def store_response(
    db: AsyncSession,
    *,
    user_id,
    key: str,
    method: str,
    path: str,
    status_code: int,
    response_body: dict,
    response_headers: dict | None = None,
) -> None:
    await db.execute(
        update(IdempotencyKey)
        .where(
            IdempotencyKey.user_id == user_id,
            IdempotencyKey.key == key,
            IdempotencyKey.method == method,
            IdempotencyKey.path == path,
        )
        .values(
            status_code=status_code,
            response_body=response_body,
            response_headers=response_headers or {},
        )
    )
