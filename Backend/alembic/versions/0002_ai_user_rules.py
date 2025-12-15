"""Add AI user rules table.

Revision ID: 0002_ai_user_rules
Revises: 0001_init
Create Date: 2025-12-15
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_ai_user_rules"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_user_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quiet_hours", postgresql.JSON(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("breaks", postgresql.JSON(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("blocked_days", postgresql.JSON(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("deleted", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_ai_user_rules_user_id_users"),
        sa.UniqueConstraint("user_id", name="uq_ai_user_rules_user_id"),
    )
    op.create_index("ix_ai_user_rules_user_id", "ai_user_rules", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_ai_user_rules_user_id", table_name="ai_user_rules")
    op.drop_table("ai_user_rules")
