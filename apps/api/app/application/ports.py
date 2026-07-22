"""Ports — the interfaces the application layer depends on.

Concrete implementations live in the infrastructure layer. Use cases receive these
as constructor arguments, so business logic never imports a database driver or an
ML library directly (Dependency Inversion).
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.domain.entities import FraudAssessment, Scan, User


class UserRepository(Protocol):
    def get_by_email(self, email: str) -> User | None: ...
    def get_by_id(self, user_id: UUID) -> User | None: ...
    def add(self, user: User) -> User: ...


class ScanRepository(Protocol):
    def add(self, scan: Scan) -> Scan: ...
    def list_for_user(self, user_id: UUID, limit: int, offset: int) -> list[Scan]: ...
    def count_for_user(self, user_id: UUID) -> int: ...


class FraudScoringService(Protocol):
    """Scores a raw message and returns a domain FraudAssessment."""

    def score_message(self, message: str) -> FraudAssessment: ...

    @property
    def is_ready(self) -> bool: ...


class PasswordHasher(Protocol):
    def hash(self, plain: str) -> str: ...
    def verify(self, plain: str, hashed: str) -> bool: ...


class TokenService(Protocol):
    def create_access_token(self, subject: str) -> str: ...
    def create_refresh_token(self, subject: str) -> str: ...
