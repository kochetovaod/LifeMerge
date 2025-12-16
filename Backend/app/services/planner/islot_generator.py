from __future__ import annotations

from typing import Protocol, Tuple

from app.schemas.planner import PlannerConflict, PlannerPreferences, PlannerSlot, PlannerSlotEdit


class ISlotGenerator(Protocol):
    def generate_slots(
        self,
        *,
        week_start: str | None,
        tasks: list[dict] | None = None,
        work_schedule: list[dict] | None = None,
        preferences: PlannerPreferences | None = None,
        calendar_events: list[dict] | None = None,
        completed_task_ids: list[str] | None = None,
        rescheduled_task_ids: list[str] | None = None,
    ) -> Tuple[list[PlannerSlot], list[PlannerConflict]]:
        ...

    def validate_slots(self, slots: list[PlannerSlot], edits: list[PlannerSlotEdit] | None = None) -> list[PlannerSlot]:
        ...
