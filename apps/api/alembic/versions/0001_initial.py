"""initial schema: users and scans

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-20
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("full_name", sa.String(length=160), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "scans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False, server_default="other"),
        sa.Column("fraud_probability", sa.Float(), nullable=False),
        sa.Column("is_fraud", sa.Boolean(), nullable=False),
        sa.Column("risk_band", sa.String(length=20), nullable=False),
        sa.Column("risk_label", sa.String(length=80), nullable=False),
        sa.Column("verdict", sa.Text(), nullable=False),
        sa.Column("factors", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("model_version", sa.String(length=40), nullable=False, server_default="unknown"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )
    op.create_index("ix_scans_user_id", "scans", ["user_id"])
    op.create_index("ix_scans_user_created", "scans", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_scans_user_created", table_name="scans")
    op.drop_index("ix_scans_user_id", table_name="scans")
    op.drop_table("scans")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
