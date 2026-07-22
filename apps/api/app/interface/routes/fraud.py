"""Fraud detection endpoints — the core product surface."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.application.use_cases.detect_message_fraud import (
    DetectMessageFraud,
    ListUserScans,
)
from app.domain.entities import User
from app.interface.dependencies import (
    get_current_user,
    get_detect_fraud,
    get_list_scans,
    get_optional_user,
)
from app.interface.schemas import (
    DetectRequest,
    ScanListResponse,
    ScanResponse,
)

router = APIRouter(prefix="/fraud", tags=["fraud"])


@router.post("/detect", response_model=ScanResponse)
def detect(
    payload: DetectRequest,
    use_case: Annotated[DetectMessageFraud, Depends(get_detect_fraud)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> ScanResponse:
    """Assess a message for fraud.

    Open to anonymous users (great for the landing-page 'try it' demo). If a valid
    token is provided, the scan is saved to the user's history.
    """
    scan = use_case.execute(
        message=payload.message,
        channel=payload.channel,
        user_id=user.id if user else None,
    )
    return ScanResponse.from_domain(scan)


@router.get("/scans", response_model=ScanListResponse)
def list_scans(
    use_case: Annotated[ListUserScans, Depends(get_list_scans)],
    user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ScanListResponse:
    """The signed-in user's scan history, most recent first."""
    items, total = use_case.execute(user_id=user.id, limit=limit, offset=offset)
    return ScanListResponse(
        items=[ScanResponse.from_domain(s) for s in items],
        total=total,
        limit=limit,
        offset=offset,
    )
