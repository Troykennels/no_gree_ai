"""Map application errors to HTTP responses so use cases stay web-agnostic."""

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

_STATUS_MAP: dict[type[ApplicationError], int] = {
    EmailAlreadyRegistered: status.HTTP_409_CONFLICT,
    InvalidCredentials: status.HTTP_401_UNAUTHORIZED,
    InactiveUser: status.HTTP_403_FORBIDDEN,
    ScoringUnavailable: status.HTTP_503_SERVICE_UNAVAILABLE,
}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApplicationError)
    async def _handle_application_error(_: Request, exc: ApplicationError) -> JSONResponse:
        code = _STATUS_MAP.get(type(exc), status.HTTP_400_BAD_REQUEST)
        return JSONResponse(status_code=code, content={"detail": str(exc)})
