"""Continuous learning — persist user feedback so the model improves over time.

When a user marks a scanned message as **Safe** or **Scam**, we append a labelled
row to a durable CSV. The scam-detection trainer reads this file as an additional
data source (see ``snaija_ml.data.training_data``), so the next training run learns
from real corrections — the human-in-the-loop feedback flywheel.

The file is append-only and newline-safe; concurrent writes are serialised with a
lock. In production point ``FEEDBACK_DIR`` at a mounted volume so feedback
survives redeploys and can be pulled into the training pipeline.
"""

from __future__ import annotations

import csv
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

_HEADER = ["timestamp", "text", "label", "source", "predicted_label", "item_id"]


def _default_feedback_dir() -> Path:
    env = os.getenv("FEEDBACK_DIR")
    if env:
        return Path(env)
    try:
        # ML_ROOT/data/processed -> ML_ROOT/data/feedback (works for editable installs)
        from snaija_ml.data import training_data

        return training_data.PROCESSED.parent / "feedback"
    except Exception:  # noqa: BLE001
        return Path("data") / "feedback"


class FeedbackStore:
    def __init__(self, feedback_dir: str | Path | None = None) -> None:
        self._dir = Path(feedback_dir) if feedback_dir else _default_feedback_dir()
        self._path = self._dir / "feedback.csv"
        self._lock = threading.Lock()
        self._count = 0
        self._ensure_file()

    def _ensure_file(self) -> None:
        try:
            self._dir.mkdir(parents=True, exist_ok=True)
            if not self._path.exists():
                with self._path.open("w", newline="", encoding="utf-8") as fh:
                    csv.writer(fh).writerow(_HEADER)
            else:
                # Count existing rows (minus header) for the dashboard counter.
                with self._path.open("r", encoding="utf-8") as fh:
                    self._count = max(sum(1 for _ in fh) - 1, 0)
        except Exception:  # noqa: BLE001 - never let telemetry setup break the API
            pass

    @property
    def path(self) -> Path:
        return self._path

    @property
    def count(self) -> int:
        return self._count

    def record(self, *, text: str, label: str, predicted_label: str | None = None,
               item_id: str | None = None) -> bool:
        """Append one labelled feedback row. ``label`` is 'Safe' or 'Scam'.

        Stored numerically for training (Scam=1, Safe=0) via the trainer's reader;
        here we keep the human label plus the model's original prediction so the
        correction is auditable.
        """
        norm = label.strip().capitalize()
        if norm not in {"Safe", "Scam"}:
            return False
        row = [
            datetime.now(timezone.utc).isoformat(),
            (text or "").replace("\r", " ").replace("\n", " ").strip(),
            norm,
            "user_feedback",
            predicted_label or "",
            item_id or "",
        ]
        with self._lock:
            try:
                with self._path.open("a", newline="", encoding="utf-8") as fh:
                    csv.writer(fh).writerow(row)
                self._count += 1
                return True
            except Exception:  # noqa: BLE001
                return False
