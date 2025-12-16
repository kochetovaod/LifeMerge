from __future__ import annotations

import uuid

from backend.domain.entities.plan import Plan
from backend.domain.entities.task import Task
from backend.domain.interfaces.services.plan_generator import PlanGenerator


class StubAIService(PlanGenerator):
    """Adapter placeholder that will call the real AI service later."""

    async def generate(self, user_id: uuid.UUID) -> Plan:
        # For now we just return an empty plan shell; orchestration happens at the
        # application service level and real AI integration will live here.
        return Plan.new(user_id=user_id, tasks=[Task.create(user_id=user_id, title="AI suggestion")])
