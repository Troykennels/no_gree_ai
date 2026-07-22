"""Health & readiness endpoints.

``/health``       liveness — the process is up (always 200 while serving).
``/health/ready`` readiness — DB reachable AND the fraud model loaded (503 if not),
                  so orchestrators (Railway/K8s) only route traffic when usable.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text

from app.core.database import engine
from app.infrastructure.ml.scoring_service import MlFraudScoringService
from app.interface.dependencies import get_scoring_service
from app.interface.schemas import HealthResponse

router = APIRouter(tags=["system"])


def _db_ready() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001 - readiness must never raise
        return False


@router.get("/health", response_model=HealthResponse)
def health(
    scoring: Annotated[MlFraudScoringService, Depends(get_scoring_service)],
) -> HealthResponse:
    db_ok = _db_ready()
    return HealthResponse(
        status="ok" if (scoring.is_ready and db_ok) else "degraded",
        model_ready=scoring.is_ready,
        db_ready=db_ok,
        model_version=scoring.model_version,
        model_error=scoring.load_error,
    )


@router.get("/health/ready", response_model=HealthResponse)
def readiness(
    response: Response,
    scoring: Annotated[MlFraudScoringService, Depends(get_scoring_service)],
) -> HealthResponse:
    db_ok = _db_ready()
    ready = scoring.is_ready and db_ok
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(
        status="ready" if ready else "not_ready",
        model_ready=scoring.is_ready,
        db_ready=db_ok,
        model_version=scoring.model_version,
        model_error=scoring.load_error,
    )
