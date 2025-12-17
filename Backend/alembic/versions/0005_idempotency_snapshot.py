"""idempotency snapshot

Revision ID: 0005_idempotency_snapshot
Revises: 0004_planner_slots_conflicts
Create Date: 2025-12-17
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_idempotency_snapshot"
down_revision = "0004_planner_slots_conflicts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("idempotency_keys", sa.Column("status_code", sa.Integer(), nullable=True))
    op.add_column("idempotency_keys", sa.Column("response_body", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("idempotency_keys", sa.Column("response_headers", postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column("idempotency_keys", "response_headers")
    op.drop_column("idempotency_keys", "response_body")
    op.drop_column("idempotency_keys", "status_code")
