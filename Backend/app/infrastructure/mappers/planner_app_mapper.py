from __future__ import annotations
import uuid
from datetime import datetime
from typing import Protocol

from app.application.models.planner import (
    PlannerPlan, PlannerSlot, PlannerConflict, 
    PlannerTask, PlannerCalendarEvent, PlannerPreferences,
    WorkScheduleEntry, PlannerBreak
)
from app.infrastructure.mappers.planner_mapper import (
    domain_slot_to_dto, domain_conflict_to_dto,
    dto_slot_to_domain, dto_conflict_to_domain
)


class PlannerMapperProtocol(Protocol):
    """Протокол маппера между слоями"""
    
    def to_domain(self, data: dict) -> PlannerPlan:
        ...
    
    def from_domain(self, plan: PlannerPlan) -> dict:
        ...


class PlannerAppMapper:
    """Маппер для приложения"""
    
    def to_domain(self, data: dict) -> PlannerPlan:
        """Из данных БД/сервиса в доменную модель"""
        slots = [
            PlannerSlot(
                slot_id=slot["slot_id"] if isinstance(slot["slot_id"], uuid.UUID) else uuid.UUID(slot["slot_id"]),
                task_id=uuid.UUID(slot["task_id"]) if slot.get("task_id") else None,
                title=slot["title"],
                description=slot.get("description"),
                start_at=slot["start_at"] if isinstance(slot["start_at"], datetime) else datetime.fromisoformat(slot["start_at"]),
                end_at=slot["end_at"] if isinstance(slot["end_at"], datetime) else datetime.fromisoformat(slot["end_at"])
            )
            for slot in data.get("slots", [])
        ]
        
        conflicts = [
            PlannerConflict(
                slot_id=uuid.UUID(conflict["slot_id"]) if conflict.get("slot_id") else None,
                reason=conflict["reason"],
                severity=conflict.get("severity", "warning"),
                details=conflict.get("details"),
                related_task_id=uuid.UUID(conflict["related_task_id"]) if conflict.get("related_task_id") else None
            )
            for conflict in data.get("conflicts", [])
        ]
        
        return PlannerPlan(
            plan_request_id=data["plan_request_id"] if isinstance(data["plan_request_id"], uuid.UUID) 
                       else uuid.UUID(data["plan_request_id"]),
            status=data["status"],
            version=data.get("version", 1),
            source=data.get("source", "ai"),
            slots=slots,
            conflicts=conflicts
        )
    
    def from_domain(self, plan: PlannerPlan) -> dict:
        """Из доменной модели в данные для БД/сервиса"""
        return {
            "plan_request_id": str(plan.plan_request_id),
            "status": plan.status,
            "version": plan.version,
            "source": plan.source,
            "slots": [
                {
                    "slot_id": str(slot.slot_id),
                    "task_id": str(slot.task_id) if slot.task_id else None,
                    "title": slot.title,
                    "description": slot.description,
                    "start_at": slot.start_at.isoformat(),
                    "end_at": slot.end_at.isoformat()
                }
                for slot in plan.slots
            ],
            "conflicts": [
                {
                    "slot_id": str(conflict.slot_id) if conflict.slot_id else None,
                    "reason": conflict.reason,
                    "severity": conflict.severity,
                    "details": conflict.details,
                    "related_task_id": str(conflict.related_task_id) if conflict.related_task_id else None
                }
                for conflict in plan.conflicts
            ]
        }