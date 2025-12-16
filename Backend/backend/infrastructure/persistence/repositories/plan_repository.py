from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_plan import AiPlanRun
from backend.domain.entities.plan import Plan
from backend.domain.interfaces.repositories.plan_repository import PlanRepository
from backend.infrastructure.persistence import mappers


class SqlAlchemyPlanRepository(PlanRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, plan: Plan) -> Plan:
        model = mappers.plan_to_model(plan)
        self._session.add(model)
        await self._session.flush()
        return mappers.model_to_plan(model, tasks=plan.tasks)

    async def get_latest_for_user(self, user_id: uuid.UUID) -> Optional[Plan]:
        res = await self._session.execute(
            select(AiPlanRun).where(AiPlanRun.user_id == user_id).order_by(AiPlanRun.created_at.desc()).limit(1)
        )
        row = res.scalar_one_or_none()
        return mappers.model_to_plan(row) if row else None
