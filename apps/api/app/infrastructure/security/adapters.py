"""Security port implementations wrapping the core security utilities."""

from __future__ import annotations

from app.core import security


class BcryptPasswordHasher:
    def hash(self, plain: str) -> str:
        return security.hash_password(plain)

    def verify(self, plain: str, hashed: str) -> bool:
        return security.verify_password(plain, hashed)


class JwtTokenService:
    def create_access_token(self, subject: str) -> str:
        return security.create_access_token(subject)

    def create_refresh_token(self, subject: str) -> str:
        return security.create_refresh_token(subject)
