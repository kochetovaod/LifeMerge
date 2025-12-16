from __future__ import annotations

from datetime import datetime
from typing import Protocol

from app.domain.value_objects.planner import PlannerPreferences


class ITimeSlotCalculator(Protocol):
    def build_available_windows(
        self,
        *,
        start_date,
        work_schedule: list[dict],
        preferences: PlannerPreferences | None,
        calendar_events: list[dict],
    ) -> list[tuple[datetime, datetime]]:
        ...

    def calculate_duration(self, start_at: datetime, end_at: datetime) -> int:
        ...

    def normalize_timezone(self, value: datetime | None) -> datetime:
        ...
