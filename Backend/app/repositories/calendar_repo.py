from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calendar_event import CalendarEvent


async def list(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    updated_from: datetime | None,
    start_from: datetime | None,
    start_to: datetime | None,
    cursor: str | None,
    limit: int,
) -> tuple[list[CalendarEvent], str | None]:
    q = select(CalendarEvent).where(CalendarEvent.user_id == user_id, CalendarEvent.deleted == False)  # noqa: E712
    if updated_from:
        q = q.where(CalendarEvent.updated_at >= updated_from)
    if start_from:
        q = q.where(CalendarEvent.start_at >= start_from)
    if start_to:
        q = q.where(CalendarEvent.start_at <= start_to)

    if cursor:
        try:
            ts_str, id_str = cursor.split("|")
            ts = datetime.fromisoformat(ts_str)
            cid = uuid.UUID(id_str)
            q = q.where((CalendarEvent.updated_at, CalendarEvent.id) < (ts, cid))
        except Exception:
            pass

    q = q.order_by(CalendarEvent.updated_at.desc(), CalendarEvent.id.desc()).limit(max(1, min(limit, 100)) + 1)
    res = await db.execute(q)
    rows = res.scalars().all()

    next_cursor = None
    if len(rows) > limit:
        last = rows[limit - 1]
        next_cursor = f"{last.updated_at.isoformat()}|{last.id}"
        rows = rows[:limit]

    return rows, next_cursor


async def get_by_id(db: AsyncSession, *, user_id: uuid.UUID, event_id: uuid.UUID) -> CalendarEvent | None:
    res = await db.execute(
        select(CalendarEvent).where(CalendarEvent.id == event_id, CalendarEvent.user_id == user_id, CalendarEvent.deleted == False)  # noqa: E712
    )
    return res.scalar_one_or_none()


async def create(db: AsyncSession, event: CalendarEvent) -> CalendarEvent:
    db.add(event)
    await db.flush()
    return event


async def patch(db: AsyncSession, *, event_id: uuid.UUID, values: dict) -> None:
    await db.execute(update(CalendarEvent).where(CalendarEvent.id == event_id).values(**values))
