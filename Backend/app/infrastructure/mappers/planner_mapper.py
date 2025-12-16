from __future__ import annotations

from app.domain.value_objects.planner import PlannerConflict as DomainPlannerConflict
from app.domain.value_objects.planner import PlannerSlot as DomainPlannerSlot
from app.schemas.planner import PlannerConflict, PlannerSlot


def domain_slot_to_dto(slot: DomainPlannerSlot) -> PlannerSlot:
    return PlannerSlot(
        slot_id=slot.slot_id,
        task_id=slot.task_id,
        title=slot.title,
        description=slot.description,
        start_at=slot.start_at,
        end_at=slot.end_at,
    )


def dto_slot_to_domain(dto: PlannerSlot) -> DomainPlannerSlot:
    return DomainPlannerSlot(
        slot_id=dto.slot_id,
        task_id=dto.task_id,
        title=dto.title,
        description=dto.description,
        start_at=dto.start_at,
        end_at=dto.end_at,
    )


def domain_conflict_to_dto(conflict: DomainPlannerConflict) -> PlannerConflict:
    return PlannerConflict(
        slot_id=conflict.slot_id,
        reason=conflict.reason,
        severity=conflict.severity,
        details=conflict.details,
        related_task_id=conflict.related_task_id,
    )


def dto_conflict_to_domain(dto: PlannerConflict) -> DomainPlannerConflict:
    return DomainPlannerConflict(
        slot_id=dto.slot_id,
        reason=dto.reason,
        severity=dto.severity,
        details=dto.details,
        related_task_id=dto.related_task_id,
    )
