from __future__ import annotations
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.application.models.planner import PlannerPlan
    from app.application.ports.ai_access import PlanRepository
    from app.infrastructure.mappers.planner_mapper import PlannerMapperProtocol


class GetPlanUseCase:
    """Use-case для получения плана"""
    
    def __init__(
        self,
        *,
        plan_repository: PlanRepository,
        mapper: PlannerMapperProtocol
    ) -> None:
        self.plan_repository = plan_repository
        self.mapper = mapper
    
    async def execute(
        self,
        *,
        plan_request_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> PlannerPlan | None:
        """Получить план по ID запроса"""
        plan_data = await self.plan_repository.get_by_request_id(
            plan_request_id=plan_request_id,
            user_id=user_id
        )
        
        if not plan_data:
            return None
        
        return self.mapper.to_domain(plan_data)