from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class DomainPlannerSlot:
    """Слот плана в доменной модели"""
    slot_id: uuid.UUID
    task_id: Optional[uuid.UUID]
    title: str
    description: Optional[str]
    start_at: datetime
    end_at: datetime
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    @property
    def duration_minutes(self) -> int:
        return int((self.end_at - self.start_at).total_seconds() // 60)


@dataclass
class DomainPlannerConflict:
    """Конфликт плана в доменной модели"""
    conflict_id: uuid.UUID
    slot_id: Optional[uuid.UUID]
    reason: str
    severity: str = "warning"
    details: Optional[str] = None
    related_task_id: Optional[uuid.UUID] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class DomainPlannerPlan:
    """План в доменной модели"""
    plan_id: uuid.UUID
    user_id: uuid.UUID
    plan_request_id: uuid.UUID
    status: str
    version: int = 1
    source: str = "ai"
    slots: list[DomainPlannerSlot] = field(default_factory=list)
    conflicts: list[DomainPlannerConflict] = field(default_factory=list)
    request_payload: dict[str, Any] = field(default_factory=dict)
    response_payload: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    deleted: bool = False
    
    def add_slot(self, slot: DomainPlannerSlot) -> None:
        """Добавить слот к плану"""
        self.slots.append(slot)
        self.updated_at = datetime.now()
    
    def add_conflict(self, conflict: DomainPlannerConflict) -> None:
        """Добавить конфликт к плану"""
        self.conflicts.append(conflict)
        self.updated_at = datetime.now()
    
    def update_status(self, status: str) -> None:
        """Обновить статус плана"""
        self.status = status
        self.updated_at = datetime.now()
    
    def increment_version(self) -> None:
        """Увеличить версию плана"""
        self.version += 1
        self.updated_at = datetime.now()