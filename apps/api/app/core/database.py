"""SQLAlchemy engine, session factory, and declarative base."""

from __future__ import annotations

import os
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings

settings = get_settings()


def _normalize_db_url(url: str) -> str:
    """Managed hosts (Railway/Heroku) hand out ``postgres://`` or ``postgresql://``.
    SQLAlchemy needs the explicit psycopg-v3 driver we install, so force the
    ``postgresql+psycopg://`` scheme."""
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


_db_url = _normalize_db_url(settings.database_url)

# SQLite (local dev) needs check_same_thread=False because FastAPI serves requests
# from a threadpool; PostgreSQL (production/Railway) uses the default psycopg args.
_is_sqlite = _db_url.startswith("sqlite")
_connect_args = {"check_same_thread": False} if _is_sqlite else {}

# Explicit connection-pool tuning for PostgreSQL (recycle stale conns; bounded
# pool so replicas don't exhaust Postgres max_connections). Not applicable to
# SQLite, which uses a single-file connection.
_pool_kwargs: dict[str, object] = {}
if not _is_sqlite:
    _pool_kwargs = {
        "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
        "pool_recycle": 1800,
    }

engine = create_engine(
    _db_url,
    pool_pre_ping=True,
    future=True,
    connect_args=_connect_args,
    **_pool_kwargs,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def get_session() -> Iterator[Session]:
    """FastAPI dependency yielding a scoped DB session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_dev_db() -> None:
    """Create tables directly for local SQLite dev. Production/Railway (Postgres)
    uses Alembic migrations instead; this is a no-op there."""
    if not _is_sqlite:
        return
    from app.infrastructure.db import models  # noqa: F401 - registers metadata

    Base.metadata.create_all(bind=engine)


def promote_configured_admins() -> None:
    """Grant the admin role to any existing users whose email is in ADMIN_EMAILS,
    so admins can be provisioned declaratively (idempotent, safe to run each boot)."""
    emails = settings.admin_email_list
    if not emails:
        return
    from app.infrastructure.db.models import UserModel

    try:
        with SessionLocal() as session:
            session.query(UserModel).filter(UserModel.email.in_(emails)).update(
                {UserModel.role: "admin"}, synchronize_session=False)
            session.commit()
    except Exception:  # noqa: BLE001 - never block startup on this
        pass
