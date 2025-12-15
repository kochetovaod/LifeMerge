from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.core.config import settings


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    is_pro: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    trial_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=lambda: datetime.now(timezone.utc)
    )
    trial_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=lambda: datetime.now(timezone.utc) + timedelta(days=settings.TRIAL_PERIOD_DAYS),
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
