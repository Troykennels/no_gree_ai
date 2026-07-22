"""Fraud Intelligence Engine — fuse both models into one verdict + AI actions.

Runs Model 1 (scam text) and/or Model 2 (transaction fraud) on whatever the caller
provides, fuses their probabilities into a single **0–100 overall risk score**,
assigns a **category** (Safe / Low / Medium / High / Critical), and returns
**instant AI recommendations**. Everything is synchronous and fast — one call in,
a complete, explainable risk picture out.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.infrastructure.intelligence.recommendations import (
    detect_signals,
    recommend,
)
from app.infrastructure.ml.scam_scoring_service import ScamScoringService
from app.infrastructure.ml.transaction_scoring_service import TransactionScoringService

CATEGORIES = ["Safe", "Low", "Medium", "High", "Critical"]


def _categorize(score: int) -> str:
    if score >= 85:
        return "Critical"
    if score >= 65:
        return "High"
    if score >= 40:
        return "Medium"
    if score >= 15:
        return "Low"
    return "Safe"


def _noisy_or(probs: list[float]) -> float:
    """Combine independent risk probabilities: P = 1 - prod(1 - p_i).

    Either channel being fraudulent raises the overall risk — the right behaviour
    for fusing two separate fraud signals into one score.
    """
    keep = 1.0
    for p in probs:
        keep *= (1.0 - max(0.0, min(1.0, p)))
    return 1.0 - keep


@dataclass
class IntelligenceResult:
    overall_risk_score: int
    category: str
    confidence: float                 # 0..1, how sure the engine is
    summary: str                      # headline
    human_explanation: str            # plain-language "what this is"
    risk_explanation: str             # what the risk means + what could happen
    reasons: list[str] = field(default_factory=list)   # plain red-flag phrases
    scam: dict[str, Any] | None = None
    transaction: dict[str, Any] | None = None
    signals: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[dict[str, Any]] = field(default_factory=list)
    model_versions: dict[str, str] = field(default_factory=dict)
    assessed_at: str = ""


class FraudIntelligenceEngine:
    def __init__(self, scam: ScamScoringService, transaction: TransactionScoringService) -> None:
        self._scam = scam
        self._txn = transaction

    def assess(self, *, message: str | None = None, channel: str = "sms",
               transaction_features: dict[str, Any] | None = None) -> IntelligenceResult:
        scam_result = None
        txn_result = None
        probs: list[float] = []
        model_versions: dict[str, str] = {}

        if message and message.strip() and self._scam.is_ready:
            scam_result = self._scam.detect(message)
            probs.append(scam_result.scam_probability)
            model_versions["scam_detection"] = scam_result.model_version

        if transaction_features and self._txn.is_ready:
            txn_result = self._txn.score(transaction_features)
            probs.append(txn_result.fraud_probability)
            model_versions["transaction_fraud"] = txn_result.algorithm + " " + txn_result.model_version

        fused = _noisy_or(probs) if probs else 0.0
        score = fused * 100.0

        # Severity floors so a single strong signal is never diluted by fusion.
        strong = int(bool(scam_result and scam_result.label == "Scam")) \
            + int(bool(txn_result and txn_result.decision == "decline"))
        mild = int(bool(scam_result and scam_result.label == "Suspicious")) \
            + int(bool(txn_result and txn_result.decision == "review"))
        if strong >= 2:
            score = max(score, 88.0)
        elif strong == 1:
            score = max(score, 68.0)
        elif mild:
            score = max(score, 42.0)

        score_int = int(round(min(100.0, max(0.0, score))))
        category = _categorize(score_int)

        signals = detect_signals(message, scam_result, txn_result)
        recommendations = recommend(
            signals, category=category,
            has_message=scam_result is not None,
            has_transaction=txn_result is not None,
        )
        reasons = self._reasons(signals, txn_result)
        confidence = self._confidence(scam_result, txn_result)
        summary = self._summarize(category, score_int, scam_result, txn_result, len(recommendations))
        human_explanation = self._human_explanation(scam_result, txn_result, reasons)
        risk_explanation = self._risk_explanation(category, score_int)

        return IntelligenceResult(
            overall_risk_score=score_int,
            category=category,
            confidence=confidence,
            summary=summary,
            human_explanation=human_explanation,
            risk_explanation=risk_explanation,
            reasons=reasons,
            scam=self._scam_component(scam_result),
            transaction=self._txn_component(txn_result),
            signals=[{"type": s.type, "label": s.label, "severity": s.severity} for s in signals],
            recommendations=[{"id": r.id, "action": r.action, "detail": r.detail,
                              "priority": r.priority} for r in recommendations],
            model_versions=model_versions,
            assessed_at=datetime.now(timezone.utc).isoformat(),
        )

    # ── plain-language explanation ───────────────────────────────────────────

    @staticmethod
    def _reasons(signals, txn_result) -> list[str]:
        """Unified plain red-flag phrases: message signals + transaction factors."""
        out: list[str] = [s.label for s in signals]
        if txn_result is not None:
            out.extend(f.label for f in txn_result.factors if f.signal == "fraud")
        seen: set[str] = set()
        return [r for r in out if not (r in seen or seen.add(r))][:6]

    @staticmethod
    def _confidence(scam_result, txn_result) -> float:
        confs = []
        if scam_result is not None:
            confs.append(scam_result.confidence)
        if txn_result is not None:
            confs.append(txn_result.confidence)
        return round(max(confs), 4) if confs else 0.0

    @staticmethod
    def _human_explanation(scam_result, txn_result, reasons: list[str]) -> str:
        bits = []
        if scam_result is not None:
            bits.append(f"the message looks {scam_result.label.lower()}")
        if txn_result is not None:
            bits.append(f"the transaction would be {txn_result.decision}d")
        lead = " and ".join(bits) if bits else "no inputs were provided"
        lead = lead[0].upper() + lead[1:]
        if reasons:
            flags = ", ".join(reasons[:3])
            return (f"{lead}. We flagged it because of: {flags}. When unsure, "
                    f"contact your bank on the number printed on your card.")
        return (f"{lead}. Nothing strongly suspicious stood out - stay alert and never "
                f"share your BVN, OTP or PIN with anyone.")

    @staticmethod
    def _risk_explanation(category: str, score: int) -> str:
        if category == "Critical":
            return (f"Critical risk ({score}/100). Acting on this could cost you money "
                    f"or your account access. Do not click, call, or pay - stop now.")
        if category == "High":
            return (f"High risk ({score}/100). Strong signs of fraud. Do not share any "
                    f"details; verify through an official channel first.")
        if category == "Medium":
            return (f"Medium risk ({score}/100). Some warning signs - be careful and "
                    f"double-check before you act.")
        if category == "Low":
            return (f"Low risk ({score}/100). Probably fine, but stay alert and never "
                    f"share your PIN or OTP.")
        return (f"Safe ({score}/100). No strong signs of fraud. Still, never share your "
                f"BVN, OTP or PIN with anyone.")

    # ── component serialisation ──────────────────────────────────────────────

    @staticmethod
    def _scam_component(scam) -> dict[str, Any] | None:
        if scam is None:
            return None
        return {
            "label": scam.label,
            "probability": scam.scam_probability,
            "confidence": scam.confidence,
            "highlighted_words": [{"word": w.word, "weight": w.weight} for w in scam.highlighted_words],
            "explanation": scam.explanation,
        }

    @staticmethod
    def _txn_component(txn) -> dict[str, Any] | None:
        if txn is None:
            return None
        return {
            "decision": txn.decision,
            "probability": txn.fraud_probability,
            "risk_band": txn.risk_band,
            "verdict": txn.verdict,
            "factors": [{"label": f.label, "signal": f.signal, "weight": f.weight}
                        for f in txn.factors],
        }

    @staticmethod
    def _summarize(category: str, score: int, scam, txn, n_actions: int) -> str:
        parts = []
        if scam is not None:
            parts.append(f"the message is {scam.label.lower()}")
        if txn is not None:
            parts.append(f"the transaction would be {txn.decision}d")
        joined = " and ".join(parts) if parts else "no signals were supplied"
        if category in {"High", "Critical"}:
            lead = f"{category} risk ({score}/100)."
            return f"{lead} Our engine finds {joined}. Take the {n_actions} actions below now."
        if category == "Medium":
            return (f"Medium risk ({score}/100). Our engine finds {joined}. "
                    f"Be cautious and follow the recommendations.")
        return (f"{category} ({score}/100). Our engine finds {joined}. "
                f"No urgent action needed, but stay alert.")
