"""In-memory audit log for security-relevant events (auth, admin, account changes).

A bounded ring buffer surfaced to admins via ``GET /admin/audit-logs``. It mirrors
what is already written to the application log, so there is one queryable trail.
For long-term retention/compliance, persist these to a table or log sink; the
interface (``record`` / ``recent``) stays the same.
"""

from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from typing import Any

_MAX = 500


class AuditStore:
    def __init__(self) -> None:
        self._events: deque[dict[str, Any]] = deque(maxlen=_MAX)

    def record(self, event: str, actor: str = "-", detail: str = "") -> None:
        self._events.append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "actor": actor,
            "detail": detail,
        })

    def recent(self, limit: int = 100) -> list[dict[str, Any]]:
        return list(self._events)[-limit:][::-1]

    @property
    def count(self) -> int:
        return len(self._events)


_store: AuditStore | None = None


def get_audit_store() -> AuditStore:
    global _store
    if _store is None:
        _store = AuditStore()
    return _store
