from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Iterable

from app.core.config import settings
from app.core.logging import log
from app.schemas.planner import PlannerConflict, PlannerPreferences, PlannerSlot, PlannerTaskIn


@dataclass
class PlanningStrategyConfig:
    week_start: str | date | None
    tasks: list[dict[str, Any]] | None = None
    work_schedule: list[dict[str, Any]] | None = None
    preferences: PlannerPreferences | dict[str, Any] | None = None
    calendar_events: list[dict[str, Any]] | None = None
    completed_task_ids: list[str] | None = None
    rescheduled_task_ids: list[str] | None = None
    strategy_name: str | None = None
    strategy_options: dict[str, Any] | None = None

    start_date: date = field(init=False)
    normalized_preferences: PlannerPreferences | None = field(init=False)
    completed_ids: set[str] = field(init=False)
    rescheduled_ids: set[str] = field(init=False)

    def __post_init__(self) -> None:
        self.normalized_preferences = self._normalize_preferences(self.preferences)
        self.start_date = self._parse_start_date(self.week_start)
        self.completed_ids = set(self.completed_task_ids or [])
        self.rescheduled_ids = set(self.rescheduled_task_ids or [])

    @staticmethod
    def _normalize_preferences(
        preferences: PlannerPreferences | dict[str, Any] | None,
    ) -> PlannerPreferences | None:
        if preferences and isinstance(preferences, dict):
            try:
                return PlannerPreferences.model_validate(preferences)
            except Exception:  # noqa: BLE001
                return None
        return preferences

    @staticmethod
    def _parse_start_date(week_start: str | date | None) -> date:
        if isinstance(week_start, date):
            return week_start
        if isinstance(week_start, str):
            try:
                return date.fromisoformat(week_start)
            except ValueError:
                return datetime.now(timezone.utc).date()
        return datetime.now(timezone.utc).date()


class PlanningStrategy(ABC):
    @abstractmethod
    def generate_slots(
        self, config: PlanningStrategyConfig
    ) -> tuple[list[PlannerSlot], list[PlannerConflict]]:
        ...

    @abstractmethod
    def get_name(self) -> str:
        ...

    @abstractmethod
    def get_metadata(self) -> dict[str, Any]:
        ...


