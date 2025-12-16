from __future__ import annotations

from collections import defaultdict
from typing import Any, Awaitable, Callable, DefaultDict, Iterable

from backend.domain.interfaces.message_bus import MessageBus

Handler = Callable[[Any], Awaitable[None]]


class InMemoryEventPublisher(MessageBus):
    """Simple async pub/sub implementation to decouple domain events."""

    def __init__(self, handlers: Iterable[Handler] | None = None) -> None:
        self._handlers: DefaultDict[str, list[Handler]] = defaultdict(list)
        for handler in handlers or []:
            self.register("*", handler)

    def register(self, event_type: str, handler: Handler) -> None:
        self._handlers[event_type].append(handler)

    async def publish(self, message: Any) -> None:
        event_type = getattr(message, "__class__", type(message)).__name__
        for handler in self._handlers.get("*", []):
            await handler(message)
        for handler in self._handlers.get(event_type, []):
            await handler(message)
