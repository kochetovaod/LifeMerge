from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from backend.domain.entities.plan import Plan


class PlanGenerator(ABC):
    @abstractmethod
    async def generate(self, user_id: uuid.UUID) -> Plan:
        """Generate a plan for the given user using domain rules."""
        raise NotImplementedError