class _BasePlanningStrategy(PlanningStrategy):
    def __init__(self) -> None:
        self._metadata: dict[str, Any] = {}

    def _clean_datetime(self, value: datetime | None) -> datetime:
        if value is None:
            return datetime.now(timezone.utc)
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def _build_available_windows(
        self,
        *,
        start_date: date,
        work_schedule: list[dict[str, Any]],
        preferences: PlannerPreferences | None,
        calendar_events: list[dict[str, Any]],
    ) -> list[tuple[datetime, datetime]]:
        schedule = work_schedule or [
            {"day_of_week": day, "start_time": time(hour=9), "end_time": time(hour=17)}
            for day in range(0, 5)
        ]
        events = []
        for event in calendar_events:
            start = event.get("start_at")
            end = event.get("end_at")
            if isinstance(start, str):
                start = datetime.fromisoformat(start)
            if isinstance(end, str):
                end = datetime.fromisoformat(end)
            if start and end:
                events.append((self._clean_datetime(start), self._clean_datetime(end)))

        windows: list[tuple[datetime, datetime]] = []
        for day_offset in range(7):
            if preferences and day_offset in preferences.no_plan_days:
                continue
            day_schedule = [entry for entry in schedule if entry.get("day_of_week") == day_offset]
            for entry in day_schedule:
                start_time = entry.get("start_time")
                end_time = entry.get("end_time")
                if isinstance(start_time, str):
                    start_time = time.fromisoformat(start_time)
                if isinstance(end_time, str):
                    end_time = time.fromisoformat(end_time)
                if not start_time or not end_time:
                    continue
                start_dt = datetime.combine(start_date + timedelta(days=day_offset), start_time, tzinfo=timezone.utc)
                end_dt = datetime.combine(start_date + timedelta(days=day_offset), end_time, tzinfo=timezone.utc)
                windows.append((start_dt, end_dt))

        if preferences and preferences.breaks:
            processed: list[tuple[datetime, datetime]] = []
            for start_dt, end_dt in windows:
                adjusted = [(start_dt, end_dt)]
                for br in preferences.breaks:
                    break_start = datetime.combine(start_dt.date(), br.start_time, tzinfo=timezone.utc)
                    break_end = datetime.combine(start_dt.date(), br.end_time, tzinfo=timezone.utc)
                    adjusted = self._subtract_interval(adjusted, break_start, break_end)
                processed.extend(adjusted)
            windows = processed

        for event_start, event_end in events:
            windows = self._subtract_interval(windows, event_start, event_end)

        windows.sort(key=lambda pair: pair[0])
        return windows

    def _subtract_interval(
        self, windows: list[tuple[datetime, datetime]], block_start: datetime, block_end: datetime
    ) -> list[tuple[datetime, datetime]]:
        updated: list[tuple[datetime, datetime]] = []
        for start_dt, end_dt in windows:
            if block_end <= start_dt or end_dt <= block_start:
                updated.append((start_dt, end_dt))
                continue
            if start_dt < block_start:
                updated.append((start_dt, block_start))
            if block_end < end_dt:
                updated.append((block_end, end_dt))
        return updated

    def _detect_conflicts(
        self,
        *,
        slots: list[PlannerSlot],
        work_schedule: list[dict[str, Any]],
        preferences: PlannerPreferences | None,
        calendar_events: list[dict[str, Any]],
        completed_task_ids: list[str],
        rescheduled_task_ids: list[str],
    ) -> list[PlannerConflict]:
        conflicts: list[PlannerConflict] = []
        for slot in slots:
            weekday = slot.start_at.weekday()
            start_time = slot.start_at.time()
            end_time = slot.end_at.time()

            allowed = False
            for entry in work_schedule:
                if entry.get("day_of_week") != weekday:
                    continue
                start_window = time.fromisoformat(
                    entry.get("start_time") if isinstance(entry.get("start_time"), str) else entry.get("start_time").isoformat()
                )
                end_window = time.fromisoformat(
                    entry.get("end_time") if isinstance(entry.get("end_time"), str) else entry.get("end_time").isoformat()
                )
                if start_window.tzinfo:
                    start_window = start_window.replace(tzinfo=None)
                if end_window.tzinfo:
                    end_window = end_window.replace(tzinfo=None)
                if start_window <= start_time and end_time <= end_window:
                    allowed = True
                    break
            if work_schedule and not allowed:
                conflicts.append(
                    PlannerConflict(
                        slot_id=slot.slot_id,
                        reason="outside_work_schedule",
                        severity="warning",
                        details="Slot falls outside configured working hours.",
                    )
                )

            if preferences:
                if preferences.latest_start_hour is not None and slot.start_at.hour > preferences.latest_start_hour:
                    conflicts.append(
                        PlannerConflict(
                            slot_id=slot.slot_id,
                            reason="after_hours",
                            severity="warning",
                            details="Starts later than user preference allows.",
                        )
                    )

                if weekday in preferences.no_plan_days:
                    conflicts.append(
                        PlannerConflict(
                            slot_id=slot.slot_id,
                            reason="no_plan_day",
                            severity="info",
                            details="User requested no planning on this day.",
                        )
                    )

                for br in preferences.breaks:
                    start_break = br.start_time
                    end_break = br.end_time
                    if start_break <= start_time < end_break or start_break < end_time <= end_break:
                        conflicts.append(
                            PlannerConflict(
                                slot_id=slot.slot_id,
                                reason="break_time",
                                severity="warning",
                                details="Overlaps with a planned break.",
                            )
                        )

            for event in calendar_events:
                event_start = event.get("start_at")
                event_end = event.get("end_at")
                if isinstance(event_start, str):
                    event_start = datetime.fromisoformat(event_start)
                if isinstance(event_end, str):
                    event_end = datetime.fromisoformat(event_end)
                if event_start < slot.end_at and slot.start_at < event_end:
                    conflicts.append(
                        PlannerConflict(
                            slot_id=slot.slot_id,
                            reason="calendar_conflict",
                            severity="error",
                            details=f"Overlaps with calendar event {event.get('title')}",
                        )
                    )

            if slot.task_id and str(slot.task_id) in completed_task_ids:
                conflicts.append(
                    PlannerConflict(
                        slot_id=slot.slot_id,
                        reason="task_already_completed",
                        severity="info",
                        related_task_id=slot.task_id,
                        details="Task was marked as completed before planning.",
                    )
                )
            if slot.task_id and str(slot.task_id) in rescheduled_task_ids:
                conflicts.append(
                    PlannerConflict(
                        slot_id=slot.slot_id,
                        reason="task_rescheduled",
                        severity="warning",
                        related_task_id=slot.task_id,
                        details="Task has been rescheduled and may need re-planning.",
                    )
                )

        return conflicts

    def _parse_tasks(self, config: PlanningStrategyConfig) -> list[PlannerTaskIn]:
        parsed_tasks: list[PlannerTaskIn] = []
        for raw in config.tasks or []:
            try:
                parsed_tasks.append(PlannerTaskIn.model_validate(raw))
            except Exception:  # noqa: BLE001
                continue
        active_tasks = [task for task in parsed_tasks if str(task.task_id) not in config.completed_ids]

        if not active_tasks:
            filler_tasks = [
                PlannerTaskIn(
                    task_id=uuid.uuid4(),
                    title="Deep work",
                    duration_minutes=90,
                    status="todo",
                ),
                PlannerTaskIn(
                    task_id=uuid.uuid4(),
                    title="Focus session",
                    duration_minutes=60,
                    status="todo",
                ),
                PlannerTaskIn(
                    task_id=uuid.uuid4(),
                    title="Wrap-up",
                    duration_minutes=45,
                    status="todo",
                ),
            ]
            active_tasks = filler_tasks
        return active_tasks

    def _detect_all_conflicts(
        self,
        *,
        slots: list[PlannerSlot],
        config: PlanningStrategyConfig,
        scheduling_conflicts: Iterable[PlannerConflict] | None = None,
    ) -> list[PlannerConflict]:
        conflicts: list[PlannerConflict] = list(scheduling_conflicts or [])
        conflicts.extend(
            self._detect_conflicts(
                slots=slots,
                work_schedule=config.work_schedule or [],
                preferences=config.normalized_preferences,
                calendar_events=config.calendar_events or [],
                completed_task_ids=list(config.completed_ids),
                rescheduled_task_ids=list(config.rescheduled_ids),
            )
        )
        return conflicts

    def get_metadata(self) -> dict[str, Any]:
        return dict(self._metadata)


