"""Text normalization shared by training and serving.

Keeping this in one place guarantees the model sees identically-processed
text at train time and inference time (no train/serve skew).
"""

from __future__ import annotations

import re
import unicodedata

_URL_RE = re.compile(
    r"(https?://\S+|www\.\S+|\b\S+\.(?:com|net|org|ng|xyz|info|top|link|click)\b|"
    r"\b(?:bit\.ly|tinyurl\.com|wa\.me|t\.me|cutt\.ly|rb\.gy)/\S*)",
    re.IGNORECASE,
)
_PHONE_RE = re.compile(r"(?:\+?234|0)\d{9,10}\b")
_WHITESPACE_RE = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Lower-case, strip accents, collapse whitespace. Non-destructive to meaning."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip()


def redact_for_model(text: str) -> str:
    """Replace volatile tokens (URLs, phone numbers, long digit runs) with
    stable placeholders so the model learns patterns, not memorized strings.
    """
    text = _URL_RE.sub(" _url_ ", text)
    text = _PHONE_RE.sub(" _phone_ ", text)
    text = re.sub(r"\b\d{6,}\b", " _longnum_ ", text)
    text = re.sub(r"\b\d{9,}\b", " _acctnum_ ", text)
    return _WHITESPACE_RE.sub(" ", text).strip()


def preprocess_for_tfidf(text: str) -> str:
    """Preprocessor passed to TfidfVectorizer. Must stay importable (top-level)
    so the pickled model can be unpickled at serving time.
    """
    return redact_for_model(normalize(text))


def has_url(text: str) -> bool:
    return bool(_URL_RE.search(text))


def count_urls(text: str) -> int:
    return len(_URL_RE.findall(text))


def has_phone(text: str) -> bool:
    return bool(_PHONE_RE.search(text))
