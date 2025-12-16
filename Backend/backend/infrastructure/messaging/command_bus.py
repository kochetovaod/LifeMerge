from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict


class InMemoryCommandBus:
    """Minimal in-memory command bus for application orchestration."""

    def __init__(self) -> None:
        self._handlers: Dict[str, Callable[[Any], Awaitable[Any]]] = {}

    def register(self, command_name: str, handler: Callable[[Any], Awaitable[Any]]) -> None:
        self._handlers[command_name] = handler

    async def dispatch(self, command_name: str, payload: Any) -> Any:
        if command_name not in self._handlers:
            raise KeyError(f"No handler registered for {command_name}")
        return await self._handlers[command_name](payload)
