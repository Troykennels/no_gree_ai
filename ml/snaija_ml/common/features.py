"""Interpretable, Nigeria-aware fraud signals.

These engineered features sit alongside a TF-IDF representation of the message.
Because each one maps to a concept a human understands ("asks for your BVN",
"creates false urgency"), the SHAP explanation the API returns is meaningful to
a trader or student, not just to a data scientist.
"""

from __future__ import annotations

import functools
import re
from dataclasses import dataclass

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin

from .text import count_urls, has_phone, normalize


# ─────────────────────────────────────────────────────────────────────────────
# Signal lexicons. Curated from common Nigerian fraud typologies.
# ─────────────────────────────────────────────────────────────────────────────

CREDENTIAL_TERMS = [
    "bvn", "otp", "pin", "atm pin", "card number", "cvv", "expiry",
    "account number", "password", "token", "one time password", "activation code",
    "nin", "date of birth", "mother's maiden", "verify your account",
    "update your details", "confirm your details", "reactivate",
]

URGENCY_TERMS = [
    "urgent", "immediately", "now", "right away", "within 24", "within 2 hours",
    "expire", "expires", "expiring", "blocked", "suspended", "deactivated",
    "restricted", "final notice", "last warning", "act now", "hurry",
]

AUTHORITY_TERMS = [
    "cbn", "central bank", "gtbank", "gtb", "access bank", "first bank",
    "zenith", "uba", "opay", "palmpay", "moniepoint", "kuda", "fcmb",
    "efcc", "npc", "nimc", "interswitch", "nibss", "customer care",
    "bank verification", "security team", "fraud department",
]

REWARD_TERMS = [
    "congratulations", "you have won", "you won", "winner", "prize", "lucky",
    "promo", "promotion", "gift", "reward", "cash prize", "giveaway",
    "lottery", "selected", "claim your", "free airtime", "free data",
]

LOAN_TERMS = [
    "instant loan", "quick loan", "no collateral", "loan approved",
    "pre-approved", "cash loan", "soft loan", "borrow", "credit limit",
    "loan offer", "disbursed", "low interest",
]

INVESTMENT_TERMS = [
    "invest", "investment", "double your", "roi", "returns", "forex",
    "crypto", "bitcoin", "usdt", "trading", "profit daily", "guaranteed profit",
    "ponzi", "mmm", "referral bonus", "sign up bonus", "earn daily",
]

PAYMENT_ACTION_TERMS = [
    "send", "transfer", "pay", "deposit", "activation fee", "processing fee",
    "clearance fee", "delivery fee", "unlock fee", "recharge", "top up",
    "buy voucher", "gift card", "steam card", "itunes",
]


@dataclass(frozen=True)
class FeatureSpec:
    name: str
    description: str        # fraud-framed: what it means when the signal is PRESENT
    safe_description: str   # safe-framed: what it means when the signal is ABSENT


# The order here IS the feature-matrix column order. Do not reorder without retraining.
ENGINEERED_FEATURES: list[FeatureSpec] = [
    FeatureSpec("credential_request", "Asks for BVN, OTP, PIN, card or account details",
                "Does not ask for your BVN, OTP or PIN"),
    FeatureSpec("urgency_pressure", "Creates false urgency (expiry, blocking, 'act now')",
                "No false urgency or pressure"),
    FeatureSpec("authority_impersonation", "Impersonates a bank, the CBN, or an agency",
                "No suspicious authority claims"),
    FeatureSpec("reward_bait", "Promises a prize, winnings, or free reward",
                "No prize or reward bait"),
    FeatureSpec("loan_bait", "Offers an instant / no-collateral loan",
                "No loan bait"),
    FeatureSpec("investment_bait", "Promises guaranteed or doubled investment returns",
                "No investment bait"),
    FeatureSpec("payment_action", "Pushes you to send money, pay a fee, or buy a voucher",
                "No pressure to send money or pay a fee"),
    FeatureSpec("has_link", "Contains a clickable link",
                "No suspicious links"),
    FeatureSpec("link_count", "Contains multiple links",
                "No suspicious links"),
    FeatureSpec("has_phone", "Contains a phone number to call or message",
                "No unknown number to contact"),
    FeatureSpec("shouty_caps", "Heavy use of ALL-CAPS words",
                "Normal capitalisation"),
    FeatureSpec("exclamation_density", "Excessive exclamation marks",
                "Calm, normal tone"),
    FeatureSpec("money_mentioned", "Mentions a naira amount",
                "No money amounts mentioned"),
]

FEATURE_NAMES: list[str] = [f.name for f in ENGINEERED_FEATURES]
FEATURE_DESCRIPTIONS: dict[str, str] = {f.name: f.description for f in ENGINEERED_FEATURES}
FEATURE_SAFE_DESCRIPTIONS: dict[str, str] = {f.name: f.safe_description for f in ENGINEERED_FEATURES}

_MONEY_RE = re.compile(r"(₦|ngn|naira|\bn\d)", re.IGNORECASE)
_CAPS_WORD_RE = re.compile(r"\b[A-Z]{3,}\b")


@functools.lru_cache(maxsize=None)
def _compile_lexicon(terms: tuple[str, ...]) -> re.Pattern:
    # Word-boundary match so "now" does not fire inside "know", "act now" still
    # matches as a phrase, etc. Compiled once per lexicon and cached.
    alt = "|".join(re.escape(t) for t in terms)
    return re.compile(rf"\b(?:{alt})\b", re.IGNORECASE)


def _term_hits(text: str, terms: list[str]) -> int:
    return len(_compile_lexicon(tuple(terms)).findall(text))


def extract_features(raw: str) -> dict[str, float]:
    """Return the engineered feature dict for a single raw message."""
    norm = normalize(raw)
    words = norm.split()
    n_words = max(len(words), 1)

    caps_words = len(_CAPS_WORD_RE.findall(raw))
    exclamations = raw.count("!")

    return {
        "credential_request": float(_term_hits(norm, CREDENTIAL_TERMS)),
        "urgency_pressure": float(_term_hits(norm, URGENCY_TERMS)),
        "authority_impersonation": float(_term_hits(norm, AUTHORITY_TERMS)),
        "reward_bait": float(_term_hits(norm, REWARD_TERMS)),
        "loan_bait": float(_term_hits(norm, LOAN_TERMS)),
        "investment_bait": float(_term_hits(norm, INVESTMENT_TERMS)),
        "payment_action": float(_term_hits(norm, PAYMENT_ACTION_TERMS)),
        "has_link": 1.0 if count_urls(raw) else 0.0,
        "link_count": float(count_urls(raw)),
        "has_phone": 1.0 if has_phone(raw) else 0.0,
        "shouty_caps": float(caps_words) / n_words,
        "exclamation_density": float(exclamations) / n_words,
        "money_mentioned": 1.0 if _MONEY_RE.search(raw) else 0.0,
    }


class EngineeredFeatureExtractor(BaseEstimator, TransformerMixin):
    """sklearn transformer: list[str] messages -> dense engineered feature matrix.

    Stateless (no fitting needed), so it is safe across train/serve boundaries.
    """

    def fit(self, X, y=None):  # noqa: N803 - sklearn API
        return self

    def transform(self, X):  # noqa: N803 - sklearn API
        rows = [extract_features(str(x)) for x in X]
        return np.array([[r[name] for name in FEATURE_NAMES] for r in rows], dtype=np.float64)

    def get_feature_names_out(self, input_features=None):
        return np.array(FEATURE_NAMES, dtype=object)
