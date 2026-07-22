"""drop redundant ix_scans_user_id (composite ix_scans_user_created covers it)

Revision ID: 0003_drop_scan_idx
Revises: 0002_user_role
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision: str = "0003_drop_scan_idx"
down_revision: str | None = "0002_user_role"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_scans_user_id", table_name="scans")


def downgrade() -> None:
    op.create_index("ix_scans_user_id", "scans", ["user_id"])
