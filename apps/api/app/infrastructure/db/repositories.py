"""SQLAlchemy implementations of the application repository ports."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.entities import Scan, User

from .mappers import scan_to_domain, scan_to_model, user_to_domain, user_to_model
from .models import ScanModel, UserModel


class SqlAlchemyUserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_email(self, email: str) -> User | None:
        row = self._session.execute(
            select(UserModel).where(UserModel.email == email)
        ).scalar_one_or_none()
        return user_to_domain(row) if row else None

    def get_by_id(self, user_id: UUID) -> User | None:
        row = self._session.get(UserModel, user_id)
        return user_to_domain(row) if row else None

    def add(self, user: User) -> User:
        row = user_to_model(user)
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return user_to_domain(row)


class SqlAlchemyScanRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, scan: Scan) -> Scan:
        row = scan_to_model(scan)
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return scan_to_domain(row)

    def list_for_user(self, user_id: UUID, limit: int, offset: int) -> list[Scan]:
        rows = self._session.execute(
            select(ScanModel)
            .where(ScanModel.user_id == user_id)
            .order_by(ScanModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        ).scalars().all()
        return [scan_to_domain(r) for r in rows]

    def count_for_user(self, user_id: UUID) -> int:
        return int(
            self._session.execute(
                select(func.count()).select_from(ScanModel).where(ScanModel.user_id == user_id)
            ).scalar_one()
        )
