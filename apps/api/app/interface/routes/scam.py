"""Model 1 - Scam Detection endpoint (Safe / Suspicious / Scam)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.infrastructure.ml.scam_scoring_service import ScamScoringService
from app.interface.dependencies import get_scam_service
from app.interface.schemas import (
    ScamDetectRequest,
    ScamDetectResponse,
    ScamWordResponse,
)

router = APIRouter(prefix="/scam", tags=["scam"])


@router.post("/detect", response_model=ScamDetectResponse)
def detect_scam(
    payload: ScamDetectRequest,
    service: Annotated[ScamScoringService, Depends(get_scam_service)],
) -> ScamDetectResponse:
    """Screen a message and return a 3-way verdict with highlighted words.

    Open to anonymous users - ideal for the landing-page 'try it' demo.
    """
    if not service.is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The scam-detection model is not available yet. "
                   "Train it with `python -m snaija_ml.pipelines.train_scam_detection`.",
        )
    r = service.detect(payload.message)
    return ScamDetectResponse(
        label=r.label,
        scam_probability=r.scam_probability,
        confidence=r.confidence,
        highlighted_words=[ScamWordResponse(word=w.word, weight=w.weight) for w in r.highlighted_words],
        explanation=r.explanation,
        model_version=r.model_version,
    )
