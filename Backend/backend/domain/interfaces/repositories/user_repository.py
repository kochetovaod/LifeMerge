from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Optional

from backend.domain.entities.user import User


class UserRepository(ABC):
    @abstractmethod
    async def get(self, user_id: uuid.UUID) -> Optional[User]:
        raise NotImplementedError

    @abstractmethod
    async def save(self, user: User) -> None:
        raise NotImplementedError
