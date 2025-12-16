from __future__ import annotations
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Protocol

from app.domain.models.planner import DomainPlannerPlan


class PlannerRepository(Protocol):
    """Порт репозитория для работы с планами"""
    
    @abstractmethod
    async def save(self, plan: DomainPlannerPlan) -> None:
        """Сохранить план"""
        ...
    
    @abstractmethod
    async def get_by_id(self, plan_id: uuid.UUID) -> Optional[DomainPlannerPlan]:
        """Получить план по ID"""
        ...
    
    @abstractmethod
    async def get_by_request_id(
        self,
        plan_request_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Optional[DomainPlannerPlan]:
        """Получить план по ID запроса и пользователю"""
        ...
    
    @abstractmethod
    async def get_by_user(
        self,
        user_id: uuid.UUID,
        *,
        status: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> list[DomainPlannerPlan]:
        """Получить планы пользователя с фильтрами"""
        ...
    
    @abstractmethod
    async def update_status(
        self,
        plan_id: uuid.UUID,
        status: str
    ) -> None:
        """Обновить статус плана"""
        ...
    
    @abstractmethod
    async def increment_version(
        self,
        plan_id: uuid.UUID
    ) -> None:
        """Увеличить версию плана"""
        ...
    
    @abstractmethod
    async def soft_delete(
        self,
        plan_id: uuid.UUID
    ) -> None:
        """Мягкое удаление плана"""
        ...
    
    @abstractmethod
    async def exists_by_request_id(
        self,
        plan_request_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> bool:
        """Проверить существование плана по ID запроса"""
        ...