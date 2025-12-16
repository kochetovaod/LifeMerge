from __future__ import annotations
from typing import Protocol, Any
import uuid


class PlannerServiceProtocol(Protocol):
    """Протокол для сервиса планировщика (адаптер к существующему коду)"""
    
    async def enqueue_planner_run(
        self,
        *,
        user_id: uuid.UUID,
        payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Поставить задание планировщика в очередь"""
        ...
    
    async def apply_plan_decision(
        self,
        *,
        plan_request_id: uuid.UUID,
        user_id: uuid.UUID,
        decision: str,
        accepted_slots: set[uuid.UUID] | None,
        edits: list[dict]
    ) -> dict[str, Any]:
        """Применить решение по плану"""
        ...
    
    def get_plan_by_request_id(
        self,
        *,
        plan_request_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> dict[str, Any] | None:
        """Получить план по ID запроса"""
        ...