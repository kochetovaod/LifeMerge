from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.idempotency import IdempotencyKey


async def insert_key(
    db: AsyncSession,
    *,
    user_id,
    key: str,
    method: str,
    path: str,
) -> bool:
    """
    Returns:
      True  -> first time seen (insert ok)
      False -> duplicate (unique constraint hit)
    """
    rec = IdempotencyKey(user_id=user_id, key=key, method=method, path=path)
    db.add(rec)
    try:
        await db.flush()
        return True
    except IntegrityError:
        return False
