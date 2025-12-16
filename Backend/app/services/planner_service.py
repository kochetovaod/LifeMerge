from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import log
from app.repositories import tasks_repo
from app.schemas.planner import PlannerSlotEdit
from app.services.events import publish_event
from app.services.planner.components import (
    AIOrchestrator,
    ConflictDetector,
    PlanHistoryManager,
    SlotGenerator,
    TimeSlotCalculator,
)
from app.services.planner.iaiorchestrator import IAIOrchestrator
from app.services.planner.iconflict_detector import IConflictDetector
from app.services.planner.iplan_history_manager import IPlanHistoryManager
from app.services.planner.islot_generator import ISlotGenerator
from app.services.planner.itimeslot_calculator import ITimeSlotCalculator
from app.services.tasks_service import create_task, update_task

_GENERATED_PLANS: dict[uuid.UUID, dict[str, Any]] = {}


class PlannerService:
    def __init__(
        self,
        *,
        slot_generator: ISlotGenerator,
        conflict_detector: IConflictDetector,
        plan_history_manager: IPlanHistoryManager,
        time_slot_calculator: ITimeSlotCalculator,
        ai_orchestrator: IAIOrchestrator,
        storage: dict[uuid.UUID, dict[str, Any]] | None = None,
    ) -> None:
        self.slot_generator = slot_generator
        self.conflict_detector = conflict_detector
        self.plan_history_manager = plan_history_manager
        self.time_slot_calculator = time_slot_calculator
        self.ai_orchestrator = ai_orchestrator
        self._generated_plans = storage if storage is not None else {}

    async def enqueue_planner_run(
        self,
        *,
        request: Request,
        user_id: uuid.UUID,
        payload: dict[str, Any],
        plan_request_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        plan_request_id = plan_request_id or uuid.uuid4()
        existing_plan = self._generated_plans.get(plan_request_id)

        publish_event(
            name="AI_Planner_Requested",
            request_id=request.state.request_id,
            user_id=str(user_id),
            payload={"plan_request_id": str(plan_request_id), **payload},
        )

        plan = await self.ai_orchestrator.request_ai_plan(
            request=request, plan_request_id=plan_request_id, payload=payload
        )
        slots = plan["slots"]
        conflicts = plan.get("conflicts", [])
        version: int = plan.get("version", 1)
        source = plan.get("source", "ai")
        new_plan = {
            "user_id": user_id,
            "status": plan["status"],
            "slots": slots,
            "conflicts": conflicts,
            "version": version,
            "created_at": existing_plan.get("created_at") if existing_plan else datetime.now(timezone.utc),
            "applied_slot_ids": payload.get("applied_slot_ids", []),
            "history": list(existing_plan.get("history", [])) if existing_plan else [],
            "source": source,
        }
        self.plan_history_manager.append_version(new_plan, status=plan["status"])
        self._generated_plans[plan_request_id] = new_plan

        log.info(
            "ai_planner_requested",
            request_id=request.state.request_id,
            user_id=str(user_id),
            plan_request_id=str(plan_request_id),
            subscription_status=payload.get("subscription_status"),
            version=version,
            conflicts=len(conflicts),
        )

        return {"plan_request_id": plan_request_id, "status": "ready", "source": source}

    def get_plan_by_request_id(self, *, plan_request_id: uuid.UUID, user_id: uuid.UUID) -> dict[str, Any] | None:
        plan = self._generated_plans.get(plan_request_id)
        if not plan or plan["user_id"] != user_id:
            return None
        return plan

    async def apply_plan_decision(
        self,
        db: AsyncSession,
        *,
        plan_request_id: uuid.UUID,
        user_id: uuid.UUID,
        decision: str,
        accepted_slots: set[uuid.UUID] | None,
        edits: list[PlannerSlotEdit] | None = None,
    ) -> dict[str, Any]:
        plan = self.get_plan_by_request_id(plan_request_id=plan_request_id, user_id=user_id)
        if not plan:
            raise ValueError("plan_not_found")

        if plan["status"] in {"accepted", "declined"}:
            return {
                "status": plan["status"],
                "created_task_ids": plan.get("created_task_ids", []),
                "updated_task_ids": plan.get("updated_task_ids", []),
                "version": plan.get("version", 1),
            }

        if decision == "decline":
            plan["status"] = "declined"
            plan["applied_slot_ids"] = []
            self.plan_history_manager.append_version(plan, status="declined")
            return {
                "status": plan["status"],
                "created_task_ids": [],
                "updated_task_ids": [],
                "version": plan.get("version", 1),
            }

        created: list[uuid.UUID] = []
        updated: list[uuid.UUID] = []
        slots = plan["slots"]
        if edits:
            slots = self.slot_generator.validate_slots(slots, edits)
            plan["slots"] = slots

        to_accept = accepted_slots if accepted_slots else {slot.slot_id for slot in slots}

        for slot in slots:
            if slot.slot_id not in to_accept:
                continue

            duration_minutes = self.time_slot_calculator.calculate_duration(slot.start_at, slot.end_at)
            if slot.task_id:
                task = await tasks_repo.get_by_id(db, task_id=slot.task_id, user_id=user_id)
                if not task:
                    continue
                patch = {
                    "title": slot.title,
                    "description": slot.description,
                    "due_at": slot.start_at,
                    "estimated_minutes": duration_minutes,
                    "status": "todo",
                }
                updated_task = await update_task(db, task, patch, expected_updated_at=None)
                updated.append(updated_task.id)
            else:
                task_data = {
                    "title": slot.title,
                    "description": slot.description,
                    "due_at": slot.start_at,
                    "estimated_minutes": duration_minutes,
                }
                new_task = await create_task(db, user_id, task_data)
                created.append(new_task.id)

        accepted_all = len(to_accept) == len(slots)
        plan["status"] = "accepted" if accepted_all else "partially_accepted"
        plan["created_task_ids"] = created
        plan["updated_task_ids"] = updated
        plan["applied_slot_ids"] = list(to_accept)
        self.plan_history_manager.append_version(
            plan, status=plan["status"], created_task_ids=created, updated_task_ids=updated
        )

        return {
            "status": plan["status"],
            "created_task_ids": created,
            "updated_task_ids": updated,
            "version": plan.get("version", 1),
        }


_time_slot_calculator = TimeSlotCalculator()
_conflict_detector = ConflictDetector()
_slot_generator = SlotGenerator(_time_slot_calculator, _conflict_detector)
_plan_history_manager = PlanHistoryManager()
_ai_orchestrator = AIOrchestrator(_slot_generator)

planner_service = PlannerService(
    slot_generator=_slot_generator,
    conflict_detector=_conflict_detector,
    plan_history_manager=_plan_history_manager,
    time_slot_calculator=_time_slot_calculator,
    ai_orchestrator=_ai_orchestrator,
    storage=_GENERATED_PLANS,
)


async def enqueue_planner_run(
    *, request: Request, user_id: uuid.UUID, payload: dict[str, Any], plan_request_id: uuid.UUID | None = None
) -> dict[str, Any]:
    return await planner_service.enqueue_planner_run(
        request=request, user_id=user_id, payload=payload, plan_request_id=plan_request_id
    )


def get_plan_by_request_id(*, plan_request_id: uuid.UUID, user_id: uuid.UUID) -> dict[str, Any] | None:
    return planner_service.get_plan_by_request_id(plan_request_id=plan_request_id, user_id=user_id)


async def apply_plan_decision(
    db: AsyncSession,
    *,
    plan_request_id: uuid.UUID,
    user_id: uuid.UUID,
    decision: str,
    accepted_slots: set[uuid.UUID] | None,
    edits: list[PlannerSlotEdit] | None = None,
) -> dict[str, Any]:
    return await planner_service.apply_plan_decision(
        db,
        plan_request_id=plan_request_id,
        user_id=user_id,
        decision=decision,
        accepted_slots=accepted_slots,
        edits=edits,
    )
