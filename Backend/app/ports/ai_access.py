from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Protocol
import uuid


class AIPlannerAccessPolicy(Protocol):
    """Порт для проверки доступа к AI планировщику"""
    
    async def ensure_access(
        self,
        *,
        subscription_status: str,
        user_id: uuid.UUID,
        request_id: str
    ) -> tuple[bool, dict | None]:
        """
        Проверяет доступ пользователя к AI планировщику.
        
        Returns:
            tuple[allowed, upgrade_payload]:
            - allowed: True если доступ разрешен
            - upgrade_payload: dict с информацией для апгрейда если доступ запрещен
        """
        ...


class IdempotencyChecker(Protocol):
    """Порт для проверки идемпотентности"""
    
    async def ensure_idempotent(
        self,
        *,
        user_id: uuid.UUID,
        key: str,
        method: str,
        path: str
    ) -> None:
        """Гарантирует идемпотентность операции"""
        ...


class EventPublisher(Protocol):
    """Порт для публикации событий"""
    
    def publish_upgrade_offered(
        self,
        *,
        request_id: str,
        user_id: uuid.UUID,
        subscription_status: str,
        plan_request_id: uuid.UUID
    ) -> None:
        """Событие: предложение апгрейда"""
        ...
    
    def publish_trial_used(
        self,
        *,
        request_id: str,
        user_id: uuid.UUID,
        plan_request_id: uuid.UUID
    ) -> None:
        """Событие: использование триала"""
        ...
    
    def publish_plan_created(
        self,
        *,
        request_id: str,
        user_id: uuid.UUID,
        plan_request_id: uuid.UUID,
        status: str
    ) -> None:
        """Событие: создание плана"""
        ...


class PlanRepository(Protocol):
    """Порт для работы с планами"""
    
    async def get_by_request_id(
        self,
        *,
        plan_request_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> dict | None:
        """Получить план по ID запроса"""
        ...
    
    async def save_plan(
        self,
        *,
        plan_request_id: uuid.UUID,
        user_id: uuid.UUID,
        plan_data: dict
    ) -> None:
        """Сохранить план"""
        ...