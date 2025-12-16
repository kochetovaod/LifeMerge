from __future__ import annotations
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.application.models.planner import PlannerRunCommand, PlannerRunResult
    from app.application.ports.ai_access import (
        AIPlannerAccessPolicy, 
        IdempotencyChecker, 
        EventPublisher,
        PlanRepository
    )
    from app.services.planner_service import PlannerServiceProtocol


class RunPlannerUseCase:
    """Use-case для запуска AI планировщика"""
    
    def __init__(
        self,
        *,
        access_policy: AIPlannerAccessPolicy,
        idempotency_checker: IdempotencyChecker,
        event_publisher: EventPublisher,
        plan_repository: PlanRepository,
        planner_service: PlannerServiceProtocol
    ) -> None:
        self.access_policy = access_policy
        self.idempotency_checker = idempotency_checker
        self.event_publisher = event_publisher
        self.plan_repository = plan_repository
        self.planner_service = planner_service
    
    async def execute(self, command: PlannerRunCommand) -> PlannerRunResult:
        """Выполнить команду запуска планировщика"""
        
        # 1. Проверка доступа
        allowed, upgrade_payload = await self.access_policy.ensure_access(
            subscription_status=command.subscription_status,
            user_id=command.user_id,
            request_id=command.request_id
        )
        
        if not allowed:
            # Доступ запрещен - возвращаем информацию для апгрейда
            self.event_publisher.publish_upgrade_offered(
                request_id=command.request_id,
                user_id=command.user_id,
                subscription_status=command.subscription_status,
                plan_request_id=uuid.uuid4()
            )
            return PlannerRunResult(
                plan_request_id=uuid.uuid4(),
                status="upgrade_required",
                message=upgrade_payload.get("message") if upgrade_payload else None,
                trial_offer=upgrade_payload.get("trial_offer") if upgrade_payload else None
            )
        
        # 2. Использование триала
        if command.subscription_status.lower() == "trial":
            self.event_publisher.publish_trial_used(
                request_id=command.request_id,
                user_id=command.user_id,
                plan_request_id=uuid.uuid4()
            )
        
        # 3. Проверка идемпотентности
        await self.idempotency_checker.ensure_idempotent(
            user_id=command.user_id,
            key=command.request_id,
            method="POST",
            path="/api/v1/planner/run"
        )
        
        # 4. Запуск планировщика через сервис
        plan_request_id = uuid.uuid4()
        result = await self.planner_service.enqueue_planner_run(
            user_id=command.user_id,
            payload=self._build_payload(command, plan_request_id)
        )
        
        # 5. Публикация события
        self.event_publisher.publish_plan_created(
            request_id=command.request_id,
            user_id=command.user_id,
            plan_request_id=plan_request_id,
            status="requested"
        )
        
        return PlannerRunResult(
            plan_request_id=plan_request_id,
            status=result["status"],
            source=result.get("source")
        )
    
    def _build_payload(self, command: PlannerRunCommand, plan_request_id: uuid.UUID) -> dict:
        """Строим payload для сервиса планировщика"""
        return {
            "plan_request_id": str(plan_request_id),
            "week_start": command.week_start.isoformat() if command.week_start else None,
            "work_schedule": [
                {
                    "day_of_week": entry.day_of_week,
                    "start_time": entry.start_time.isoformat(),
                    "end_time": entry.end_time.isoformat()
                }
                for entry in command.work_schedule
            ],
            "subscription_status": command.subscription_status,
            "tasks": [
                {
                    "task_id": str(task.task_id),
                    "title": task.title,
                    "duration_minutes": task.duration_minutes,
                    "due_at": task.due_at.isoformat() if task.due_at else None,
                    "priority": task.priority,
                    "status": task.status
                }
                for task in command.tasks
            ],
            "calendar_events": [
                {
                    "event_id": str(event.event_id),
                    "title": event.title,
                    "start_at": event.start_at.isoformat(),
                    "end_at": event.end_at.isoformat()
                }
                for event in command.calendar_events
            ],
            "preferences": self._serialize_preferences(command.preferences),
            "previous_plan_version": command.previous_plan_version or 0,
            "completed_task_ids": [str(item) for item in command.completed_task_ids],
            "rescheduled_task_ids": [str(item) for item in command.rescheduled_task_ids],
            "applied_slot_ids": [str(item) for item in command.applied_slot_ids]
        }
    
    def _serialize_preferences(self, preferences) -> dict | None:
        if not preferences:
            return None
        return {
            "latest_start_hour": preferences.latest_start_hour,
            "breaks": [
                {
                    "start_time": br.start_time.isoformat(),
                    "end_time": br.end_time.isoformat()
                }
                for br in preferences.breaks
            ],
            "no_plan_days": list(preferences.no_plan_days)
        }