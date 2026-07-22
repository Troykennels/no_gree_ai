"""Admin endpoints — dataset intelligence.

Serves the preprocessing report produced by
`python -m snaija_ml.data.preprocess`. The web admin page can consume this
endpoint, or read the statically-mirrored copy under the web app's /public.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.domain.entities import User
from app.interface.dependencies import get_current_user

router = APIRouter(tags=["admin"], prefix="/admin")


def _report_path() -> Path:
    try:
        import snaija_ml

        return Path(snaija_ml.__file__).resolve().parents[1] / "data" / "reports" / "dataset_report.json"
    except Exception:  # noqa: BLE001 - package not importable
        return Path("ml/data/reports/dataset_report.json")


@router.get("/dataset-report")
def dataset_report(_: Annotated[User, Depends(get_current_user)]) -> dict:
    path = _report_path()
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="Dataset report not generated yet. Run "
                   "`python -m snaija_ml.data.preprocess`.",
        )
    return json.loads(path.read_text(encoding="utf-8"))
