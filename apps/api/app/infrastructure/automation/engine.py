"""The SecureNaija Automation Engine — the always-on brain behind the live UI.

Every scored message and transaction flows through here. For each one the engine:

  * runs the right model (scam / transaction),
  * updates the live aggregates — stats, security score, fraud timeline, threat
    heatmap, alerts — in memory,
  * publishes events on the broker so every connected browser updates instantly
    (no manual refresh),
  * records human feedback back into the training data (continuous learning).

The derived state is held in bounded in-memory buffers (swap for Redis to scale
horizontally). A snapshot repaints a fresh page; the event stream keeps it live.
"""

from __future__ import annotations

import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any

from app.infrastructure.learning.feedback_store import FeedbackStore
from app.infrastructure.ml.scam_scoring_service import ScamScoringService
from app.infrastructure.ml.transaction_scoring_service import TransactionScoringService
from app.infrastructure.realtime.broker import EventBroker
from app.infrastructure.security.pii import redact_pii

# Nigerian cities for the threat heatmap (used when an event carries no region).
NIGERIA_REGIONS = [
    "Lagos", "Ibadan", "Abuja", "Kano", "Kaduna", "Port Harcourt", "Benin", "Enugu",
]

_MAX_ALERTS = 40
_MAX_ACTIVITY = 40
_MAX_TIMELINE = 30       # rolling minute buckets
_MAX_ITEMS = 400         # recent scored items retained for feedback lookup


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _grade(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 65:
        return "C"
    if score >= 50:
        return "D"
    return "F"


def _heat_level(threats: int) -> str:
    if threats >= 8:
        return "high"
    if threats >= 3:
        return "medium"
    return "low"


class AutomationEngine:
    def __init__(self, scam: ScamScoringService, transaction: TransactionScoringService,
                 broker: EventBroker, feedback: FeedbackStore) -> None:
        self._scam = scam
        self._txn = transaction
        self._broker = broker
        self._feedback = feedback

        self._stats = {
            "messages_scanned": 0,
            "transactions_analyzed": 0,
            "scams_detected": 0,
            "frauds_blocked": 0,
            "alerts": 0,
            "value_protected": 0.0,
            "feedback_count": feedback.count,
        }
        self._timeline: dict[str, dict[str, int]] = {}
        self._heatmap: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "threats": 0})
        self._alerts: deque[dict[str, Any]] = deque(maxlen=_MAX_ALERTS)
        self._activity: deque[dict[str, Any]] = deque(maxlen=_MAX_ACTIVITY)
        self._items: dict[str, dict[str, Any]] = {}
        self._item_order: deque[str] = deque(maxlen=_MAX_ITEMS)
        self._security_score = 100.0
        self._report: dict[str, Any] | None = None
        self._started_at = _now()

    # ── ingest: messages ─────────────────────────────────────────────────────

    async def ingest_message(self, message: str, channel: str = "sms",
                             region: str | None = None) -> dict[str, Any]:
        result = self._scam.detect(message)  # model scores the RAW text
        is_threat = result.label in {"Scam", "Suspicious"}
        region = region or "Unknown"

        item = {
            "id": uuid.uuid4().hex,
            "kind": "message",
            "channel": channel,
            # Redacted before it is stored / broadcast over SSE / shown in notifications.
            "text": redact_pii(message)[:200],
            "label": result.label,
            "probability": result.scam_probability,
            "confidence": result.confidence,
            "region": region,
            "is_threat": is_threat,
            "ts": _now().isoformat(),
        }
        self._remember(item)
        self._stats["messages_scanned"] += 1
        if result.label == "Scam":
            self._stats["scams_detected"] += 1
        self._tally_timeline(is_threat)
        self._tally_heatmap(region, is_threat)
        self._push_activity(item, f"{result.label} message from {region}")

        if is_threat:
            severity = "critical" if result.label == "Scam" else "warning"
            self._raise_alert(kind="message", severity=severity,
                              title=f"{result.label} message detected",
                              detail=result.explanation, probability=result.scam_probability,
                              region=region, ref_id=item["id"])

        await self._recompute_and_publish(item, is_threat)
        return item

    # ── ingest: transactions ─────────────────────────────────────────────────

    async def ingest_transaction(self, features: dict[str, Any],
                                 region: str | None = None,
                                 bank: str | None = None,
                                 payer: str | None = None) -> dict[str, Any]:
        result = self._txn.score(features)
        is_threat = result.decision in {"decline", "review"}
        region = region or "Unknown"
        amount = float(features.get("TransactionAmt") or 0.0)  # Naira

        item = {
            "id": uuid.uuid4().hex,
            "kind": "transaction",
            "amount": amount,
            "bank": bank,
            "payer": payer,
            "decision": result.decision,
            "label": result.decision,
            "probability": result.fraud_probability,
            "risk_band": result.risk_band,
            "region": region,
            "is_threat": is_threat,
            "ts": _now().isoformat(),
        }
        self._remember(item)
        self._stats["transactions_analyzed"] += 1
        if result.decision == "decline":
            self._stats["frauds_blocked"] += 1
            self._stats["value_protected"] += amount
        self._tally_timeline(is_threat)
        self._tally_heatmap(region, is_threat)
        self._push_activity(item, f"Transaction {result.decision} in {region}")

        if is_threat:
            severity = "critical" if result.decision == "decline" else "warning"
            self._raise_alert(kind="transaction", severity=severity,
                              title=f"Transaction flagged: {result.decision}",
                              detail=result.verdict, probability=result.fraud_probability,
                              region=region, ref_id=item["id"], amount=amount)

        await self._recompute_and_publish(item, is_threat)
        return item

    # ── continuous learning ──────────────────────────────────────────────────

    async def record_feedback(self, item_id: str, label: str) -> dict[str, Any]:
        item = self._items.get(item_id)
        text = item.get("text") if item else None
        predicted = item.get("label") if item else None
        ok = False
        if text:  # only message feedback feeds the text model
            ok = self._feedback.record(text=text, label=label,
                                       predicted_label=predicted, item_id=item_id)
        if item is not None:
            item["feedback"] = label
        for alert in self._alerts:
            if alert.get("ref_id") == item_id:
                alert["feedback"] = label
                alert["status"] = "reviewed"
        self._stats["feedback_count"] = self._feedback.count
        payload = {"item_id": item_id, "label": label, "stored": ok,
                   "feedback_count": self._feedback.count}
        await self._broker.publish({"type": "feedback_recorded", **payload})
        await self._broker.publish({"type": "state", "state": self.snapshot()})
        return payload

    # ── security score + reports ─────────────────────────────────────────────

    def _recompute_security_score(self) -> float:
        window = list(self._items.values())[-120:]
        events = len(window)
        threats = sum(1 for i in window if i.get("is_threat"))
        threat_rate = threats / events if events else 0.0
        open_critical = sum(1 for a in self._alerts
                            if a.get("severity") == "critical" and a.get("status") == "new")
        score = 100.0 - threat_rate * 70.0 - min(open_critical, 8) * 3.0
        self._security_score = round(max(0.0, min(100.0, score)), 1)
        return self._security_score

    async def recompute_security_score(self) -> dict[str, Any]:
        """Public heartbeat entry (called by the scheduler)."""
        before = self._security_score
        after = self._recompute_security_score()
        payload = {"score": after, "grade": _grade(after), "delta": round(after - before, 1)}
        await self._broker.publish({"type": "security_score", **payload})
        return payload

    def generate_daily_report(self) -> dict[str, Any]:
        top_regions = sorted(self._heatmap.items(), key=lambda kv: kv[1]["threats"], reverse=True)[:5]
        report = {
            "id": uuid.uuid4().hex,
            "generated_at": _now().isoformat(),
            "period": "rolling-24h",
            "security_score": self._security_score,
            "security_grade": _grade(self._security_score),
            "totals": dict(self._stats),
            "top_threat_regions": [
                {"region": r, "threats": v["threats"], "total": v["total"]} for r, v in top_regions
            ],
            "critical_alerts": sum(1 for a in self._alerts if a.get("severity") == "critical"),
            "headline": self._report_headline(),
        }
        self._report = report
        return report

    async def generate_daily_report_and_publish(self) -> dict[str, Any]:
        report = self.generate_daily_report()
        await self._broker.publish({"type": "report_ready", "report": report})
        await self._broker.publish({"type": "state", "state": self.snapshot()})
        return report

    def current_report(self) -> dict[str, Any]:
        """The cached daily report, generating one on first request."""
        return self._report or self.generate_daily_report()

    def _report_headline(self) -> str:
        s = self._stats
        blocked = f"N{s['value_protected']:,.0f}" if s["value_protected"] else "N0"
        return (f"{s['scams_detected']} scams and {s['frauds_blocked']} fraudulent "
                f"transactions stopped; {blocked} protected. Security score "
                f"{self._security_score:.0f}/100 ({_grade(self._security_score)}).")

    # ── snapshot ─────────────────────────────────────────────────────────────

    def snapshot(self) -> dict[str, Any]:
        return {
            "stats": dict(self._stats),
            "security_score": self._security_score,
            "security_grade": _grade(self._security_score),
            "risk_score": self._risk_score(),
            "timeline": self._timeline_series(),
            "heatmap": self._heatmap_series(),
            "alerts": list(self._alerts)[::-1],
            "activity": list(self._activity)[::-1],
            "recent_messages": self._recent("message", 8),
            "recent_transactions": self._recent("transaction", 8),
            "analytics": self._analytics(),
            "report": self._report,
            "live_subscribers": self._broker.subscriber_count,
            "uptime_seconds": int((_now() - self._started_at).total_seconds()),
            "updated_at": _now().isoformat(),
        }

    def _risk_score(self) -> int:
        """Current fraud pressure 0-100 = rolling mean fraud probability."""
        window = list(self._items.values())[-60:]
        if not window:
            return 0
        return int(round(sum(i["probability"] for i in window) / len(window) * 100))

    def _recent(self, kind: str, n: int) -> list[dict[str, Any]]:
        items = [i for i in reversed(self._items.values()) if i["kind"] == kind]
        return items[:n]

    def _analytics(self) -> dict[str, Any]:
        window = list(self._items.values())
        msgs = [i for i in window if i["kind"] == "message"]
        txns = [i for i in window if i["kind"] == "transaction"]
        scam = sum(1 for i in msgs if i.get("label") == "Scam")
        suspicious = sum(1 for i in msgs if i.get("label") == "Suspicious")
        safe_msgs = len(msgs) - scam - suspicious
        decline = sum(1 for i in txns if i.get("decision") == "decline")
        review = sum(1 for i in txns if i.get("decision") == "review")
        approve = len(txns) - decline - review
        return {
            "messages": {"Scam": scam, "Suspicious": suspicious, "Safe": safe_msgs},
            "transactions": {"decline": decline, "review": review, "approve": approve},
        }

    # ── internals ────────────────────────────────────────────────────────────

    def _remember(self, item: dict[str, Any]) -> None:
        if len(self._item_order) == self._item_order.maxlen and self._item_order:
            evicted = self._item_order[0]
            self._items.pop(evicted, None)
        self._item_order.append(item["id"])
        self._items[item["id"]] = item

    def _tally_timeline(self, is_threat: bool) -> None:
        bucket = _now().replace(second=0, microsecond=0).isoformat()
        slot = self._timeline.setdefault(bucket, {"threats": 0, "safe": 0})
        slot["threats" if is_threat else "safe"] += 1
        if len(self._timeline) > _MAX_TIMELINE:
            oldest = sorted(self._timeline)[0]
            self._timeline.pop(oldest, None)

    def _tally_heatmap(self, region: str, is_threat: bool) -> None:
        cell = self._heatmap[region]
        cell["total"] += 1
        if is_threat:
            cell["threats"] += 1

    def _push_activity(self, item: dict[str, Any], label: str) -> None:
        self._activity.append({
            "id": item["id"], "kind": item["kind"], "label": label,
            "probability": item["probability"], "is_threat": item["is_threat"],
            "region": item["region"], "ts": item["ts"],
        })

    def _raise_alert(self, *, kind: str, severity: str, title: str, detail: str,
                     probability: float, region: str, ref_id: str,
                     amount: float | None = None) -> dict[str, Any]:
        alert = {
            "id": uuid.uuid4().hex, "ref_id": ref_id, "kind": kind, "severity": severity,
            "title": title, "detail": detail, "probability": probability,
            "region": region, "amount": amount, "status": "new", "feedback": None,
            "ts": _now().isoformat(),
        }
        self._alerts.append(alert)
        self._stats["alerts"] += 1
        return alert

    def _timeline_series(self) -> list[dict[str, Any]]:
        return [{"t": t, **self._timeline[t]} for t in sorted(self._timeline)]

    def _heatmap_series(self) -> list[dict[str, Any]]:
        rows = [{"region": r, "total": v["total"], "threats": v["threats"],
                 "level": _heat_level(v["threats"])}
                for r, v in self._heatmap.items()]
        return sorted(rows, key=lambda x: x["threats"], reverse=True)

    @staticmethod
    def _notification_for(item: dict[str, Any]) -> dict[str, Any]:
        """Priority + human title/body for a scored item (drives the UI notifications)."""
        p = item.get("probability", 0.0)
        if item["kind"] == "message":
            label = item.get("label")
            body = item.get("text", "")[:100]
            if label == "Scam":
                return {"priority": "critical" if p >= 0.85 else "danger",
                        "title": "Scam SMS detected", "body": body}
            if label == "Suspicious":
                return {"priority": "warning", "title": "Suspicious message flagged", "body": body}
            return {"priority": "info", "title": "Message looks safe", "body": body}
        # transaction
        amt = item.get("amount") or 0
        where = " ".join(x for x in (item.get("bank"), item.get("region")) if x)
        body = (f"NGN{int(amt):,}" + (f" - {where}" if where else "")).strip()
        decision = item.get("decision")
        if decision == "decline":
            return {"priority": "critical", "title": "Fraudulent transaction blocked", "body": body}
        if decision == "review":
            return {"priority": "warning", "title": "Transaction looks suspicious", "body": body}
        return {"priority": "info", "title": "Safe transaction", "body": body}

    async def _recompute_and_publish(self, item: dict[str, Any], is_threat: bool) -> None:
        self._recompute_security_score()
        latest_alert = self._alerts[-1] if (is_threat and self._alerts) else None
        await self._broker.publish({"type": "state", "state": self.snapshot()})
        await self._broker.publish({
            "type": "notification",
            "item": item,
            "alert": latest_alert,
            "is_threat": is_threat,
            "notification": self._notification_for(item),
        })
