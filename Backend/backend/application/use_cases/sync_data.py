from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Protocol

from backend.domain.interfaces.message_bus import MessageBus


class SyncService(Protocol):
    async def sync(self, user_id: uuid.UUID) -> None:  # pragma: no cover - protocol
        ...


@dataclass
class SyncDataRequest:
    user_id: uuid.UUID


class SyncData:
    def __init__(self, sync_service: SyncService, message_bus: MessageBus) -> None:
        self._sync_service = sync_service
        self._bus = message_bus

    async def execute(self, request: SyncDataRequest) -> None:
        await self._sync_service.sync(request.user_id)
        # We intentionally avoid creating a specific event yet to keep the event
        # catalog lean while the rest of the domain is extracted.
        await self._bus.publish({"type": "sync_completed", "user_id": str(request.user_id)})
