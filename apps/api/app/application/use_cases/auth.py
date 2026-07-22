"""Authentication use cases: register and authenticate a user."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from app.application.errors import (
    EmailAlreadyRegistered,
    InactiveUser,
    InvalidCredentials,
)
from app.application.ports import PasswordHasher, TokenService, UserRepository
from app.domain.entities import User

# A real bcrypt hash used to burn the same CPU time when the email is unknown, so
# login latency doesn't reveal whether an account exists (user-enumeration guard).
_DUMMY_HASH = "$2b$12$dStnrs.bN8rODKPENiRI0e.3slyovi.HvBq4eeW6J8C2IKNli5kte"


@dataclass(frozen=True)
class AuthTokens:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RegisterUser:
    def __init__(self, users: UserRepository, hasher: PasswordHasher) -> None:
        self._users = users
        self._hasher = hasher

    def execute(self, email: str, full_name: str, password: str) -> User:
        email = email.strip().lower()
        if self._users.get_by_email(email):
            raise EmailAlreadyRegistered(email)
        user = User(
            id=uuid4(),
            email=email,
            full_name=full_name.strip(),
            hashed_password=self._hasher.hash(password),
            is_active=True,
        )
        return self._users.add(user)


class AuthenticateUser:
    def __init__(
        self,
        users: UserRepository,
        hasher: PasswordHasher,
        tokens: TokenService,
    ) -> None:
        self._users = users
        self._hasher = hasher
        self._tokens = tokens

    def execute(self, email: str, password: str) -> AuthTokens:
        user = self._users.get_by_email(email.strip().lower())
        if user is None:
            # Verify against a dummy hash to equalise timing (anti-enumeration).
            self._hasher.verify(password, _DUMMY_HASH)
            raise InvalidCredentials()
        if not self._hasher.verify(password, user.hashed_password):
            raise InvalidCredentials()
        if not user.is_active:
            raise InactiveUser()
        subject = str(user.id)
        return AuthTokens(
            access_token=self._tokens.create_access_token(subject),
            refresh_token=self._tokens.create_refresh_token(subject),
        )
