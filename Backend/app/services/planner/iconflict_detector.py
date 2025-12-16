from __future__ import annotations

from typing import Protocol

from app.domain.value_objects.planner import PlannerConflict, PlannerPreferences, PlannerSlot


class IConflictDetector(Protocol):
    def detect_schedule_conflicts(
        self,
        *,
        slots: list[PlannerSlot],
        work_schedule: list[dict],
        calendar_events: list[dict],
    ) -> list[PlannerConflict]:
        ...

    def detect_resource_conflicts(
        self,
        *,
        slots: list[PlannerSlot],
        completed_task_ids: list[str],
        rescheduled_task_ids: list[str],
    ) -> list[PlannerConflict]:
        ...

    def detect_preference_conflicts(
        self,
        *,
        slots: list[PlannerSlot],
        preferences: PlannerPreferences | None,
    ) -> list[PlannerConflict]:
        ...
