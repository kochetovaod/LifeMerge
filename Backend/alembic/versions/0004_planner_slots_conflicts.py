"""Add planner_slots and planner_conflicts tables.

Revision ID: 0004_planner_slots_conflicts
Revises: 0003_infra
Create Date: 2025-12-21
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004_planner_slots_conflicts"
down_revision = "0003_infra"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Таблица для слотов плана
    op.create_table(
        "planner_slots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["plan_id"], ["ai_plan_runs.id"], name="fk_planner_slots_plan_id_ai_plan_runs"),
    )
    op.create_index("ix_planner_slots_plan_id", "planner_slots", ["plan_id"], unique=False)
    op.create_index("ix_planner_slots_slot_id", "planner_slots", ["slot_id"], unique=True)
    op.create_index("ix_planner_slots_task_id", "planner_slots", ["task_id"], unique=False)
    
    # Таблица для конфликтов плана
    op.create_table(
        "planner_conflicts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conflict_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slot_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reason", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="warning"),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("related_task_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["plan_id"], ["ai_plan_runs.id"], name="fk_planner_conflicts_plan_id_ai_plan_runs"),
    )
    op.create_index("ix_planner_conflicts_plan_id", "planner_conflicts", ["plan_id"], unique=False)
    op.create_index("ix_planner_conflicts_conflict_id", "planner_conflicts", ["conflict_id"], unique=True)
    op.create_index("ix_planner_conflicts_slot_id", "planner_conflicts", ["slot_id"], unique=False)
    op.create_index("ix_planner_conflicts_related_task_id", "planner_conflicts", ["related_task_id"], unique=False)
    
    # Добавляем поле source в ai_plan_runs
    op.add_column(
        "ai_plan_runs",
        sa.Column("source", sa.String(length=32), nullable=False, server_default="ai")
    )
    op.add_column(
        "ai_plan_runs",
        sa.Column("deleted", sa.Boolean(), nullable=False, server_default=sa.text("FALSE"))
    )
    
    # Добавляем индексы
    op.create_index("ix_ai_plan_runs_plan_request_id", "ai_plan_runs", ["plan_request_id"], unique=False)
    op.create_index("ix_ai_plan_runs_user_id_status", "ai_plan_runs", ["user_id", "status"], unique=False)
    op.create_index("ix_ai_plan_runs_updated_at", "ai_plan_runs", ["updated_at"], unique=False)


def downgrade() -> None:
    # Удаляем индексы
    op.drop_index("ix_ai_plan_runs_updated_at", table_name="ai_plan_runs")
    op.drop_index("ix_ai_plan_runs_user_id_status", table_name="ai_plan_runs")
    op.drop_index("ix_ai_plan_runs_plan_request_id", table_name="ai_plan_runs")
    
    # Удаляем поля из ai_plan_runs
    op.drop_column("ai_plan_runs", "deleted")
    op.drop_column("ai_plan_runs", "source")
    
    # Удаляем таблицы
    op.drop_index("ix_planner_conflicts_related_task_id", table_name="planner_conflicts")
    op.drop_index("ix_planner_conflicts_slot_id", table_name="planner_conflicts")
    op.drop_index("ix_planner_conflicts_conflict_id", table_name="planner_conflicts")
    op.drop_index("ix_planner_conflicts_plan_id", table_name="planner_conflicts")
    op.drop_table("planner_conflicts")
    
    op.drop_index("ix_planner_slots_task_id", table_name="planner_slots")
    op.drop_index("ix_planner_slots_slot_id", table_name="planner_slots")
    op.drop_index("ix_planner_slots_plan_id", table_name="planner_slots")
    op.drop_table("planner_slots")