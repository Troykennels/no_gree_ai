"""In-memory fakes for the ports, so use cases can be tested without a DB or ML."""

from __future__ import annotations

from uuid import UUID

from app.domain.entities import (
    FraudAssessment,
    RiskBand,
    RiskFactor,
    Scan,
    User,
)


class InMemoryUserRepository:
    def __init__(self) -> None:
        self._by_email: dict[str, User] = {}
        self._by_id: dict[UUID, User] = {}

    def get_by_email(self, email: str) -> User | None:
        return self._by_email.get(email)

    def get_by_id(self, user_id: UUID) -> User | None:
        return self._by_id.get(user_id)

    def add(self, user: User) -> User:
        self._by_email[user.email] = user
        self._by_id[user.id] = user
        return user


class InMemoryScanRepository:
    def __init__(self) -> None:
        self.items: list[Scan] = []

    def add(self, scan: Scan) -> Scan:
        self.items.append(scan)
        return scan

    def list_for_user(self, user_id: UUID, limit: int, offset: int) -> list[Scan]:
        rows = [s for s in self.items if s.user_id == user_id]
        return rows[offset : offset + limit]

    def count_for_user(self, user_id: UUID) -> int:
        return len([s for s in self.items if s.user_id == user_id])


class FakePasswordHasher:
    def hash(self, plain: str) -> str:
        return f"hashed::{plain}"

    def verify(self, plain: str, hashed: str) -> bool:
        return hashed == f"hashed::{plain}"


class FakeTokenService:
    def create_access_token(self, subject: str) -> str:
        return f"access::{subject}"

    def create_refresh_token(self, subject: str) -> str:
        return f"refresh::{subject}"


class StubScoringService:
    """Flags a message as fraud if it contains the word 'bvn'."""

    is_ready = True

    def score_message(self, message: str) -> FraudAssessment:
        fraud = "bvn" in message.lower()
        return FraudAssessment(
            fraud_probability=0.94 if fraud else 0.05,
            is_fraud=fraud,
            risk_band=RiskBand.CRITICAL if fraud else RiskBand.MINIMAL,
            risk_label="Almost certainly fraud" if fraud else "Looks safe",
            verdict="stub verdict",
            factors=[RiskFactor(label="Asks for your BVN", signal="fraud", weight=1.2)]
            if fraud
            else [],
            model_version="test",
        )
