"""Map application errors to HTTP responses so use cases stay web-agnostic, and
log everything (audit trail for security events, full trace for unexpected errors).
"""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.application.errors import (
    ApplicationError,
    EmailAlreadyRegistered,
    InactiveUser,
    InvalidCredentials,
    ScoringUnavailable,
)
from app.core.logging_config import get_logger

logger = get_logger("securenaija.api")

_STATUS_MAP: dict[type[ApplicationError], int] = {
    EmailAlreadyRegistered: status.HTTP_409_CONFLICT,
    InvalidCredentials: status.HTTP_401_UNAUTHORIZED,
    InactiveUser: status.HTTP_403_FORBIDDEN,
    ScoringUnavailable: status.HTTP_503_SERVICE_UNAVAILABLE,
}

# Security-relevant errors we want in the audit log (not just returned).
_AUDIT = {InvalidCredentials, InactiveUser}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApplicationError)
    async def _handle_application_error(request: Request, exc: ApplicationError) -> JSONResponse:
        code = _STATUS_MAP.get(type(exc), status.HTTP_400_BAD_REQUEST)
        if type(exc) in _AUDIT:
            logger.warning("auth_event=%s path=%s client=%s",
                           type(exc).__name__, request.url.path,
                           request.client.host if request.client else "?")
        return JSONResponse(status_code=code, content={"detail": str(exc)})

    @app.exception_handler(Exception)
    async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        # Log the full trace for observability; return a generic message so we
        # never leak internal detail (paths, stack, driver errors) to clients.
        logger.exception("unhandled_error method=%s path=%s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )
