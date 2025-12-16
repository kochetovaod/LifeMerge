from __future__ import annotations
import uuid
from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.ai_access import ensure_ai_access
from app.api.idempotency import enforce_idempotency
from app.services.events import publish_event
from app.application.ports.ai_access import (
    AIPlannerAccessPolicy,
    IdempotencyChecker,
    EventPublisher,
    PlanRepository
)


class FastAPIAIAccessPolicy(AIPlannerAccessPolicy):
    """Адаптер политики доступа через FastAPI"""
    
    def __init__(self, request: Request):
        self.request = request
    
    async def ensure_access(
        self,
        *,
        subscription_status: str,
        user_id: uuid.UUID,
        request_id: str
    ) -> tuple[bool, dict | None]:
        try:
            ensure_ai_access(self.request, subscription_status=subscription_status)
            return True, None
        except HTTPException as exc:
            if exc.status_code == 403:
                detail = exc.detail or {}
                if isinstance(detail, dict):
                    error = detail.get("error") or {}
                    details = error.get("details") or {}
                    upgrade_payload = {
                        "message": error.get("message") or "AI planner is only available on Trial or Pro.",
                        "trial_offer": details.get("trial_offer") or "Start a trial to enable the AI planner."
                    }
                    return False, upgrade_payload
                return False, {"message": str(exc.detail)}
            raise


class SQLAlchemyIdempotencyChecker(IdempotencyChecker):
    """Адаптер проверки идемпотентности через SQLAlchemy"""
    
    def __init__(self, request: Request, db: AsyncSession):
        self.request = request
        self.db = db
    
    async def ensure_idempotent(
        self,
        *,
        user_id: uuid.UUID,
        key: str,
        method: str,
        path: str
    ) -> None:
        from app.models.user import User
        from app.core.response import err
        
        # Создаем временный user объект для вызова enforce_idempotency
        # В реальном приложении нужно вынести логику из enforce_idempotency в отдельный сервис
        user_obj = User()
        user_obj.id = user_id
        
        # Вызываем существующую функцию
        await enforce_idempotency(
            self.request,
            user_obj,
            self.db,
            request_id=key,
            idempotency_key=None
        )


class StructuredLogEventPublisher(EventPublisher):
    """Адаптер публикации событий через структурированное логирование"""
    
    def publish_upgrade_offered(
        self,
        *,
        request_id: str,
        user_id: uuid.UUID,
        subscription_status: str,
        plan_request_id: uuid.UUID
    ) -> None:
        publish_event(
            name="AI_Planner_Upgrade_Offered",
            request_id=request_id,
            user_id=str(user_id),
            payload={
                "subscription_status": subscription_status,
                "plan_request_id": str(plan_request_id)
            }
        )
    
    def publish_trial_used(
        self,
        *,
        request_id: str,
        user_id: uuid.UUID,
        plan_request_id: uuid.UUID
    ) -> None:
        publish_event(
            name="AI_Planner_Trial_Used",
            request_id=request_id,
            user_id=str(user_id),
            payload={"plan_request_id": str(plan_request_id)}
        )
    
    def publish_plan_created(
        self,
        *,
        request_id: str,
        user_id: uuid.UUID,
        plan_request_id: uuid.UUID,
        status: str
    ) -> None:
        publish_event(
            name="AI_Planner_Created",
            request_id=request_id,
            user_id=str(user_id),
            payload={
                "plan_request_id": str(plan_request_id),
                "status": status
            }
        )