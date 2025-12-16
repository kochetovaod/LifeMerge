from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.task_service import TaskService
from app.db.session import get_db
from app.infrastructure.repositories.task_repository import SQLTaskRepository


def create_task_service(db: AsyncSession) -> TaskService:
    repository = SQLTaskRepository(db)
    return TaskService(repository)


def get_task_service(db: AsyncSession = Depends(get_db)) -> TaskService:
    return create_task_service(db)
