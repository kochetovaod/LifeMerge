from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class MessageBus(ABC):
    """Port for publishing domain events or commands."""

    @abstractmethod
    async def publish(self, message: Any) -> None:
        raise NotImplementedError
