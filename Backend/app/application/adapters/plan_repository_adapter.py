from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Optional

from app.application.ports.ai_access import PlanRepository
from app.domain.repositories.planner_repository import PlannerRepository as DomainPlannerRepository
from app.infrastructure.mappers.planner_domain_mapper import PlannerDomainMapper


class ApplicationPlanRepositoryAdapter(PlanRepository):
    """Адаптер для PlanRepository порта application слоя"""
    
    def __init__(self, domain_repository: DomainPlannerRepository):
        self.domain_repository = domain_repository
        self.mapper = PlannerDomainMapper()
    
    async def get_by_request_id(
        self,
        *,
        plan_request_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> dict | None:
        """Получить план по ID запроса"""
        domain_plan = await self.domain_repository.get_by_request_id(
            plan_request_id=plan_request_id,
            user_id=user_id
        )
        
        if not domain_plan:
            return None
        
        # Преобразуем доменную модель в dict для application слоя
        return self._domain_to_dict(domain_plan)
    
    async def save_plan(
        self,
        *,
        plan_request_id: uuid.UUID,
        user_id: uuid.UUID,
        plan_data: dict
    ) -> None:
        """Сохранить план"""
        # Создаем доменную модель из данных
        domain_plan = self._dict_to_domain(plan_data, plan_request_id, user_id)
        await self.domain_repository.save(domain_plan)
    
    def _domain_to_dict(self, domain_plan) -> dict:
        """Преобразовать доменную модель в dict"""
        return {
            "plan_id": str(domain_plan.plan_id),
            "user_id": str(domain_plan.user_id),
            "plan_request_id": str(domain_plan.plan_request_id),
            "status": domain_plan.status,
            "version": domain_plan.version,
            "source": domain_plan.source,
            "slots": [
                {
                    "slot_id": str(slot.slot_id),
                    "task_id": str(slot.task_id) if slot.task_id else None,
                    "title": slot.title,
                    "description": slot.description,
                    "start_at": slot.start_at.isoformat(),
                    "end_at": slot.end_at.isoformat()
                }
                for slot in domain_plan.slots
            ],
            "conflicts": [
                {
                    "conflict_id": str(conflict.conflict_id),
                    "slot_id": str(conflict.slot_id) if conflict.slot_id else None,
                    "reason": conflict.reason,
                    "severity": conflict.severity,
                    "details": conflict.details,
                    "related_task_id": str(conflict.related_task_id) if conflict.related_task_id else None
                }
                for conflict in domain_plan.conflicts
            ],
            "request_payload": domain_plan.request_payload,
            "response_payload": domain_plan.response_payload,
            "created_at": domain_plan.created_at.isoformat(),
            "updated_at": domain_plan.updated_at.isoformat()
        }
    
    def _dict_to_domain(self, plan_data: dict, plan_request_id: uuid.UUID, user_id: uuid.UUID):
        """Преобразовать dict в доменную модель"""
        from app.domain.models.planner import (
            DomainPlannerPlan,
            DomainPlannerSlot,
            DomainPlannerConflict
        )
        from datetime import datetime, timezone
        
        # Создаем слоты
        slots = []
        for slot_data in plan_data.get("slots", []):
            slot = DomainPlannerSlot(
                slot_id=uuid.UUID(slot_data["slot_id"]),
                task_id=uuid.UUID(slot_data["task_id"]) if slot_data.get("task_id") else None,
                title=slot_data["title"],
                description=slot_data.get("description"),
                start_at=datetime.fromisoformat(slot_data["start_at"]),
                end_at=datetime.fromisoformat(slot_data["end_at"])
            )
            slots.append(slot)
        
        # Создаем конфликты
        conflicts = []
        for conflict_data in plan_data.get("conflicts", []):
            conflict = DomainPlannerConflict(
                conflict_id=uuid.UUID(conflict_data["conflict_id"]) if conflict_data.get("conflict_id") else uuid.uuid4(),
                slot_id=uuid.UUID(conflict_data["slot_id"]) if conflict_data.get("slot_id") else None,
                reason=conflict_data["reason"],
                severity=conflict_data.get("severity", "warning"),
                details=conflict_data.get("details"),
                related_task_id=uuid.UUID(conflict_data["related_task_id"]) if conflict_data.get("related_task_id") else None
            )
            conflicts.append(conflict)
        
        # Создаем план
        plan = DomainPlannerPlan(
            plan_id=uuid.UUID(plan_data.get("plan_id")) if plan_data.get("plan_id") else uuid.uuid4(),
            user_id=user_id,
            plan_request_id=plan_request_id,
            status=plan_data.get("status", "requested"),
            version=plan_data.get("version", 1),
            source=plan_data.get("source", "ai"),
            slots=slots,
            conflicts=conflicts,
            request_payload=plan_data.get("request_payload", {}),
            response_payload=plan_data.get("response_payload", {}),
            created_at=datetime.fromisoformat(plan_data["created_at"]) if plan_data.get("created_at") else datetime.now(timezone.utc),
            updated_at=datetime.fromisoformat(plan_data["updated_at"]) if plan_data.get("updated_at") else datetime.now(timezone.utc),
            deleted=plan_data.get("deleted", False)
        )
        
        return plan