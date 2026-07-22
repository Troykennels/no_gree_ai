"""Translation between ORM models and domain entities."""

from __future__ import annotations

from app.domain.entities import (
    Channel,
    FraudAssessment,
    RiskBand,
    RiskFactor,
    Scan,
    User,
)
from app.infrastructure.security.pii import redact_pii

from .models import ScanModel, UserModel


def user_to_domain(row: UserModel) -> User:
    return User(
        id=row.id,
        email=row.email,
        full_name=row.full_name,
        hashed_password=row.hashed_password,
        is_active=row.is_active,
        created_at=row.created_at,
    )


def user_to_model(user: User) -> UserModel:
    return UserModel(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        hashed_password=user.hashed_password,
        is_active=user.is_active,
    )


def scan_to_model(scan: Scan) -> ScanModel:
    a = scan.assessment
    return ScanModel(
        id=scan.id,
        user_id=scan.user_id,
        # NDPR data-minimisation: never persist raw PII (BVN/PIN/PAN/etc.).
        message=redact_pii(scan.message),
        channel=scan.channel.value,
        fraud_probability=a.fraud_probability,
        is_fraud=a.is_fraud,
        risk_band=a.risk_band.value,
        risk_label=a.risk_label,
        verdict=a.verdict,
        factors=[{"label": f.label, "signal": f.signal, "weight": f.weight} for f in a.factors],
        model_version=a.model_version,
    )


def scan_to_domain(row: ScanModel) -> Scan:
    assessment = FraudAssessment(
        fraud_probability=row.fraud_probability,
        is_fraud=row.is_fraud,
        risk_band=RiskBand(row.risk_band),
        risk_label=row.risk_label,
        verdict=row.verdict,
        factors=[
            RiskFactor(label=f["label"], signal=f["signal"], weight=f["weight"])
            for f in (row.factors or [])
        ],
        model_version=row.model_version,
    )
    return Scan(
        id=row.id,
        message=row.message,
        channel=Channel(row.channel),
        assessment=assessment,
        user_id=row.user_id,
        created_at=row.created_at,
    )
