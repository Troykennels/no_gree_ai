"""In-process async pub/sub broker — the backbone of the Automation Engine.

Every automation (a scored message, a scored transaction, a recalculated security
score, a fresh alert, a generated report) publishes a typed event here. Connected
clients subscribe over Server-Sent Events (``/automation/stream``) and receive the
events the instant they happen — so the UI updates itself with no manual refresh.

This is intentionally dependency-free (pure ``asyncio``) so it runs anywhere the
API runs. For a multi-replica deployment, swap this single class for a Redis
pub/sub adapter behind the same ``publish`` / ``subscribe`` surface — nothing else
changes.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

# Per-subscriber queue depth. If a slow client can't keep up we drop its oldest
# events rather than let one stalled browser tab grow memory without bound.
_QUEUE_MAXSIZE = 200


class EventBroker:
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[dict[str, Any]]] = set()
        self._lock = asyncio.Lock()

    async def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=_QUEUE_MAXSIZE)
        async with self._lock:
            self._subscribers.add(queue)
        return queue

    async def unsubscribe(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        async with self._lock:
            self._subscribers.discard(queue)

    async def publish(self, event: dict[str, Any]) -> None:
        """Fan an event out to every subscriber (never blocks on a slow client)."""
        async with self._lock:
            targets = list(self._subscribers)
        for queue in targets:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                # Drop the oldest event to make room — liveness over completeness.
                try:
                    queue.get_nowait()
                    queue.put_nowait(event)
                except (asyncio.QueueEmpty, asyncio.QueueFull):
                    pass

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)

    async def stream(self, queue: asyncio.Queue[dict[str, Any]],
                     heartbeat_seconds: float = 20.0) -> AsyncIterator[dict[str, Any]]:
        """Yield events for one subscriber, emitting a heartbeat when idle so
        proxies don't close the connection. Always unsubscribes on exit."""
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=heartbeat_seconds)
                    yield event
                except asyncio.TimeoutError:
                    yield {"type": "heartbeat"}
        finally:
            await self.unsubscribe(queue)


# Process-wide singleton broker.
_broker: EventBroker | None = None


def get_broker() -> EventBroker:
    global _broker
    if _broker is None:
        _broker = EventBroker()
    return _broker
