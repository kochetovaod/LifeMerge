from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Optional

from backend.domain.entities.plan import Plan


class PlanRepository(ABC):
    @abstractmethod
    async def add(self, plan: Plan) -> Plan:
        raise NotImplementedError

    @abstractmethod
    async def get_latest_for_user(self, user_id: uuid.UUID) -> Optional[Plan]:
        raise NotImplementedError
