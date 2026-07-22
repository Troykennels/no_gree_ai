"""AI recommendation engine — turns fused fraud signals into clear actions.

Given what the two models found (a scam verdict and/or a transaction verdict) plus
a light scan of the message text, this produces a *prioritised, de-duplicated* list
of concrete steps a Nigerian user should take right now — "Do not click the link",
"Freeze your card", "Contact your bank", "Change your PIN", "Enable 2FA", etc.

It is deterministic and explainable (rules over detected signals), so every
recommendation can be traced to why it fired — the right property for advice about
someone's money.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Priority order (most urgent first) used to sort and cap the final list.
PRIORITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


@dataclass
class Signal:
    type: str
    label: str
    severity: str  # critical | high | medium | low | info


@dataclass
class Recommendation:
    id: str
    action: str
    detail: str
    priority: str  # critical | high | medium | low | info


# ── keyword scanners (light, lowercased) ─────────────────────────────────────
_CREDENTIAL = re.compile(r"\b(bvn|otp|pin|password|cvv|card\s*number|atm|token|nin)\b", re.I)
_LINK = re.compile(r"(https?://|www\.|bit\.ly|tinyurl|cutt\.ly|\.top\b|\.xyz\b|\.click\b|/login|/verify)", re.I)
_PHONE = re.compile(r"(\bcall\b|\+?234\d{6,}|\b0[789]\d{9}\b)", re.I)
_BAIT = re.compile(r"\b(loan|prize|won|winner|congratulations|reward|palliative|grant|promo|bonus)\b", re.I)
_URGENCY = re.compile(r"\b(now|immediately|urgent|blocked?|expire[sd]?|deactivat|suspend|within\s+\d+\s*(min|hour))\b", re.I)


def detect_signals(message: str | None, scam, transaction) -> list[Signal]:
    """Extract the notable risk signals from the model outputs + message text."""
    signals: list[Signal] = []
    text = message or ""

    if scam is not None:
        if scam.label == "Scam":
            signals.append(Signal("scam_message", "Message reads like a scam", "critical"))
        elif scam.label == "Suspicious":
            signals.append(Signal("suspicious_message", "Message looks suspicious", "high"))
        # Word-level cues from the model's highlighted words.
        joined = " ".join(w.word.lower() for w in getattr(scam, "highlighted_words", []))
        if "link" in joined or _LINK.search(text):
            signals.append(Signal("malicious_link", "Suspicious link", "critical"))
        if "phone" in joined or "number to call" in joined or _PHONE.search(text):
            signals.append(Signal("callback_number", "Asks you to call a number", "high"))

    if _CREDENTIAL.search(text):
        signals.append(Signal("credential_request", "Requests your BVN, OTP or PIN", "critical"))
    if _BAIT.search(text):
        signals.append(Signal("financial_bait", "Fake prize or loan offer", "medium"))
    if _URGENCY.search(text):
        signals.append(Signal("urgency", "Urgent phishing words", "medium"))

    if transaction is not None:
        if transaction.decision == "decline":
            signals.append(Signal("transaction_decline", "Transaction flagged as fraud", "critical"))
        elif transaction.decision == "review":
            signals.append(Signal("transaction_review", "Transaction needs a second look", "high"))
        # "Large transaction" is surfaced from the model's own SHAP reasons
        # ("Large or unusual amount") rather than a hardcoded threshold here.

    return signals


def _rec(rid, action, detail, priority) -> Recommendation:
    return Recommendation(id=rid, action=action, detail=detail, priority=priority)


def recommend(signals: list[Signal], *, category: str,
              has_message: bool, has_transaction: bool) -> list[Recommendation]:
    """Map detected signals to concrete, prioritised actions (de-duplicated)."""
    types = {s.type for s in signals}
    out: list[Recommendation] = []

    if "malicious_link" in types:
        out.append(_rec("no_click", "Do not click the link",
                        "The message contains a link built to steal your details or install malware.",
                        "critical"))
    if "credential_request" in types:
        out.append(_rec("never_share", "Never share your BVN, OTP, PIN or password",
                        "No real bank or agency will ever ask for these. Sharing them hands over your account.",
                        "critical"))
        out.append(_rec("change_pin", "Change your PIN and password",
                        "If you already entered or sent them, change your card PIN and internet-banking password now.",
                        "high"))
    if "callback_number" in types:
        out.append(_rec("no_call", "Do not call the number in the message",
                        "Call your bank only on the number printed on your card or its official website.",
                        "high"))

    if "transaction_decline" in types:
        out.append(_rec("freeze_card", "Freeze your card immediately",
                        "Block the card in your banking app or dial your bank's USSD block code to stop further charges.",
                        "critical"))
        out.append(_rec("contact_bank", "Contact your bank",
                        "Report the suspicious transaction and ask them to secure your account.",
                        "critical"))
        out.append(_rec("dispute_txn", "Dispute the transaction",
                        "Formally dispute the charge so the bank can investigate and reverse it if fraudulent.",
                        "high"))
    elif "transaction_review" in types:
        out.append(_rec("verify_txn", "Verify this transaction before approving",
                        "Use a step-up check (OTP or a call-back to the cardholder) before letting it through.",
                        "high"))

    if "financial_bait" in types:
        out.append(_rec("ignore_bait", "Ignore 'you have won' and 'pre-approved loan' offers",
                        "Unsolicited prizes, bonuses and instant loans that ask for a fee or your details are scams.",
                        "medium"))
    if "urgency" in types:
        out.append(_rec("slow_down", "Slow down - urgency is a scam tactic",
                        "Pressure to act 'now' is a red flag. Verify through an official channel before doing anything.",
                        "medium"))

    # Cross-cutting hardening for anything genuinely risky.
    if category in {"High", "Critical"}:
        out.append(_rec("enable_2fa", "Enable Two-Factor Authentication (2FA)",
                        "Turn on 2FA / transaction PIN on your bank and email so a stolen password alone can't get in.",
                        "high"))
        out.append(_rec("report", "Report it",
                        "Report to your bank, and forward scam SMS to your telco and the NFIU so others are protected.",
                        "medium"))

    if not out:
        # Safe / low-risk: reassurance + baseline hygiene.
        out.append(_rec("stay_alert", "Looks safe - but stay alert",
                        "Nothing strongly fraudulent was detected. Still, never share your BVN, OTP or PIN with anyone.",
                        "info"))
        if has_transaction:
            out.append(_rec("monitor", "Keep an eye on your statement",
                            "Check your transaction alerts regularly and report anything you don't recognise.",
                            "low"))

    # De-duplicate by id, then sort by priority.
    seen: set[str] = set()
    unique = [r for r in out if not (r.id in seen or seen.add(r.id))]
    unique.sort(key=lambda r: PRIORITY_RANK.get(r.priority, 5))
    return unique[:7]
