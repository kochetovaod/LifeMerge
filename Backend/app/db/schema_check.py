from __future__ import annotations

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


async def ensure_schema_up_to_date(engine: AsyncEngine, alembic_ini_path: str = "alembic.ini") -> None:
    """
    Stage/Prod startup gate:
      - Alembic version table must exist
      - DB revision must equal alembic head
    """
    cfg = Config(alembic_ini_path)
    script = ScriptDirectory.from_config(cfg)
    head = script.get_current_head()

    async with engine.connect() as conn:
        # If alembic_version table is missing, this will fail -> block startup
        try:
            # quick existence probe (works if table exists)
            await conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
        except Exception as e:
            raise RuntimeError(
                "Database schema is not initialized via Alembic (missing alembic_version). "
                "Run: alembic upgrade head"
            ) from e

        def _get_current_rev(sync_conn) -> str | None:
            ctx = MigrationContext.configure(sync_conn)
            return ctx.get_current_revision()

        current = await conn.run_sync(_get_current_rev)

    if current != head:
        raise RuntimeError(
            f"Database schema is out of date: current={current}, head={head}. "
            "Run: alembic upgrade head"
        )
