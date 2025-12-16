from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.domain.repositories.planner_repository import PlannerRepository


def create_planner_repository(session: "AsyncSession") -> "PlannerRepository":
    """Фабрика для создания репозитория планов"""
    from app.infrastructure.repositories.planner_repository import SQLPlannerRepository
    return SQLPlannerRepository(session)