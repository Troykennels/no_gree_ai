"""FastAPI application entrypoint."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import get_settings
from app.core.database import init_dev_db, promote_configured_admins
from app.core.logging_config import configure_logging, get_logger
from app.core.rate_limit import limiter

configure_logging()
_log = get_logger("securenaija.api")
from app.infrastructure.automation.engine import AutomationEngine
from app.interface.dependencies import (
    get_automation_engine,
    get_scam_service,
    get_scoring_service,
    get_transaction_service,
)
from app.interface.error_handlers import register_error_handlers
from app.interface.routes import (
    admin,
    auth,
    automation,
    engine,
    fraud,
    health,
    intelligence,
    scam,
    transaction,
)

settings = get_settings()

API_V1 = "/api/v1"


async def _automation_scheduler(auto_engine: AutomationEngine) -> None:
    """Always-on background loop: recalculates the security score on a heartbeat
    and regenerates the daily security report periodically - so those update on
    their own with no request needed. Cancelled cleanly on shutdown."""
    ticks = 0
    try:
        while True:
            await asyncio.sleep(15)
            await auto_engine.recompute_security_score()
            ticks += 1
            if ticks % 40 == 0:  # roughly every 10 minutes
                await auto_engine.generate_daily_report_and_publish()
    except asyncio.CancelledError:
        pass


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Local dev on SQLite: ensure tables exist (production/Railway uses Alembic).
    init_dev_db()
    # Grant the admin role to any ADMIN_EMAILS accounts (declarative RBAC bootstrap).
    promote_configured_admins()

    # Warm every model singleton at startup so the first user request is fast
    # instead of paying the joblib/XGBoost load cost mid-demo. Load failures are
    # held on each service (is_ready/load_error) and surfaced via /engine/status,
    # never fatal here - a model that isn't trained yet just reports "not ready".
    get_scoring_service()
    get_scam_service()
    get_transaction_service()

    # Start the Automation Engine's background heartbeat (security score + report).
    scheduler_task = asyncio.create_task(_automation_scheduler(get_automation_engine()))
    try:
        yield
    finally:
        scheduler_task.cancel()


app = FastAPI(
    title="No_Gree AI API",
    version="0.2.0",
    description=(
        "AI-powered fraud intelligence for Nigeria. Detects fraud in SMS, WhatsApp, "
        "POS and loan messages before money is lost."
    ),
    # Interactive docs are disabled in production to avoid disclosing the full API.
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
    lifespan=lifespan,
)

# Rate limiting (slowapi): global per-IP default + stricter per-route limits.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# A wildcard origin cannot be combined with credentials (browsers reject it), so
# only allow credentials when the origins are explicit.
_origins = settings.cors_origin_list
_allow_credentials = "*" not in _origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=_allow_credentials,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def _security_headers(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    if settings.is_production:
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )
    return response


register_error_handlers(app)

app.include_router(health.router, prefix=API_V1)
app.include_router(engine.router, prefix=API_V1)
app.include_router(automation.router, prefix=API_V1)
app.include_router(auth.router, prefix=API_V1)
app.include_router(fraud.router, prefix=API_V1)
app.include_router(scam.router, prefix=API_V1)
app.include_router(transaction.router, prefix=API_V1)
app.include_router(intelligence.router, prefix=API_V1)
app.include_router(admin.router, prefix=API_V1)


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    return {"name": "No_Gree AI API", "docs": "/docs", "health": f"{API_V1}/health"}
