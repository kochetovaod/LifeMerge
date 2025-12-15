from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.finance import FinanceAccount
from app.models.goal import Goal
from app.models.task import Task
from app.models.user import User


async def ensure_within_limits(db: AsyncSession, user: User) -> None:
    if user.is_pro:
        return

    await _enforce_goal_limit(db, user_id=user.id)
    await _enforce_task_limit(db, user_id=user.id)
    await _enforce_account_limit(db, user_id=user.id)


def ai_access_allowed(user: User) -> bool:
    return user.is_pro or user.trial_ends_at is not None


def analytics_access_allowed(user: User) -> bool:
    return user.is_pro


async def _enforce_goal_limit(db: AsyncSession, *, user_id: uuid.UUID) -> None:
    res = await db.execute(select(func.count(Goal.id)).where(Goal.user_id == user_id, Goal.deleted.is_(False)))
    if res.scalar_one() >= settings.FREE_MAX_GOALS:
        raise PermissionError("goal_limit_reached")


async def _enforce_task_limit(db: AsyncSession, *, user_id: uuid.UUID) -> None:
    res = await db.execute(select(func.count(Task.id)).where(Task.user_id == user_id, Task.deleted.is_(False)))
    if res.scalar_one() >= settings.FREE_MAX_TASKS:
        raise PermissionError("task_limit_reached")


async def _enforce_account_limit(db: AsyncSession, *, user_id: uuid.UUID) -> None:
    res = await db.execute(
        select(func.count(FinanceAccount.id)).where(FinanceAccount.user_id == user_id, FinanceAccount.deleted.is_(False))
    )
    if res.scalar_one() >= settings.FREE_MAX_FINANCE_ACCOUNTS:
        raise PermissionError("finance_account_limit_reached")