class SimpleGreedyStrategy(_BasePlanningStrategy):
    def get_name(self) -> str:
        return "simple_greedy"

    def generate_slots(
        self, config: PlanningStrategyConfig
    ) -> tuple[list[PlannerSlot], list[PlannerConflict]]:
        windows = self._build_available_windows(
            start_date=config.start_date,
            work_schedule=config.work_schedule or [],
            preferences=config.normalized_preferences,
            calendar_events=config.calendar_events or [],
        )
        tasks = self._parse_tasks(config)

        sorted_tasks = sorted(
            tasks,
            key=lambda t: (
                self._clean_datetime(t.due_at) if t.due_at else datetime.combine(config.start_date, time.max, tzinfo=timezone.utc),
                -(t.priority or 0),
            ),
        )
        slots: list[PlannerSlot] = []
        conflicts: list[PlannerConflict] = []
        available_windows = list(windows)

        for task in sorted_tasks:
            duration = timedelta(minutes=task.duration_minutes)
            deadline = self._clean_datetime(task.due_at) if task.due_at else datetime.combine(
                config.start_date + timedelta(days=7),
                time(hour=23, minute=59),
                tzinfo=timezone.utc,
            )

            placed = False
            for idx, (win_start, win_end) in enumerate(list(available_windows)):
                latest_end = min(win_end, deadline)
                if win_start >= latest_end:
                    continue
                slot_start = win_start
                slot_end = slot_start + duration
                if slot_end > latest_end:
                    continue

                slots.append(
                    PlannerSlot(
                        slot_id=uuid.uuid4(),
                        task_id=task.task_id,
                        title=task.title,
                        description=task.status or "Suggested by AI",
                        start_at=slot_start,
                        end_at=slot_end,
                    )
                )
                placed = True

                remaining = []
                if slot_end < win_end:
                    remaining.append((slot_end, win_end))
                available_windows.pop(idx)
                available_windows[idx:idx] = remaining
                break

            if not placed:
                conflicts.append(
                    PlannerConflict(
                        slot_id=None,
                        related_task_id=task.task_id,
                        reason="no_available_window",
                        severity="error",
                        details="No free slot before the task deadline.",
                    )
                )

        all_conflicts = self._detect_all_conflicts(
            slots=slots,
            config=config,
            scheduling_conflicts=conflicts,
        )
        self._metadata = {
            "strategy": self.get_name(),
            "scheduled_slots": len(slots),
            "conflicts": len(all_conflicts),
            "windows_considered": len(windows),
        }
        return slots, all_conflicts


