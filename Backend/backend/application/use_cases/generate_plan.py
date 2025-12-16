from __future__ import annotations

import uuid
from dataclasses import dataclass

from backend.domain.domain_events.plan_generated import PlanGenerated
from backend.domain.entities.plan import Plan
from backend.domain.interfaces.message_bus import MessageBus
from backend.domain.interfaces.repositories.plan_repository import PlanRepository
from backend.domain.interfaces.services.plan_generator import PlanGenerator


@dataclass
class GeneratePlanRequest:
    user_id: uuid.UUID
    version: int = 1


class GeneratePlan:
    def __init__(
        self,
        plan_repo: PlanRepository,
        plan_generator: PlanGenerator,
        message_bus: MessageBus,
    ) -> None:
        self._plan_repo = plan_repo
        self._plan_generator = plan_generator
        self._bus = message_bus

    async def execute(self, request: GeneratePlanRequest) -> Plan:
        plan = await self._plan_generator.generate(request.user_id)
        plan.version = request.version
        plan = await self._plan_repo.add(plan)
        await self._bus.publish(
            PlanGenerated(plan_id=plan.id, user_id=plan.user_id, version=plan.version)
        )
        return plan
