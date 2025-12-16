from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any

from app.domain.models.planner import (
    DomainPlannerPlan,
    DomainPlannerSlot,
    DomainPlannerConflict
)
from app.infrastructure.models.planner_models import (
    SQLPlannerPlan,
    SQLPlannerSlot,
    SQLPlannerConflict
)


class PlannerDomainMapper:
    """Маппер между доменными моделями и SQLAlchemy моделями"""
    
    @staticmethod
    def to_domain(sql_plan: SQLPlannerPlan) -> DomainPlannerPlan:
        """Преобразовать SQLAlchemy модель в доменную"""
        
        # Преобразуем слоты
        slots = [
            DomainPlannerSlot(
                slot_id=slot.slot_id,
                task_id=slot.task_id,
                title=slot.title,
                description=slot.description,
                start_at=slot.start_at,
                end_at=slot.end_at,
                created_at=slot.created_at,
                updated_at=slot.updated_at
            )
            for slot in sql_plan.slots
        ]
        
        # Преобразуем конфликты
        conflicts = [
            DomainPlannerConflict(
                conflict_id=conflict.conflict_id,
                slot_id=conflict.slot_id,
                reason=conflict.reason,
                severity=conflict.severity,
                details=conflict.details,
                related_task_id=conflict.related_task_id,
                created_at=conflict.created_at
            )
            for conflict in sql_plan.conflicts
        ]
        
        return DomainPlannerPlan(
            plan_id=sql_plan.id,
            user_id=sql_plan.user_id,
            plan_request_id=sql_plan.plan_request_id,
            status=sql_plan.status,
            version=sql_plan.version,
            source=sql_plan.source,
            slots=slots,
            conflicts=conflicts,
            request_payload=sql_plan.request_payload or {},
            response_payload=sql_plan.response_payload or {},
            created_at=sql_plan.created_at,
            updated_at=sql_plan.updated_at,
            deleted=sql_plan.deleted
        )
    
    @staticmethod
    def from_domain(domain_plan: DomainPlannerPlan) -> SQLPlannerPlan:
        """Преобразовать доменную модель в SQLAlchemy модель"""
        
        sql_plan = SQLPlannerPlan(
            id=domain_plan.plan_id,
            user_id=domain_plan.user_id,
            plan_request_id=domain_plan.plan_request_id,
            status=domain_plan.status,
            version=domain_plan.version,
            source=domain_plan.source,
            request_payload=domain_plan.request_payload,
            response_payload=domain_plan.response_payload,
            created_at=domain_plan.created_at or datetime.now(timezone.utc),
            updated_at=domain_plan.updated_at or datetime.now(timezone.utc),
            deleted=domain_plan.deleted
        )
        
        # Добавляем слоты
        for slot in domain_plan.slots:
            sql_slot = SQLPlannerSlot(
                slot_id=slot.slot_id,
                task_id=slot.task_id,
                title=slot.title,
                description=slot.description,
                start_at=slot.start_at,
                end_at=slot.end_at,
                created_at=slot.created_at or datetime.now(timezone.utc),
                updated_at=slot.updated_at or datetime.now(timezone.utc),
                plan=sql_plan
            )
            sql_plan.slots.append(sql_slot)
        
        # Добавляем конфликты
        for conflict in domain_plan.conflicts:
            sql_conflict = SQLPlannerConflict(
                conflict_id=conflict.conflict_id,
                slot_id=conflict.slot_id,
                reason=conflict.reason,
                severity=conflict.severity,
                details=conflict.details,
                related_task_id=conflict.related_task_id,
                created_at=conflict.created_at or datetime.now(timezone.utc),
                plan=sql_plan
            )
            sql_plan.conflicts.append(sql_conflict)
        
        return sql_plan
    
    @staticmethod
    def update_sql_from_domain(sql_plan: SQLPlannerPlan, domain_plan: DomainPlannerPlan) -> None:
        """Обновить SQLAlchemy модель из доменной модели"""
        sql_plan.status = domain_plan.status
        sql_plan.version = domain_plan.version
        sql_plan.source = domain_plan.source
        sql_plan.request_payload = domain_plan.request_payload
        sql_plan.response_payload = domain_plan.response_payload
        sql_plan.updated_at = domain_plan.updated_at or datetime.now(timezone.utc)
        sql_plan.deleted = domain_plan.deleted
        
        # Обновляем слоты
        existing_slot_ids = {slot.slot_id for slot in sql_plan.slots}
        for domain_slot in domain_plan.slots:
            if domain_slot.slot_id in existing_slot_ids:
                # Обновляем существующий слот
                sql_slot = next(s for s in sql_plan.slots if s.slot_id == domain_slot.slot_id)
                sql_slot.task_id = domain_slot.task_id
                sql_slot.title = domain_slot.title
                sql_slot.description = domain_slot.description
                sql_slot.start_at = domain_slot.start_at
                sql_slot.end_at = domain_slot.end_at
                sql_slot.updated_at = domain_slot.updated_at or datetime.now(timezone.utc)
            else:
                # Добавляем новый слот
                sql_slot = SQLPlannerSlot(
                    slot_id=domain_slot.slot_id,
                    task_id=domain_slot.task_id,
                    title=domain_slot.title,
                    description=domain_slot.description,
                    start_at=domain_slot.start_at,
                    end_at=domain_slot.end_at,
                    created_at=domain_slot.created_at or datetime.now(timezone.utc),
                    updated_at=domain_slot.updated_at or datetime.now(timezone.utc),
                    plan=sql_plan
                )
                sql_plan.slots.append(sql_slot)
        
        # Удаляем слоты, которых нет в доменной модели
        domain_slot_ids = {slot.slot_id for slot in domain_plan.slots}
        sql_plan.slots[:] = [slot for slot in sql_plan.slots if slot.slot_id in domain_slot_ids]
        
        # Обновляем конфликты
        existing_conflict_ids = {conflict.conflict_id for conflict in sql_plan.conflicts}
        for domain_conflict in domain_plan.conflicts:
            if domain_conflict.conflict_id in existing_conflict_ids:
                # Обновляем существующий конфликт
                sql_conflict = next(c for c in sql_plan.conflicts if c.conflict_id == domain_conflict.conflict_id)
                sql_conflict.slot_id = domain_conflict.slot_id
                sql_conflict.reason = domain_conflict.reason
                sql_conflict.severity = domain_conflict.severity
                sql_conflict.details = domain_conflict.details
                sql_conflict.related_task_id = domain_conflict.related_task_id
                sql_conflict.created_at = domain_conflict.created_at or datetime.now(timezone.utc)
            else:
                # Добавляем новый конфликт
                sql_conflict = SQLPlannerConflict(
                    conflict_id=domain_conflict.conflict_id,
                    slot_id=domain_conflict.slot_id,
                    reason=domain_conflict.reason,
                    severity=domain_conflict.severity,
                    details=domain_conflict.details,
                    related_task_id=domain_conflict.related_task_id,
                    created_at=domain_conflict.created_at or datetime.now(timezone.utc),
                    plan=sql_plan
                )
                sql_plan.conflicts.append(sql_conflict)
        
        # Удаляем конфликты, которых нет в доменной модели
        domain_conflict_ids = {conflict.conflict_id for conflict in domain_plan.conflicts}
        sql_plan.conflicts[:] = [conflict for conflict in sql_plan.conflicts if conflict.conflict_id in domain_conflict_ids]