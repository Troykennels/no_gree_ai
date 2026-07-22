"""Password hashing and JWT token utilities.

These are framework-level concerns (the outermost Clean Architecture ring) and are
exposed to the application layer only through the security ports.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from .config import get_settings

settings = get_settings()

ACCESS_TOKEN = "access"
REFRESH_TOKEN = "refresh"

# bcrypt hashes only the first 72 bytes of the input; longer inputs must be
# truncated explicitly (bcrypt>=4.1 raises instead of silently truncating).
_BCRYPT_MAX_BYTES = 72


def _to_bcrypt_bytes(plain: str) -> bytes:
    return plain.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(_to_bcrypt_bytes(plain), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_to_bcrypt_bytes(plain), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def _create_token(subject: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str) -> str:
    return _create_token(
        subject, ACCESS_TOKEN, timedelta(minutes=settings.access_token_expire_minutes)
    )


def create_refresh_token(subject: str) -> str:
    return _create_token(
        subject, REFRESH_TOKEN, timedelta(days=settings.refresh_token_expire_days)
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT. Raises jwt.PyJWTError on any problem."""
    return jwt.decode(
        token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
    )
