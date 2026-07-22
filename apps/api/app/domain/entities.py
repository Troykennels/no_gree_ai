"""Domain entities and value objects.

Pure Python — no SQLAlchemy, no FastAPI, no ML library imports. This is the
innermost ring; everything else depends on it, it depends on nothing.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


class Channel(str, enum.Enum):
    """Where the suspicious message arrived from."""

    SMS = "sms"
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    POS = "pos"
    OTHER = "other"


class RiskBand(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    ELEVATED = "elevated"
    LOW = "low"
    MINIMAL = "minimal"


@dataclass(frozen=True)
class RiskFactor:
    """A single human-readable reason contributing to the verdict."""

    label: str
    signal: str          # "fraud" | "safe"
    weight: float        # relative importance (absolute SHAP contribution)


@dataclass(frozen=True)
class FraudAssessment:
    """The result of scoring one message — a value object, immutable."""

    fraud_probability: float
    is_fraud: bool
    risk_band: RiskBand
    risk_label: str
    verdict: str
    factors: list[RiskFactor] = field(default_factory=list)
    model_version: str = "unknown"


@dataclass
class User:
    id: UUID
    email: str
    full_name: str
    hashed_password: str
    is_active: bool = True
    role: str = "user"          # "user" | "admin"
    created_at: datetime | None = None

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


@dataclass
class Scan:
    """A persisted fraud check performed by (optionally) a user."""

    id: UUID
    message: str
    channel: Channel
    assessment: FraudAssessment
    user_id: UUID | None = None
    created_at: datetime | None = None
