from __future__ import annotations
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.run_planner import RunPlannerUseCase
from app.application.use_cases.get_plan import GetPlanUseCase
from app.application.use_cases.apply_decision import ApplyDecisionUseCase
from app.application.adapters.plan_repository_adapter import ApplicationPlanRepositoryAdapter
from app.infrastructure.adapters.ai_access_adapter import (
    FastAPIAIAccessPolicy,
    SQLAlchemyIdempotencyChecker,
    StructuredLogEventPublisher
)
from app.infrastructure.repositories.planner_repository_factory import create_planner_repository
from app.infrastructure.mappers.planner_app_mapper import PlannerAppMapper
from app.services.planner_service_protocol import PlannerServiceProtocol
from app.db.session import get_db


# Адаптер для PlannerService
class PlannerServiceAdapter(PlannerServiceProtocol):
    """Адаптер для сервиса планировщика"""
    
    async def enqueue_planner_run(
        self,
        *,
        user_id,
        payload: dict
    ) -> dict:
        """Поставить задание планировщика в очередь"""
        from app.services.planner_service import enqueue_planner_run as original_enqueue
        from fastapi import Request
        
        # Создаем заглушку Request для совместимости
        class StubRequest:
            def __init__(self, request_id: str):
                self.state = type('obj', (object,), {'request_id': request_id})()
        
        stub_request = StubRequest(payload.get("request_id", ""))
        
        # Вызываем оригинальную функцию
        return await original_enqueue(
            request=stub_request,
            user_id=user_id,
            payload=payload
        )
    
    async def apply_plan_decision(
        self,
        *,
        plan_request_id,
        user_id,
        decision,
        accepted_slots,
        edits
    ) -> dict:
        """Применить решение по плану"""
        from app.services.planner_service import apply_plan_decision as original_apply
        from sqlalchemy.ext.asyncio import AsyncSession
        
        # Создаем заглушку сессии
        class StubSession:
            async def commit(self):
                pass
            
            async def rollback(self):
                pass
        
        stub_db = StubSession()
        
        # Вызываем оригинальную функцию
        return await original_apply(
            db=stub_db,
            plan_request_id=plan_request_id,
            user_id=user_id,
            decision=decision,
            accepted_slots=accepted_slots,
            edits=edits
        )
    
    def get_plan_by_request_id(
        self,
        *,
        plan_request_id,
        user_id
    ) -> dict | None:
        """Получить план по ID запроса"""
        from app.services.planner_service import get_plan_by_request_id as original_get
        return original_get(
            plan_request_id=plan_request_id,
            user_id=user_id
        )


def get_run_planner_use_case(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> RunPlannerUseCase:
    """Фабрика для RunPlannerUseCase"""
    
    # Создаем доменный репозиторий
    domain_repository = create_planner_repository(db)
    
    # Создаем адаптер для application слоя
    plan_repository = ApplicationPlanRepositoryAdapter(domain_repository)
    
    return RunPlannerUseCase(
        access_policy=FastAPIAIAccessPolicy(request),
        idempotency_checker=SQLAlchemyIdempotencyChecker(request, db),
        event_publisher=StructuredLogEventPublisher(),
        plan_repository=plan_repository,
        planner_service=PlannerServiceAdapter()
    )


def get_get_plan_use_case(
    db: AsyncSession = Depends(get_db)
) -> GetPlanUseCase:
    """Фабрика для GetPlanUseCase"""
    
    domain_repository = create_planner_repository(db)
    plan_repository = ApplicationPlanRepositoryAdapter(domain_repository)
    
    return GetPlanUseCase(
        plan_repository=plan_repository,
        mapper=PlannerAppMapper()
    )


def get_apply_decision_use_case(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> ApplyDecisionUseCase:
    """Фабрика для ApplyDecisionUseCase"""
    
    domain_repository = create_planner_repository(db)
    plan_repository = ApplicationPlanRepositoryAdapter(domain_repository)
    
    return ApplyDecisionUseCase(
        idempotency_checker=SQLAlchemyIdempotencyChecker(request, db),
        plan_repository=plan_repository,
        planner_service=PlannerServiceAdapter()
    )