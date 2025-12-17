from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
# Ensure all models are imported and registered
import app.models  # noqa: E402,F401