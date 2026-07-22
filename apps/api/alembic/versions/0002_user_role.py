"""add role column to users (RBAC)

Revision ID: 0002_user_role
Revises: 0001_initial
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision: str = "0002_user_role"
down_revision: str | None = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("role", sa.String(length=20), nullable=False, server_default="user"),
    )


def downgrade() -> None:
    op.drop_column("users", "role")
