from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SQLPlannerPlan(Base):
    """SQLAlchemy модель плана"""
    __tablename__ = "ai_plan_runs"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    plan_request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="requested")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="ai")
    request_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    response_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # Relationships
    slots: Mapped[list["SQLPlannerSlot"]] = relationship(
        "SQLPlannerSlot",
        back_populates="plan",
        cascade="all, delete-orphan"
    )
    conflicts: Mapped[list["SQLPlannerConflict"]] = relationship(
        "SQLPlannerConflict",
        back_populates="plan",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"SQLPlannerPlan(id={self.id}, plan_request_id={self.plan_request_id}, status={self.status})"


class SQLPlannerSlot(Base):
    """SQLAlchemy модель слота плана"""
    __tablename__ = "planner_slots"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ai_plan_runs.id"), nullable=False, index=True)
    
    slot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    task_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    
    # Relationships
    plan: Mapped["SQLPlannerPlan"] = relationship("SQLPlannerPlan", back_populates="slots")
    
    def __repr__(self) -> str:
        return f"SQLPlannerSlot(id={self.id}, slot_id={self.slot_id}, title={self.title})"


class SQLPlannerConflict(Base):
    """SQLAlchemy модель конфликта плана"""
    __tablename__ = "planner_conflicts"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ai_plan_runs.id"), nullable=False, index=True)
    
    conflict_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    slot_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    reason: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="warning")
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_task_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    
    # Relationships
    plan: Mapped["SQLPlannerPlan"] = relationship("SQLPlannerPlan", back_populates="conflicts")
    
    def __repr__(self) -> str:
        return f"SQLPlannerConflict(id={self.id}, conflict_id={self.conflict_id}, reason={self.reason})"