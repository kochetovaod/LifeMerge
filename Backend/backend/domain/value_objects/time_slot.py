from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class TimeSlot:
    """Represents a concrete time range."""

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if self.start >= self.end:
            raise ValueError("start must be earlier than end")

    @property
    def duration(self) -> timedelta:
        return self.end - self.start
