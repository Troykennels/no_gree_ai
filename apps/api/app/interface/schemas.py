"""Pydantic request/response schemas — the API's public contract."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domain.entities import Channel, Scan


# ── Auth ─────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=160)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str
    is_active: bool
    role: str = "user"
    created_at: datetime | None = None


# ── Fraud detection ──────────────────────────────────────────────────────────

class DetectRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000, description="The suspicious message text")
    channel: Channel = Channel.OTHER


class RiskFactorResponse(BaseModel):
    label: str
    signal: str  # "fraud" | "safe"
    weight: float


class AssessmentResponse(BaseModel):
    fraud_probability: float
    is_fraud: bool
    risk_band: str
    risk_label: str
    verdict: str
    factors: list[RiskFactorResponse]
    model_version: str


class ScanResponse(BaseModel):
    id: UUID
    message: str
    channel: Channel
    assessment: AssessmentResponse
    created_at: datetime | None = None

    @classmethod
    def from_domain(cls, scan: Scan) -> "ScanResponse":
        a = scan.assessment
        return cls(
            id=scan.id,
            message=scan.message,
            channel=scan.channel,
            created_at=scan.created_at,
            assessment=AssessmentResponse(
                fraud_probability=a.fraud_probability,
                is_fraud=a.is_fraud,
                risk_band=a.risk_band.value,
                risk_label=a.risk_label,
                verdict=a.verdict,
                model_version=a.model_version,
                factors=[
                    RiskFactorResponse(label=f.label, signal=f.signal, weight=f.weight)
                    for f in a.factors
                ],
            ),
        )


class ScanListResponse(BaseModel):
    items: list[ScanResponse]
    total: int
    limit: int
    offset: int


# ── Model 1: Scam Detection (Safe / Suspicious / Scam) ───────────────────────

class ScamDetectRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000, description="The message text to screen")


class ScamWordResponse(BaseModel):
    word: str
    weight: float


class ScamDetectResponse(BaseModel):
    label: str                       # Safe | Suspicious | Scam
    scam_probability: float
    confidence: float
    highlighted_words: list[ScamWordResponse]
    explanation: str
    model_version: str


# ── Model 2: Transaction Fraud ───────────────────────────────────────────────

class TransactionScoreRequest(BaseModel):
    """A card transaction as a flexible feature map.

    Send whatever fields you have (e.g. TransactionAmt, ProductCD, card4, card6,
    P_emaildomain, C1..C14, D1..D15, M1..M9, V*). Anything omitted is imputed
    exactly as during training - so even a couple of fields returns a score.
    """

    features: dict[str, float | int | str | None] = Field(
        default_factory=dict, description="transaction_field -> value (all optional)"
    )


class TxnFactorResponse(BaseModel):
    feature: str
    label: str
    signal: str                      # "fraud" | "safe"
    weight: float


class TransactionScoreResponse(BaseModel):
    fraud_probability: float
    confidence: float
    is_fraud: bool
    decision: str                    # approve | review | decline
    risk_band: str                   # minimal | low | elevated | high | critical
    reasons: list[str]               # plain-English red flags
    verdict: str                     # human explanation
    risk_explanation: str            # what the risk means + what could happen
    factors: list[TxnFactorResponse]
    model_version: str
    algorithm: str


# ── Fraud Intelligence Engine ────────────────────────────────────────────────

class IntelligenceTransactionInput(BaseModel):
    features: dict[str, float | int | str | None] = Field(default_factory=dict)


class IntelligenceRequest(BaseModel):
    message: str | None = Field(default=None, max_length=5000)
    channel: Channel = Channel.SMS
    transaction: IntelligenceTransactionInput | None = None


class SignalResponse(BaseModel):
    type: str
    label: str
    severity: str


class RecommendationResponse(BaseModel):
    id: str
    action: str
    detail: str
    priority: str


class IntelligenceResponse(BaseModel):
    overall_risk_score: int
    category: str                 # Safe | Low | Medium | High | Critical
    confidence: float             # 0..1
    summary: str
    human_explanation: str
    risk_explanation: str
    reasons: list[str]            # plain-English red flags
    scam: dict | None = None
    transaction: dict | None = None
    signals: list[SignalResponse]
    recommendations: list[RecommendationResponse]
    model_versions: dict[str, str]
    assessed_at: str


# ── Automation Engine ────────────────────────────────────────────────────────

class IngestMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    channel: Channel = Channel.SMS
    region: str | None = Field(default=None, max_length=64)


class IngestTransactionRequest(BaseModel):
    features: dict[str, float | int | str | None] = Field(default_factory=dict)
    region: str | None = Field(default=None, max_length=64)


class FeedbackRequest(BaseModel):
    item_id: str = Field(min_length=1, max_length=64)
    label: str = Field(description="Safe or Scam")


class SimulateRequest(BaseModel):
    count: int = Field(default=40, ge=1, le=200)
    interval_ms: int = Field(default=900, ge=100, le=5000)


# ── Engine status ────────────────────────────────────────────────────────────

class EngineModelStatus(BaseModel):
    key: str
    name: str
    ready: bool
    version: str
    error: str | None = None


class EngineStatusResponse(BaseModel):
    status: str
    models: list[EngineModelStatus]


# ── Health ───────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    model_ready: bool
    db_ready: bool = True
    model_version: str
    model_error: str | None = None
