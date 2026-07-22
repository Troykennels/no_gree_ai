"""SQLAlchemy engine, session factory, and declarative base."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings

settings = get_settings()

# SQLite (local dev) needs check_same_thread=False because FastAPI serves requests
# from a threadpool; PostgreSQL (production/Railway) uses the default psycopg args.
_is_sqlite = settings.database_url.startswith("sqlite")
_connect_args = {"check_same_thread": False} if _is_sqlite else {}

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
    connect_args=_connect_args,
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