class PriorityBasedStrategy(_BasePlanningStrategy):
    def get_name(self) -> str:
        return "priority_based"

    def generate_slots(
        self, config: PlanningStrategyConfig
    ) -> tuple[list[PlannerSlot], list[PlannerConflict]]:
        windows = self._build_available_windows(
            start_date=config.start_date,
            work_schedule=config.work_schedule or [],
            preferences=config.normalized_preferences,
            calendar_events=config.calendar_events or [],
        )
        tasks = self._parse_tasks(config)

        sorted_tasks = sorted(
            tasks,
            key=lambda t: (-(t.priority or 0), self._clean_datetime(t.due_at) if t.due_at else datetime.max.replace(tzinfo=timezone.utc)),
        )

        slots: list[PlannerSlot] = []
        conflicts: list[PlannerConflict] = []
        available_windows = list(windows)

        for task in sorted_tasks:
            duration = timedelta(minutes=task.duration_minutes)
            target_end = self._clean_datetime(task.due_at) if task.due_at else available_windows[-1][1] if available_windows else self._clean_datetime(None)
            placed = False

            for idx, (win_start, win_end) in enumerate(list(available_windows)):
                earliest_start = win_start
                latest_end = min(win_end, target_end)
                if latest_end - earliest_start < duration:
                    continue

                slot_end = min(latest_end, earliest_start + duration)
                slot_start = slot_end - duration
                if slot_start < win_start:
                    slot_start = win_start
                    slot_end = slot_start + duration

                slots.append(
                    PlannerSlot(
                        slot_id=uuid.uuid4(),
                        task_id=task.task_id,
                        title=task.title,
                        description=task.status or "Prioritized task",
                        start_at=slot_start,
                        end_at=slot_end,
                    )
                )
                placed = True

                remaining = []
                if slot_start > win_start:
                    remaining.append((win_start, slot_start))
                if slot_end < win_end:
                    remaining.append((slot_end, win_end))
                available_windows.pop(idx)
                available_windows[idx:idx] = remaining
                break

            if not placed:
                conflicts.append(
                    PlannerConflict(
                        slot_id=None,
                        related_task_id=task.task_id,
                        reason="priority_overflow",
                        severity="warning",
                        details="Task could not be placed within prioritized windows.",
                    )
                )

        all_conflicts = self._detect_all_conflicts(slots=slots, config=config, scheduling_conflicts=conflicts)
        self._metadata = {
            "strategy": self.get_name(),
            "scheduled_slots": len(slots),
            "conflicts": len(all_conflicts),
            "windows_considered": len(windows),
            "prioritized_tasks": len(sorted_tasks),
        }
        return slots, all_conflicts


