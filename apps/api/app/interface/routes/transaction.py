"""Model 2 - Transaction Fraud endpoint (IEEE-CIS XGBoost / RandomForest)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.infrastructure.ml.transaction_scoring_service import TransactionScoringService
from app.interface.dependencies import get_transaction_service
from app.interface.schemas import (
    TransactionScoreRequest,
    TransactionScoreResponse,
    TxnFactorResponse,
)

router = APIRouter(prefix="/transaction", tags=["transaction"])


def _require_ready(service: TransactionScoringService) -> None:
    if not service.is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The transaction-fraud model is not available yet. "
                   "Train it with `python -m snaija_ml.pipelines.train_transaction_fraud`.",
        )


@router.post("/score", response_model=TransactionScoreResponse)
def score_transaction(
    payload: TransactionScoreRequest,
    service: Annotated[TransactionScoringService, Depends(get_transaction_service)],
) -> TransactionScoreResponse:
    """Score a card transaction. Unknown fields are imputed, so a partial payload
    still returns a calibrated fraud probability, a decision, and SHAP factors."""
    _require_ready(service)
    r = service.score(payload.features)
    return TransactionScoreResponse(
        fraud_probability=r.fraud_probability,
        confidence=r.confidence,
        is_fraud=r.is_fraud,
        decision=r.decision,
        risk_band=r.risk_band,
        reasons=r.reasons,
        verdict=r.verdict,
        risk_explanation=r.risk_explanation,
        factors=[TxnFactorResponse(feature=f.feature, label=f.label, signal=f.signal, weight=f.weight)
                 for f in r.factors],
        model_version=r.model_version,
        algorithm=r.algorithm,
    )


@router.get("/fields")
def transaction_fields(
    service: Annotated[TransactionScoringService, Depends(get_transaction_service)],
) -> dict:
    """The feature names the model accepts (all optional). Handy for building a form."""
    _require_ready(service)
    return service.expected_fields
