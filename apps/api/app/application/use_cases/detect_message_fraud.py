"""Core use case: assess a message for fraud and (optionally) persist the scan."""

from __future__ import annotations

from uuid import UUID, uuid4

from app.application.errors import ScoringUnavailable
from app.application.ports import FraudScoringService, ScanRepository
from app.domain.entities import Channel, Scan


class DetectMessageFraud:
    def __init__(self, scoring: FraudScoringService, scans: ScanRepository) -> None:
        self._scoring = scoring
        self._scans = scans

    def execute(
        self,
        message: str,
        channel: Channel = Channel.OTHER,
        user_id: UUID | None = None,
        persist: bool = True,
    ) -> Scan:
        if not self._scoring.is_ready:
            raise ScoringUnavailable()

        assessment = self._scoring.score_message(message)
        scan = Scan(
            id=uuid4(),
            message=message,
            channel=channel,
            assessment=assessment,
            user_id=user_id,
        )
        # We persist history only for signed-in users; anonymous "try it" scans
        # on the landing page are scored but not stored.
        if persist and user_id is not None:
            scan = self._scans.add(scan)
        return scan


class ListUserScans:
    def __init__(self, scans: ScanRepository) -> None:
        self._scans = scans

    def execute(self, user_id: UUID, limit: int = 20, offset: int = 0) -> tuple[list[Scan], int]:
        items = self._scans.list_for_user(user_id, limit=limit, offset=offset)
        total = self._scans.count_for_user(user_id)
        return items, total
