"""SQLAlchemy ORM models. These are infrastructure detail, kept separate from
the pure domain entities they persist.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# Dialect-portable column types: native UUID/JSONB on PostgreSQL (production),
# portable CHAR(32)/JSON on SQLite (local dev) — one model, both backends.
UUIDType = Uuid(as_uuid=True)
JSONType = JSON().with_variant(JSONB(), "postgresql")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    scans: Mapped[list["ScanModel"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class ScanModel(Base):
    __tablename__ = "scans"
    __table_args__ = (
        Index("ix_scans_user_created", "user_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False, default="other")

    fraud_probability: Mapped[float] = mapped_column(Float, nullable=False)
    is_fraud: Mapped[bool] = mapped_column(Boolean, nullable=False)
    risk_band: Mapped[str] = mapped_column(String(20), nullable=False)
    risk_label: Mapped[str] = mapped_column(String(80), nullable=False)
    verdict: Mapped[str] = mapped_column(Text, nullable=False)
    # Full list of RiskFactors, stored as JSONB (Postgres) / JSON (SQLite) for
    # auditing and dashboards.
    factors: Mapped[list] = mapped_column(JSONType, nullable=False, default=list)
    model_version: Mapped[str] = mapped_column(String(40), nullable=False, default="unknown")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    user: Mapped["UserModel | None"] = relationship(back_populates="scans")
