from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inbox_item import InboxItem


async def list(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    updated_from: datetime | None,
    cursor: str | None,
    limit: int,
) -> tuple[list[InboxItem], str | None]:
    q = select(InboxItem).where(InboxItem.user_id == user_id, InboxItem.deleted == False)  # noqa: E712
    if updated_from:
        q = q.where(InboxItem.updated_at >= updated_from)

    if cursor:
        try:
            ts_str, id_str = cursor.split("|")
            ts = datetime.fromisoformat(ts_str)
            cid = uuid.UUID(id_str)
            q = q.where((InboxItem.updated_at, InboxItem.id) < (ts, cid))
        except Exception:
            pass

    q = q.order_by(InboxItem.updated_at.desc(), InboxItem.id.desc()).limit(max(1, min(limit, 100)) + 1)
    res = await db.execute(q)
    rows = res.scalars().all()

    next_cursor = None
    if len(rows) > limit:
        last = rows[limit - 1]
        next_cursor = f"{last.updated_at.isoformat()}|{last.id}"
        rows = rows[:limit]

    return rows, next_cursor


async def get_by_id(db: AsyncSession, *, user_id: uuid.UUID, item_id: uuid.UUID) -> InboxItem | None:
    res = await db.execute(select(InboxItem).where(InboxItem.id == item_id, InboxItem.user_id == user_id, InboxItem.deleted == False))  # noqa: E712
    return res.scalar_one_or_none()


async def create(db: AsyncSession, item: InboxItem) -> InboxItem:
    db.add(item)
    await db.flush()
    return item


async def patch(db: AsyncSession, *, item_id: uuid.UUID, values: dict) -> None:
    await db.execute(update(InboxItem).where(InboxItem.id == item_id).values(**values))
