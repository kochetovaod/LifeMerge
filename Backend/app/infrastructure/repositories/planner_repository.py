from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import and_, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models.planner import DomainPlannerPlan
from app.domain.repositories.planner_repository import PlannerRepository
from app.infrastructure.mappers.planner_domain_mapper import PlannerDomainMapper
from app.infrastructure.models.planner_models import SQLPlannerPlan


class SQLPlannerRepository(PlannerRepository):
    """SQLAlchemy реализация репозитория планов"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.mapper = PlannerDomainMapper()
    
    async def save(self, plan: DomainPlannerPlan) -> None:
        """Сохранить или обновить план"""
        
        # Проверяем существование плана
        existing = await self._get_sql_plan_by_id(plan.plan_id)
        
        if existing:
            # Обновляем существующий план
            self.mapper.update_sql_from_domain(existing, plan)
            self.session.add(existing)
        else:
            # Создаем новый план
            sql_plan = self.mapper.from_domain(plan)
            self.session.add(sql_plan)
        
        await self.session.flush()
    
    async def get_by_id(self, plan_id: uuid.UUID) -> Optional[DomainPlannerPlan]:
        """Получить план по ID"""
        sql_plan = await self._get_sql_plan_by_id(plan_id)
        if not sql_plan:
            return None
        return self.mapper.to_domain(sql_plan)
    
    async def get_by_request_id(
        self,
        plan_request_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Optional[DomainPlannerPlan]:
        """Получить план по ID запроса и пользователю"""
        sql_plan = await self._get_sql_plan_by_request_id(plan_request_id, user_id)
        if not sql_plan:
            return None
        return self.mapper.to_domain(sql_plan)
    
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
        
        query = select(SQLPlannerPlan).where(
            SQLPlannerPlan.user_id == user_id,
            SQLPlannerPlan.deleted == False
        )
        
        # Применяем фильтры
        if status:
            query = query.where(SQLPlannerPlan.status == status)
        if from_date:
            query = query.where(SQLPlannerPlan.created_at >= from_date)
        if to_date:
            query = query.where(SQLPlannerPlan.created_at <= to_date)
        
        # Сортируем и ограничиваем
        query = query.order_by(SQLPlannerPlan.created_at.desc())
        query = query.offset(offset).limit(limit)
        
        # Загружаем связанные данные
        query = query.options(
            selectinload(SQLPlannerPlan.slots),
            selectinload(SQLPlannerPlan.conflicts)
        )
        
        result = await self.session.execute(query)
        sql_plans = result.scalars().all()
        
        return [self.mapper.to_domain(plan) for plan in sql_plans]
    
    async def update_status(
        self,
        plan_id: uuid.UUID,
        status: str
    ) -> None:
        """Обновить статус плана"""
        await self.session.execute(
            update(SQLPlannerPlan)
            .where(SQLPlannerPlan.id == plan_id)
            .values(
                status=status,
                updated_at=datetime.now(timezone.utc)
            )
        )
        await self.session.flush()
    
    async def increment_version(
        self,
        plan_id: uuid.UUID
    ) -> None:
        """Увеличить версию плана"""
        await self.session.execute(
            update(SQLPlannerPlan)
            .where(SQLPlannerPlan.id == plan_id)
            .values(
                version=SQLPlannerPlan.version + 1,
                updated_at=datetime.now(timezone.utc)
            )
        )
        await self.session.flush()
    
    async def soft_delete(
        self,
        plan_id: uuid.UUID
    ) -> None:
        """Мягкое удаление плана"""
        await self.session.execute(
            update(SQLPlannerPlan)
            .where(SQLPlannerPlan.id == plan_id)
            .values(
                deleted=True,
                updated_at=datetime.now(timezone.utc)
            )
        )
        await self.session.flush()
    
    async def exists_by_request_id(
        self,
        plan_request_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> bool:
        """Проверить существование плана по ID запроса"""
        query = select(SQLPlannerPlan.id).where(
            SQLPlannerPlan.plan_request_id == plan_request_id,
            SQLPlannerPlan.user_id == user_id,
            SQLPlannerPlan.deleted == False
        ).limit(1)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def _get_sql_plan_by_id(
        self,
        plan_id: uuid.UUID
    ) -> Optional[SQLPlannerPlan]:
        """Получить SQLAlchemy модель плана по ID"""
        query = select(SQLPlannerPlan).where(
            SQLPlannerPlan.id == plan_id,
            SQLPlannerPlan.deleted == False
        ).options(
            selectinload(SQLPlannerPlan.slots),
            selectinload(SQLPlannerPlan.conflicts)
        )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_sql_plan_by_request_id(
        self,
        plan_request_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Optional[SQLPlannerPlan]:
        """Получить SQLAlchemy модель плана по ID запроса"""
        query = select(SQLPlannerPlan).where(
            SQLPlannerPlan.plan_request_id == plan_request_id,
            SQLPlannerPlan.user_id == user_id,
            SQLPlannerPlan.deleted == False
        ).options(
            selectinload(SQLPlannerPlan.slots),
            selectinload(SQLPlannerPlan.conflicts)
        )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def delete_slots_by_plan_id(self, plan_id: uuid.UUID) -> None:
        """Удалить все слоты плана"""
        await self.session.execute(
            delete(SQLPlannerSlot)
            .where(SQLPlannerSlot.plan_id == plan_id)
        )
        await self.session.flush()
    
    async def delete_conflicts_by_plan_id(self, plan_id: uuid.UUID) -> None:
        """Удалить все конфликты плана"""
        await self.session.execute(
            delete(SQLPlannerConflict)
            .where(SQLPlannerConflict.plan_id == plan_id)
        )
        await self.session.flush()