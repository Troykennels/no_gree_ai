"""Fraud Intelligence Engine endpoint — one fused verdict + AI recommendations."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.infrastructure.intelligence.engine import FraudIntelligenceEngine
from app.infrastructure.ml.scam_scoring_service import ScamScoringService
from app.infrastructure.ml.transaction_scoring_service import TransactionScoringService
from app.interface.dependencies import (
    get_intelligence_engine,
    get_scam_service,
    get_transaction_service,
)
from app.interface.schemas import IntelligenceRequest, IntelligenceResponse

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


@router.post("/assess", response_model=IntelligenceResponse)
def assess(
    payload: IntelligenceRequest,
    engine: Annotated[FraudIntelligenceEngine, Depends(get_intelligence_engine)],
    scam: Annotated[ScamScoringService, Depends(get_scam_service)],
    txn: Annotated[TransactionScoringService, Depends(get_transaction_service)],
) -> IntelligenceResponse:
    """Fuse the scam + transaction models into a single 0-100 risk score, a
    category (Safe/Low/Medium/High/Critical) and instant AI recommendations.

    Provide a ``message``, a ``transaction`` (partial features are fine), or both.
    """
    has_message = bool(payload.message and payload.message.strip())
    if not has_message and not payload.transaction:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Provide a message, a transaction, or both to assess.",
        )
    # Never silently return "Safe" because a requested model failed to load.
    if has_message and not scam.is_ready:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "Scam-detection model is not available right now.")
    if payload.transaction and not txn.is_ready:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "Transaction-fraud model is not available right now.")
    result = engine.assess(
        message=payload.message,
        channel=payload.channel.value,
        transaction_features=payload.transaction.features if payload.transaction else None,
    )
    return IntelligenceResponse(
        overall_risk_score=result.overall_risk_score,
        category=result.category,
        confidence=result.confidence,
        summary=result.summary,
        human_explanation=result.human_explanation,
        risk_explanation=result.risk_explanation,
        reasons=result.reasons,
        scam=result.scam,
        transaction=result.transaction,
        signals=result.signals,
        recommendations=result.recommendations,
        model_versions=result.model_versions,
        assessed_at=result.assessed_at,
    )
