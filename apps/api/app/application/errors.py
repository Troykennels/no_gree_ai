"""Application-level errors, independent of any web framework."""

from __future__ import annotations


class ApplicationError(Exception):
    """Base class for expected, handled application errors."""


class EmailAlreadyRegistered(ApplicationError):
    def __init__(self, email: str) -> None:
        super().__init__(f"An account with email '{email}' already exists.")
        self.email = email


class InvalidCredentials(ApplicationError):
    def __init__(self) -> None:
        super().__init__("Incorrect email or password.")


class InactiveUser(ApplicationError):
    def __init__(self) -> None:
        super().__init__("This account is inactive.")


class ScoringUnavailable(ApplicationError):
    def __init__(self) -> None:
        super().__init__(
            "The fraud model is not available. Train it with "
            "`python -m snaija_ml.pipelines.train_message_fraud`."
        )
