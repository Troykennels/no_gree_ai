"""PII redaction for stored / broadcast fraud messages (NDPR data-minimisation).

Fraud SMS routinely embed sensitive identifiers - BVN, NIN, card PANs, account
numbers, phone numbers, OTP/PIN/CVV. We must never persist or broadcast those in
the clear. The **raw** text is still fed to the model in-memory for scoring; only
the copy that lands in the database, the SSE stream, notifications and the
feedback file is passed through ``redact_pii`` first.

Design: mask long digit runs and secret-keyword contexts, but deliberately leave
Naira amounts (short and/or comma-formatted, e.g. ``NGN25,000``) intact so the UX
still reads naturally.
"""

from __future__ import annotations

import re

# Card PANs: 12-19 contiguous digits -> keep last 4 for reference.
_CARD = re.compile(r"\b\d{12,19}\b")
# BVN / NIN / phone / account numbers: 10-11 contiguous digits -> full mask.
_ID = re.compile(r"\b\d{10,11}\b")
# Secret in context: "OTP is 123456", "PIN: 1234", "CVV 111".
_SECRET_CTX = re.compile(r"\b(OTP|PIN|password|CVV|token)\b(\W{0,4})(\d{3,8})", re.IGNORECASE)


def _mask_card(match: re.Match[str]) -> str:
    digits = match.group(0)
    return f"****{digits[-4:]}"


def redact_pii(text: str | None) -> str:
    """Return ``text`` with PII masked. Safe on None/empty."""
    if not text:
        return text or ""
    t = _SECRET_CTX.sub(lambda m: f"{m.group(1)}{m.group(2) or ' '}****", text)
    t = _CARD.sub(_mask_card, t)
    t = _ID.sub("**********", t)
    return t
