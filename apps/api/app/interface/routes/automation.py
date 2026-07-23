"""The No_Gree AI Automation Engine API.

Real-time, no-manual-refresh operations:

  * ``GET  /automation/stream``          Server-Sent Events — the live feed every
                                         dashboard subscribes to.
  * ``GET  /automation/snapshot``        Full current state (initial page paint).
  * ``POST /automation/ingest/message``  Score a message -> updates everything live.
  * ``POST /automation/ingest/transaction`` Score a transaction -> updates live.
  * ``POST /automation/simulate``        Drive a realistic live demo feed.
  * ``POST /automation/feedback``        Mark Safe/Scam -> continuous learning.
  * ``GET  /automation/report/daily``    The auto-generated daily security report.
"""

from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from app.core.rate_limit import limiter
from app.domain.entities import User
from app.infrastructure.automation.engine import AutomationEngine
from app.infrastructure.automation.simulator import get_simulation_manager
from app.infrastructure.ml.scam_scoring_service import ScamScoringService
from app.infrastructure.ml.transaction_scoring_service import TransactionScoringService
from app.infrastructure.realtime.broker import EventBroker, get_broker
from app.interface.dependencies import (
    get_automation_engine,
    get_current_user,
    get_scam_service,
    get_transaction_service,
)
from app.interface.schemas import (
    FeedbackRequest,
    IngestMessageRequest,
    IngestTransactionRequest,
    SimulateRequest,
)

router = APIRouter(prefix="/automation", tags=["automation"])

EngineDep = Annotated[AutomationEngine, Depends(get_automation_engine)]


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event, default=str)}\n\n"


@router.get("/stream")
async def stream(
    request: Request,
    engine: EngineDep,
    broker: Annotated[EventBroker, Depends(get_broker)],
) -> StreamingResponse:
    """Server-Sent Events stream. Sends the current state immediately, then every
    automation event as it happens. The browser's EventSource stays connected."""
    queue = await broker.subscribe()

    async def gen():
        yield _sse({"type": "state", "state": engine.snapshot()})
        async for event in broker.stream(queue):
            if await request.is_disconnected():
                break
            yield _sse(event)

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # disable proxy buffering (nginx)
        },
    )


@router.get("/snapshot")
async def snapshot(engine: EngineDep) -> dict:
    return engine.snapshot()


@router.post("/ingest/message")
async def ingest_message(
    payload: IngestMessageRequest,
    engine: EngineDep,
    scam: Annotated[ScamScoringService, Depends(get_scam_service)],
    _user: Annotated[User, Depends(get_current_user)],  # auth required (anti-abuse)
) -> dict:
    if not scam.is_ready:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "Scam-detection model not available.")
    return await engine.ingest_message(payload.message, payload.channel.value, payload.region)


@router.post("/ingest/transaction")
async def ingest_transaction(
    payload: IngestTransactionRequest,
    engine: EngineDep,
    txn: Annotated[TransactionScoringService, Depends(get_transaction_service)],
    _user: Annotated[User, Depends(get_current_user)],  # auth required (anti-abuse)
) -> dict:
    if not txn.is_ready:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "Transaction-fraud model not available.")
    return await engine.ingest_transaction(payload.features, payload.region)


@router.post("/simulate")
@limiter.limit("6/minute")
async def simulate(request: Request, payload: SimulateRequest, engine: EngineDep) -> dict:
    """Start a realistic live feed so the whole dashboard animates on its own."""
    mgr = get_simulation_manager()
    started = mgr.start(engine, count=payload.count, interval_ms=payload.interval_ms)
    return {"started": started, "running": mgr.running,
            "count": payload.count, "interval_ms": payload.interval_ms}


@router.post("/simulate/stop")
async def simulate_stop() -> dict:
    get_simulation_manager().stop()
    return {"running": False}


@router.post("/feedback")
@limiter.limit("60/minute")
async def feedback(request: Request, payload: FeedbackRequest, engine: EngineDep) -> dict:
    # Provenance is enforced in the engine: feedback only applies to an item that
    # already exists in live state (the text comes from the stored, redacted item,
    # never from the client), so this cannot inject arbitrary training data.
    if payload.label.strip().capitalize() not in {"Safe", "Scam"}:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "label must be 'Safe' or 'Scam'.")
    return await engine.record_feedback(payload.item_id, payload.label)


@router.get("/report/daily")
async def daily_report(engine: EngineDep) -> dict:
    return engine.current_report()
