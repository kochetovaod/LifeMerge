from __future__ import annotations

import uuid
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.goal import Goal as GoalModel
from backend.domain.entities.goal import Goal
from backend.domain.interfaces.repositories.goal_repository import GoalRepository
from backend.infrastructure.persistence import mappers


class SqlAlchemyGoalRepository(GoalRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, goal: Goal) -> Goal:
        model = mappers.goal_to_model(goal)
        self._session.add(model)
        await self._session.flush()
        return mappers.model_to_goal(model)

    async def get(self, goal_id: uuid.UUID, *, user_id: uuid.UUID) -> Goal | None:
        res = await self._session.execute(
            select(GoalModel).where(GoalModel.id == goal_id, GoalModel.user_id == user_id, GoalModel.deleted == False)  # noqa: E712
        )
        row = res.scalar_one_or_none()
        return mappers.model_to_goal(row) if row else None

    async def list_for_user(self, user_id: uuid.UUID) -> Iterable[Goal]:
        res = await self._session.execute(
            select(GoalModel).where(GoalModel.user_id == user_id, GoalModel.deleted == False).order_by(GoalModel.updated_at.desc())  # noqa: E712
        )
        return [mappers.model_to_goal(row) for row in res.scalars().all()]