class TimeBlockStrategy(_BasePlanningStrategy):
    def get_name(self) -> str:
        return "time_block"

    def generate_slots(
        self, config: PlanningStrategyConfig
    ) -> tuple[list[PlannerSlot], list[PlannerConflict]]:
        block_minutes = (config.strategy_options or {}).get("block_minutes") or 90
        windows = self._build_available_windows(
            start_date=config.start_date,
            work_schedule=config.work_schedule or [],
            preferences=config.normalized_preferences,
            calendar_events=config.calendar_events or [],
        )
        tasks = self._parse_tasks(config)
        tasks.sort(key=lambda t: (self._clean_datetime(t.due_at), -(t.priority or 0), -t.duration_minutes))

        slots: list[PlannerSlot] = []
        conflicts: list[PlannerConflict] = []
        block_delta = timedelta(minutes=block_minutes)

        for win_start, win_end in windows:
            current_start = win_start
            while current_start + timedelta(minutes=30) <= win_end and tasks:
                block_end = min(current_start + block_delta, win_end)
                task = tasks.pop(0)
                duration = timedelta(minutes=task.duration_minutes)
                if current_start + duration > block_end:
                    duration = block_end - current_start
                slots.append(
                    PlannerSlot(
                        slot_id=uuid.uuid4(),
                        task_id=task.task_id,
                        title=task.title,
                        description=task.status or "Time-blocked task",
                        start_at=current_start,
                        end_at=current_start + duration,
                    )
                )
                current_start = block_end

        for remaining in tasks:
            conflicts.append(
                PlannerConflict(
                    slot_id=None,
                    related_task_id=remaining.task_id,
                    reason="time_block_overflow",
                    severity="error",
                    details="Not enough time blocks to schedule task.",
                )
            )

        all_conflicts = self._detect_all_conflicts(slots=slots, config=config, scheduling_conflicts=conflicts)
        self._metadata = {
            "strategy": self.get_name(),
            "scheduled_slots": len(slots),
            "conflicts": len(all_conflicts),
            "block_minutes": block_minutes,
            "time_blocks_used": len(slots),
        }
        return slots, all_conflicts


class PlanningStrategyFactory:
    _registry: dict[str, type[PlanningStrategy]] = {}
    _runtime_override: str | None = None

    @classmethod
    def register_strategy(cls, strategy_cls: type[PlanningStrategy]) -> None:
        strategy_name = strategy_cls().get_name().lower()
        cls._registry[strategy_name] = strategy_cls

    @classmethod
    def set_runtime_override(cls, strategy_name: str | None) -> None:
        cls._runtime_override = strategy_name.lower() if strategy_name else None

    @classmethod
    def get_strategy(cls, config: PlanningStrategyConfig) -> PlanningStrategy:
        strategy_name = (
            cls._runtime_override
            or (config.strategy_name.lower() if config.strategy_name else None)
            or settings.PLANNER_DEFAULT_STRATEGY.lower()
        )
        strategy_cls = cls._registry.get(strategy_name) or cls._registry.get(settings.PLANNER_DEFAULT_STRATEGY.lower())
        if not strategy_cls:
            raise ValueError("No planning strategies registered")
        strategy_instance = strategy_cls()
        log.info(
            "planner_strategy_selected",
            strategy=strategy_instance.get_name(),
            override=bool(cls._runtime_override),
        )
        return strategy_instance

    @classmethod
    def available_strategies(cls) -> list[str]:
        return sorted(cls._registry.keys())


PlanningStrategyFactory.register_strategy(SimpleGreedyStrategy)
PlanningStrategyFactory.register_strategy(PriorityBasedStrategy)
PlanningStrategyFactory.register_strategy(TimeBlockStrategy)
