from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Iterable, Optional

from backend.domain.entities.goal import Goal


class GoalRepository(ABC):
    @abstractmethod
    async def add(self, goal: Goal) -> Goal:
        raise NotImplementedError

    @abstractmethod
    async def get(self, goal_id: uuid.UUID, *, user_id: uuid.UUID) -> Optional[Goal]:
        raise NotImplementedError

    @abstractmethod
    async def list_for_user(self, user_id: uuid.UUID) -> Iterable[Goal]:
        raise NotImplementedError
