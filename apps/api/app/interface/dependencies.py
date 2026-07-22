"""Composition root: FastAPI dependencies that wire use cases to infrastructure.

This is the one place allowed to know about both the application and infrastructure
layers at once. Everything else stays decoupled.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.application.use_cases.auth import AuthenticateUser, RegisterUser
from app.application.use_cases.detect_message_fraud import DetectMessageFraud, ListUserScans
from app.core import security
from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.domain.entities import User
from app.infrastructure.db.repositories import (
    SqlAlchemyScanRepository,
    SqlAlchemyUserRepository,
)
from app.infrastructure.automation.engine import AutomationEngine
from app.infrastructure.intelligence.engine import FraudIntelligenceEngine
from app.infrastructure.learning.feedback_store import FeedbackStore
from app.infrastructure.ml.scam_scoring_service import ScamScoringService
from app.infrastructure.ml.scoring_service import MlFraudScoringService
from app.infrastructure.ml.transaction_scoring_service import TransactionScoringService
from app.infrastructure.realtime.broker import get_broker
from app.infrastructure.security.adapters import BcryptPasswordHasher, JwtTokenService

# ── Singletons ───────────────────────────────────────────────────────────────

@lru_cache
def get_scoring_service() -> MlFraudScoringService:
    settings = get_settings()
    return MlFraudScoringService(registry_dir=settings.model_registry_dir)


@lru_cache
def get_scam_service() -> ScamScoringService:
    settings = get_settings()
    return ScamScoringService(registry_dir=settings.model_registry_dir)


@lru_cache
def get_transaction_service() -> TransactionScoringService:
    settings = get_settings()
    return TransactionScoringService(registry_dir=settings.model_registry_dir)


@lru_cache
def get_feedback_store() -> FeedbackStore:
    return FeedbackStore()


@lru_cache
def get_intelligence_engine() -> FraudIntelligenceEngine:
    """Fuses the scam + transaction models into one 0-100 risk verdict."""
    return FraudIntelligenceEngine(
        scam=get_scam_service(),
        transaction=get_transaction_service(),
    )


@lru_cache
def get_automation_engine() -> AutomationEngine:
    """The always-on engine: one instance holds the live in-memory state that the
    SSE stream broadcasts. Singleton so every request shares the same state."""
    return AutomationEngine(
        scam=get_scam_service(),
        transaction=get_transaction_service(),
        broker=get_broker(),
        feedback=get_feedback_store(),
    )


# ── Repositories (request-scoped) ────────────────────────────────────────────

def get_user_repository(session: Annotated[Session, Depends(get_session)]) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(session)


def get_scan_repository(session: Annotated[Session, Depends(get_session)]) -> SqlAlchemyScanRepository:
    return SqlAlchemyScanRepository(session)


# ── Use cases ────────────────────────────────────────────────────────────────

def get_register_user(
    users: Annotated[SqlAlchemyUserRepository, Depends(get_user_repository)],
) -> RegisterUser:
    return RegisterUser(users=users, hasher=BcryptPasswordHasher())


def get_authenticate_user(
    users: Annotated[SqlAlchemyUserRepository, Depends(get_user_repository)],
) -> AuthenticateUser:
    return AuthenticateUser(users=users, hasher=BcryptPasswordHasher(), tokens=JwtTokenService())


def get_detect_fraud(
    scans: Annotated[SqlAlchemyScanRepository, Depends(get_scan_repository)],
    scoring: Annotated[MlFraudScoringService, Depends(get_scoring_service)],
) -> DetectMessageFraud:
    return DetectMessageFraud(scoring=scoring, scans=scans)


def get_list_scans(
    scans: Annotated[SqlAlchemyScanRepository, Depends(get_scan_repository)],
) -> ListUserScans:
    return ListUserScans(scans=scans)


# ── Auth extraction ──────────────────────────────────────────────────────────

_bearer = HTTPBearer(auto_error=False)


def _decode_subject(credentials: HTTPAuthorizationCredentials | None) -> UUID | None:
    if credentials is None:
        return None
    try:
        payload = security.decode_token(credentials.credentials)
        if payload.get("type") != security.ACCESS_TOKEN:
            return None
        return UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None


def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    users: Annotated[SqlAlchemyUserRepository, Depends(get_user_repository)],
) -> User | None:
    """Returns the user if a valid token is present, else None (anonymous allowed)."""
    user_id = _decode_subject(credentials)
    if user_id is None:
        return None
    return users.get_by_id(user_id)


def get_current_user(
    user: Annotated[User | None, Depends(get_optional_user)],
) -> User:
    """Requires an authenticated, active user."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive account")
    return user


SettingsDep = Annotated[Settings, Depends(get_settings)]
