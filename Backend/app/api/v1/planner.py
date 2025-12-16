from __future__ import annotations
import uuid
from datetime import time
from fastapi import APIRouter, Depends, Header, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.response import ok, err
from app.db.session import get_db
from app.schemas.planner import (
    PlannerDecisionIn,
    PlannerDecisionOut,
    PlannerPlanOut,
    PlannerReplanIn,
    PlannerRunIn,
    PlannerRunOut,
    PlannerSlot,
    PlannerConflict
)
from app.infrastructure.di_planner import (
    get_run_planner_use_case,
    get_get_plan_use_case,
    get_apply_decision_use_case
)

router = APIRouter(prefix="/planner")


@router.post("/run", response_model=PlannerRunOut)
async def run_ai_planner(
    request: Request,
    body: PlannerRunIn,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_idempotency_key: str | None = Header(default=None, alias="X-Idempotency-Key"),
):
    """Запуск AI планировщика через use-case"""
    from app.application.models.planner import (
        PlannerRunCommand, PlannerTask, PlannerCalendarEvent,
        WorkScheduleEntry, PlannerBreak, PlannerPreferences
    )
    
    try:
        # Преобразуем входной DTO в команду приложения
        work_schedule_entries = [
            WorkScheduleEntry(
                day_of_week=entry.day_of_week,
                start_time=entry.start_time,
                end_time=entry.end_time
            )
            for entry in body.work_schedule
        ]
        
        tasks = [
            PlannerTask(
                task_id=task.task_id,
                title=task.title,
                duration_minutes=task.duration_minutes,
                due_at=task.due_at,
                priority=task.priority,
                status=task.status
            )
            for task in body.tasks
        ]
        
        calendar_events = [
            PlannerCalendarEvent(
                event_id=event.event_id,
                title=event.title,
                start_at=event.start_at,
                end_at=event.end_at
            )
            for event in body.calendar_events
        ]
        
        preferences = None
        if body.preferences:
            breaks = [
                PlannerBreak(
                    start_time=br.start_time,
                    end_time=br.end_time
                )
                for br in body.preferences.breaks
            ]
            preferences = PlannerPreferences(
                latest_start_hour=body.preferences.latest_start_hour,
                breaks=breaks,
                no_plan_days=body.preferences.no_plan_days
            )
        
        command = PlannerRunCommand(
            request_id=body.request_id,
            user_id=current_user.id,
            week_start=body.week_start,
            work_schedule=work_schedule_entries,
            subscription_status=body.subscription_status,
            tasks=tasks,
            calendar_events=calendar_events,
            preferences=preferences,
            previous_plan_version=body.previous_plan_version,
            completed_task_ids=body.completed_task_ids,
            rescheduled_task_ids=body.rescheduled_task_ids,
            applied_slot_ids=body.applied_slot_ids
        )
        
        # Выполняем use-case
        use_case = get_run_planner_use_case(request, db)
        result = await use_case.execute(command)
        
        # Конвертируем результат в выходной DTO
        return ok(request, {
            "plan_request_id": result.plan_request_id,
            "status": result.status,
            "request_id": request.state.request_id,
            "message": result.message,
            "trial_offer": result.trial_offer,
            "source": result.source
        })
        
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=err(request, "validation_error", str(exc))
        )


@router.get("/{plan_request_id}", response_model=PlannerPlanOut)
async def get_ai_plan(
    request: Request,
    plan_request_id: uuid.UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получение плана через use-case"""
    
    try:
        # Выполняем use-case
        use_case = get_get_plan_use_case(db)
        plan = await use_case.execute(
            plan_request_id=plan_request_id,
            user_id=current_user.id
        )
        
        if not plan:
            raise HTTPException(
                status_code=404,
                detail=err(request, "not_found", "Plan not found")
            )
        
        # Конвертируем доменную модель в DTO
        slots = [
            PlannerSlot(
                slot_id=slot.slot_id,
                task_id=slot.task_id,
                title=slot.title,
                description=slot.description,
                start_at=slot.start_at,
                end_at=slot.end_at
            )
            for slot in plan.slots
        ]
        
        conflicts = [
            PlannerConflict(
                slot_id=conflict.slot_id,
                reason=conflict.reason,
                severity=conflict.severity,
                details=conflict.details,
                related_task_id=conflict.related_task_id
            )
            for conflict in plan.conflicts
        ]
        
        return ok(request, {
            "plan_request_id": plan.plan_request_id,
            "status": plan.status,
            "version": plan.version,
            "source": plan.source,
            "slots": slots,
            "conflicts": conflicts,
            "request_id": request.state.request_id
        })
        
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=err(request, "validation_error", str(exc))
        )


@router.post("/{plan_request_id}/replan", response_model=PlannerPlanOut)
async def replan_ai_plan(
    request: Request,
    plan_request_id: uuid.UUID,
    body: PlannerReplanIn,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_idempotency_key: str | None = Header(default=None, alias="X-Idempotency-Key"),
):
    """Replan через существующий orchestrator (временно)"""
    
    # Временная реализация - используем существующий код
    # TODO: Реализовать отдельный use-case для replan
    from app.services.planner_orchestration import (
        PlannerEventPublisher,
        PlannerAccessService,
        PlannerPayloadValidator,
        PlannerOrchestrator
    )
    
    event_publisher = PlannerEventPublisher()
    payload_validator = PlannerPayloadValidator()
    access_service = PlannerAccessService(event_publisher)
    orchestrator = PlannerOrchestrator(access_service, event_publisher, payload_validator)
    
    payload = await orchestrator.replan(
        request,
        plan_request_id=plan_request_id,
        body=body,
        current_user=current_user,
        db=db,
        idempotency_key=x_idempotency_key,
    )
    return ok(request, payload)


@router.post("/{plan_request_id}/decision", response_model=PlannerDecisionOut)
async def decide_ai_plan(
    request: Request,
    plan_request_id: uuid.UUID,
    body: PlannerDecisionIn,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_idempotency_key: str | None = Header(default=None, alias="X-Idempotency-Key"),
):
    """Принятие решения через use-case"""
    
    try:
        from app.application.models.planner import PlannerDecisionCommand
        
        # Преобразуем входной DTO в команду
        command = PlannerDecisionCommand(
            request_id=body.request_id,
            plan_request_id=plan_request_id,
            user_id=current_user.id,
            decision=body.decision,
            accepted_slot_ids=body.accepted_slot_ids,
            edits=body.edits
        )
        
        # Выполняем use-case
        use_case = get_apply_decision_use_case(request, db)
        result = await use_case.execute(command)
        
        # Конвертируем результат в DTO
        return ok(request, {
            "plan_request_id": result.plan_request_id,
            "status": result.status,
            "created_task_ids": result.created_task_ids,
            "updated_task_ids": result.updated_task_ids,
            "request_id": request.state.request_id,
            "version": result.version
        })
        
    except ValueError as exc:
        if "Plan not found" in str(exc):
            raise HTTPException(
                status_code=404,
                detail=err(request, "not_found", "Plan not found")
            )
        raise HTTPException(
            status_code=400,
            detail=err(request, "validation_error", str(exc))
        )