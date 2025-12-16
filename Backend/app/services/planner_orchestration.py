from __future__ import annotations

import uuid
from dataclasses import dataclass

from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.ai_access import ensure_ai_access
from app.api.idempotency import enforce_idempotency
from app.core.logging import log
from app.core.response import err
from app.infrastructure.mappers.planner_mapper import domain_conflict_to_dto, domain_slot_to_dto
from app.schemas.planner import (
    PlannerDecisionIn,
    PlannerReplanIn,
    PlannerRunIn,
)
from app.services.events import publish_event
from app.services.planner_service import apply_plan_decision, enqueue_planner_run, get_plan_by_request_id


@dataclass
class AccessResult:
    allowed: bool
    upgrade_payload: dict | None = None


class PlannerEventPublisher:
    def publish_upgrade_offered(
        self,
        request_id: uuid.UUID,
        user_id: uuid.UUID,
        subscription_status: str,
        request_body_id: uuid.UUID,
    ) -> None:
        publish_event(
            name="AI_Planner_Upgrade_Offered",
            request_id=request_id,
            user_id=str(user_id),
            payload={"subscription_status": subscription_status, "request_id": request_body_id},
        )

    def publish_trial_used(self, request_id: uuid.UUID, user_id: uuid.UUID, request_body_id: uuid.UUID) -> None:
        publish_event(
            name="AI_Planner_Trial_Used",
            request_id=request_id,
            user_id=str(user_id),
            payload={"request_id": request_body_id},
        )


class PlannerAccessService:
    def __init__(self, event_publisher: PlannerEventPublisher) -> None:
        self.event_publisher = event_publisher

    def ensure_access(
        self,
        request: Request,
        subscription_status: str,
        current_user,
        request_body_id: uuid.UUID,
    ) -> AccessResult:
        try:
            ensure_ai_access(request, subscription_status=subscription_status)
        except HTTPException as exc:
            if exc.status_code == 403:
                trial_offer = None
                detail = exc.detail or {}
                if isinstance(detail, dict):
                    error = detail.get("error") or {}
                    details = error.get("details") or {}
                    trial_offer = details.get("trial_offer") or "Start a trial to enable the AI planner."
                self.event_publisher.publish_upgrade_offered(
                    request_id=request.state.request_id,
                    user_id=current_user.id,
                    subscription_status=subscription_status,
                    request_body_id=request_body_id,
                )
                payload = {
                    "plan_request_id": None,
                    "status": "upgrade_required",
                    "request_id": request.state.request_id,
                    "message": "AI planner is only available on Trial or Pro.",
                    "trial_offer": trial_offer,
                }
                return AccessResult(allowed=False, upgrade_payload=payload)
            raise
        return AccessResult(True)


class PlannerPayloadValidator:
    def build_run_payload(self, body: PlannerRunIn) -> dict:
        return {
            "week_start": body.week_start.isoformat() if body.week_start else None,
            "work_schedule": [entry.model_dump(mode="json") for entry in body.work_schedule],
            "subscription_status": body.subscription_status,
            "tasks": [task.model_dump(mode="json") for task in body.tasks],
            "calendar_events": [event.model_dump(mode="json") for event in body.calendar_events],
            "preferences": body.preferences.model_dump(mode="json") if body.preferences else None,
            "previous_plan_version": body.previous_plan_version or 0,
            "completed_task_ids": [str(item) for item in body.completed_task_ids],
            "rescheduled_task_ids": [str(item) for item in body.rescheduled_task_ids],
            "applied_slot_ids": [str(item) for item in body.applied_slot_ids],
        }

    def build_replan_payload(self, body: PlannerReplanIn, plan: dict) -> dict:
        return {
            "week_start": body.week_start.isoformat() if body.week_start else None,
            "work_schedule": [entry.model_dump(mode="json") for entry in body.work_schedule],
            "subscription_status": body.subscription_status,
            "tasks": [task.model_dump(mode="json") for task in body.tasks],
            "calendar_events": [event.model_dump(mode="json") for event in body.calendar_events],
            "preferences": body.preferences.model_dump(mode="json") if body.preferences else None,
            "previous_plan_version": plan.get("version", 0),
            "completed_task_ids": [str(item) for item in body.completed_task_ids],
            "rescheduled_task_ids": [str(item) for item in body.rescheduled_task_ids],
            "applied_slot_ids": [str(item) for item in body.applied_slot_ids] or plan.get("applied_slot_ids", []),
        }

    def ensure_plan_exists(self, plan: dict | None, request: Request) -> dict:
        if not plan:
            raise HTTPException(status_code=404, detail=err(request, "not_found", "Plan not found"))
        return plan

    async def ensure_idempotent(
        self,
        request: Request,
        current_user,
        db: AsyncSession,
        request_id: uuid.UUID,
        idempotency_key: str | None,
    ) -> None:
        await enforce_idempotency(
            request,
            current_user,
            db,
            request_id=request_id,
            idempotency_key=idempotency_key,
        )


