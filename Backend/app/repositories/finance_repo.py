from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import Budget, FinanceAccount, FinanceTransaction


async def list_accounts(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    updated_from: datetime | None,
    cursor: str | None,
    limit: int,
) -> tuple[list[FinanceAccount], str | None]:
    q = select(FinanceAccount).where(FinanceAccount.user_id == user_id, FinanceAccount.deleted == False)  # noqa: E712
    if updated_from:
        q = q.where(FinanceAccount.updated_at >= updated_from)

    if cursor:
        try:
            ts_str, id_str = cursor.split("|")
            ts = datetime.fromisoformat(ts_str)
            cid = uuid.UUID(id_str)
            q = q.where((FinanceAccount.updated_at, FinanceAccount.id) < (ts, cid))
        except Exception:
            pass

    q = q.order_by(FinanceAccount.updated_at.desc(), FinanceAccount.id.desc()).limit(max(1, min(limit, 100)) + 1)
    res = await db.execute(q)
    rows = res.scalars().all()

    next_cursor = None
    if len(rows) > limit:
        last = rows[limit - 1]
        next_cursor = f"{last.updated_at.isoformat()}|{last.id}"
        rows = rows[:limit]

    return rows, next_cursor


async def list_transactions(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    account_id: uuid.UUID | None,
    updated_from: datetime | None,
    cursor: str | None,
    limit: int,
) -> tuple[list[FinanceTransaction], str | None]:
    q = select(FinanceTransaction).where(FinanceTransaction.user_id == user_id, FinanceTransaction.deleted == False)  # noqa: E712
    if account_id:
        q = q.where(FinanceTransaction.account_id == account_id)
    if updated_from:
        q = q.where(FinanceTransaction.updated_at >= updated_from)

    if cursor:
        try:
            ts_str, id_str = cursor.split("|")
            ts = datetime.fromisoformat(ts_str)
            cid = uuid.UUID(id_str)
            q = q.where((FinanceTransaction.updated_at, FinanceTransaction.id) < (ts, cid))
        except Exception:
            pass

    q = q.order_by(FinanceTransaction.updated_at.desc(), FinanceTransaction.id.desc()).limit(max(1, min(limit, 100)) + 1)
    res = await db.execute(q)
    rows = res.scalars().all()

    next_cursor = None
    if len(rows) > limit:
        last = rows[limit - 1]
        next_cursor = f"{last.updated_at.isoformat()}|{last.id}"
        rows = rows[:limit]

    return rows, next_cursor


async def patch_account(db: AsyncSession, *, account_id: uuid.UUID, values: dict) -> None:
    await db.execute(update(FinanceAccount).where(FinanceAccount.id == account_id).values(**values))


async def patch_transaction(db: AsyncSession, *, tx_id: uuid.UUID, values: dict) -> None:
    await db.execute(update(FinanceTransaction).where(FinanceTransaction.id == tx_id).values(**values))


async def patch_budget(db: AsyncSession, *, budget_id: uuid.UUID, values: dict) -> None:
    await db.execute(update(Budget).where(Budget.id == budget_id).values(**values))
