"""Unit tests for the application use cases — no DB, no ML, no web server."""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.application.errors import EmailAlreadyRegistered, InvalidCredentials
from app.application.use_cases.auth import AuthenticateUser, RegisterUser
from app.application.use_cases.detect_message_fraud import (
    DetectMessageFraud,
    ListUserScans,
)
from app.domain.entities import Channel

from .fakes import (
    FakePasswordHasher,
    FakeTokenService,
    InMemoryScanRepository,
    InMemoryUserRepository,
    StubScoringService,
)


def test_register_user_creates_account():
    users = InMemoryUserRepository()
    use_case = RegisterUser(users=users, hasher=FakePasswordHasher())

    user = use_case.execute("Ada@Example.com", "Ada Okeke", "supersecret")

    assert user.email == "ada@example.com"  # normalized
    assert user.hashed_password == "hashed::supersecret"
    assert users.get_by_email("ada@example.com") is not None


def test_register_duplicate_email_rejected():
    users = InMemoryUserRepository()
    use_case = RegisterUser(users=users, hasher=FakePasswordHasher())
    use_case.execute("ada@example.com", "Ada", "supersecret")

    with pytest.raises(EmailAlreadyRegistered):
        use_case.execute("ada@example.com", "Ada Again", "anotherpass")


def test_authenticate_success_and_failure():
    users = InMemoryUserRepository()
    RegisterUser(users, FakePasswordHasher()).execute("ada@example.com", "Ada", "supersecret")
    auth = AuthenticateUser(users, FakePasswordHasher(), FakeTokenService())

    tokens = auth.execute("ada@example.com", "supersecret")
    assert tokens.access_token.startswith("access::")

    with pytest.raises(InvalidCredentials):
        auth.execute("ada@example.com", "wrong")


def test_detect_fraud_persists_only_for_authenticated_users():
    scans = InMemoryScanRepository()
    detect = DetectMessageFraud(scoring=StubScoringService(), scans=scans)

    # Anonymous scan: scored but not persisted.
    anon = detect.execute("Please update your BVN now", channel=Channel.SMS)
    assert anon.assessment.is_fraud is True
    assert len(scans.items) == 0

    # Authenticated scan: persisted.
    user_id = uuid4()
    saved = detect.execute("Update your BVN", channel=Channel.SMS, user_id=user_id)
    assert saved.assessment.is_fraud is True
    assert len(scans.items) == 1


def test_list_user_scans_counts_and_paginates():
    scans = InMemoryScanRepository()
    detect = DetectMessageFraud(scoring=StubScoringService(), scans=scans)
    user_id = uuid4()
    for _ in range(3):
        detect.execute("share your bvn", user_id=user_id)

    items, total = ListUserScans(scans).execute(user_id, limit=2, offset=0)
    assert total == 3
    assert len(items) == 2