class PlannerOrchestrator:
    def __init__(
        self,
        access_service: PlannerAccessService,
        event_publisher: PlannerEventPublisher,
        payload_validator: PlannerPayloadValidator,
    ) -> None:
        self.access_service = access_service
        self.event_publisher = event_publisher
        self.payload_validator = payload_validator

    async def run_planner(
        self,
        request: Request,
        body: PlannerRunIn,
        current_user,
        db: AsyncSession,
        idempotency_key: str | None,
    ) -> dict:
        access_result = self.access_service.ensure_access(
            request,
            subscription_status=body.subscription_status,
            current_user=current_user,
            request_body_id=body.request_id,
        )
        if not access_result.allowed:
            log.info(
                "planner_run_denied_free_plan",
                request_id=request.state.request_id,
                user_id=str(current_user.id),
                subscription_status=body.subscription_status,
            )
            return access_result.upgrade_payload or {}
        if body.subscription_status.lower() == "trial":
            self.event_publisher.publish_trial_used(
                request_id=request.state.request_id,
                user_id=current_user.id,
                request_body_id=body.request_id,
            )
        await self.payload_validator.ensure_idempotent(
            request,
            current_user=current_user,
            db=db,
            request_id=body.request_id,
            idempotency_key=idempotency_key,
        )
        planner_payload = self.payload_validator.build_run_payload(body)
        result = await enqueue_planner_run(request=request, user_id=current_user.id, payload=planner_payload)
        log.info(
            "planner_run_requested",
            request_id=request.state.request_id,
            user_id=str(current_user.id),
            subscription_status=body.subscription_status,
            work_schedule_entries=len(body.work_schedule),
            tasks=len(body.tasks),
            calendar_events=len(body.calendar_events),
        )
        return result

    def get_plan(self, request: Request, plan_request_id: uuid.UUID, current_user) -> dict:
        plan = get_plan_by_request_id(plan_request_id=plan_request_id, user_id=current_user.id)
        validated_plan = self.payload_validator.ensure_plan_exists(plan, request)
        mapped_slots = [domain_slot_to_dto(slot) for slot in validated_plan.get("slots", [])]
        mapped_conflicts = [domain_conflict_to_dto(item) for item in validated_plan.get("conflicts", [])]
        payload = {
            "plan_request_id": plan_request_id,
            "status": validated_plan["status"],
            "slots": mapped_slots,
            "conflicts": mapped_conflicts,
            "version": validated_plan.get("version", 1),
            "request_id": request.state.request_id,
            "source": validated_plan.get("source", "ai"),
        }
        log.info(
            "planner_plan_retrieved",
            request_id=request.state.request_id,
            user_id=str(current_user.id),
            plan_request_id=str(plan_request_id),
            slots=len(validated_plan.get("slots", [])),
            conflicts=len(validated_plan.get("conflicts", [])),
            version=validated_plan.get("version", 1),
        )
        return payload

    async def replan(
        self,
        request: Request,
        plan_request_id: uuid.UUID,
        body: PlannerReplanIn,
        current_user,
        db: AsyncSession,
        idempotency_key: str | None,
    ) -> dict:
        access_result = self.access_service.ensure_access(
            request,
            subscription_status=body.subscription_status,
            current_user=current_user,
            request_body_id=body.request_id,
        )
        if not access_result.allowed:
            return access_result.upgrade_payload or {}

        existing_plan = get_plan_by_request_id(plan_request_id=plan_request_id, user_id=current_user.id)
        validated_plan = self.payload_validator.ensure_plan_exists(existing_plan, request)
        if body.subscription_status.lower() == "trial":
            self.event_publisher.publish_trial_used(
                request_id=request.state.request_id,
                user_id=current_user.id,
                request_body_id=body.request_id,
            )
        await self.payload_validator.ensure_idempotent(
            request,
            current_user=current_user,
            db=db,
            request_id=body.request_id,
            idempotency_key=idempotency_key,
        )

        planner_payload = self.payload_validator.build_replan_payload(body, validated_plan)
        await enqueue_planner_run(
            request=request, user_id=current_user.id, payload=planner_payload, plan_request_id=plan_request_id
        )
        refreshed_plan = get_plan_by_request_id(plan_request_id=plan_request_id, user_id=current_user.id)
        validated_refreshed_plan = self.payload_validator.ensure_plan_exists(refreshed_plan, request)
        mapped_slots = [domain_slot_to_dto(slot) for slot in validated_refreshed_plan.get("slots", [])]
        mapped_conflicts = [
            domain_conflict_to_dto(item) for item in validated_refreshed_plan.get("conflicts", [])
        ]
        payload = {
            "plan_request_id": plan_request_id,
            "status": validated_refreshed_plan["status"],
            "slots": mapped_slots,
            "conflicts": mapped_conflicts,
            "version": validated_refreshed_plan.get("version", 1),
            "request_id": request.state.request_id,
            "source": validated_refreshed_plan.get("source", "ai"),
        }
        log.info(
            "planner_plan_replanned",
            request_id=request.state.request_id,
            user_id=str(current_user.id),
            plan_request_id=str(plan_request_id),
            slots=len(validated_refreshed_plan.get("slots", [])),
            conflicts=len(validated_refreshed_plan.get("conflicts", [])),
            version=validated_refreshed_plan.get("version", 1),
        )
        return payload

    async def decide_plan(
        self,
        request: Request,
        plan_request_id: uuid.UUID,
        body: PlannerDecisionIn,
        current_user,
        db: AsyncSession,
        idempotency_key: str | None,
    ) -> dict:
        await self.payload_validator.ensure_idempotent(
            request,
            current_user=current_user,
            db=db,
            request_id=body.request_id,
            idempotency_key=idempotency_key,
        )

        try:
            accepted_slots = set(body.accepted_slot_ids) if body.accepted_slot_ids else None
            decision_result = await apply_plan_decision(
                db,
                plan_request_id=plan_request_id,
                user_id=current_user.id,
                decision=body.decision,
                accepted_slots=accepted_slots,
                edits=body.edits,
            )
        except ValueError:
            raise HTTPException(status_code=404, detail=err(request, "not_found", "Plan not found"))

        await db.commit()
        log.info(
            "planner_plan_decision",
            request_id=request.state.request_id,
            user_id=str(current_user.id),
            plan_request_id=str(plan_request_id),
            decision=body.decision,
            accepted_slots=len(body.accepted_slot_ids or []),
            version=decision_result.get("version", 1),
        )
        return {
            "plan_request_id": plan_request_id,
            "status": decision_result["status"],
            "created_task_ids": decision_result.get("created_task_ids", []),
            "updated_task_ids": decision_result.get("updated_task_ids", []),
            "request_id": body.request_id,
            "version": decision_result.get("version", 1),
        }
