"""Engine status - readiness of every model in the SecureNaija AI Engine."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.infrastructure.ml.scam_scoring_service import ScamScoringService
from app.infrastructure.ml.scoring_service import MlFraudScoringService
from app.infrastructure.ml.transaction_scoring_service import TransactionScoringService
from app.interface.dependencies import (
    get_scam_service,
    get_scoring_service,
    get_transaction_service,
)
from app.interface.schemas import EngineModelStatus, EngineStatusResponse

router = APIRouter(prefix="/engine", tags=["engine"])


@router.get("/status", response_model=EngineStatusResponse)
def engine_status(
    message: Annotated[MlFraudScoringService, Depends(get_scoring_service)],
    scam: Annotated[ScamScoringService, Depends(get_scam_service)],
    transaction: Annotated[TransactionScoringService, Depends(get_transaction_service)],
) -> EngineStatusResponse:
    models = [
        EngineModelStatus(key="message_fraud", name="Message Fraud Detector",
                          ready=message.is_ready, version=message.model_version,
                          error=message.load_error),
        EngineModelStatus(key="scam_detection", name="Scam Detection (Model 1)",
                          ready=scam.is_ready, version=scam.model_version,
                          error=scam.load_error),
        EngineModelStatus(key="transaction_fraud", name="Transaction Fraud (Model 2)",
                          ready=transaction.is_ready, version=transaction.model_version,
                          error=transaction.load_error),
    ]
    status_str = "ok" if all(m.ready for m in models) else "degraded"
    return EngineStatusResponse(status=status_str, models=models)
