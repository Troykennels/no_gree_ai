"""Download the external datasets.

  1. SMS Spam Collection (UCI)  -> public, small, fetched directly (with mirrors).
  2. IEEE-CIS Fraud Detection   -> Kaggle competition; requires the Kaggle API and
                                   accepted competition rules. Downloaded when
                                   credentials are present, otherwise skipped with
                                   clear instructions.

Nothing here is fatal: if a source is unreachable the pipeline continues with
whatever datasets are available.
"""

from __future__ import annotations

import io
import subprocess
import zipfile
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"

# SMS Spam Collection — several mirrors, tried in order.
SMS_SPAM_SOURCES = [
    ("tsv", "https://raw.githubusercontent.com/justmarkham/pycon-2016-tutorial/master/data/sms.tsv"),
    ("zip", "https://archive.ics.uci.edu/ml/machine-learning-databases/00228/smsspamcollection.zip"),
    ("zip", "https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip"),
]


def _http_get(url: str, timeout: int = 30) -> bytes:
    import requests

    resp = requests.get(url, timeout=timeout, headers={"User-Agent": "SecureNaija/1.0"})
    resp.raise_for_status()
    return resp.content


def download_sms_spam() -> Path | None:
    """Fetch the SMS Spam Collection and normalise to a 2-column TSV: label<TAB>text."""
    out_dir = RAW_DIR / "sms_spam"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "SMSSpamCollection.tsv"
    if out_file.exists() and out_file.stat().st_size > 0:
        print(f"[sms_spam] already present -> {out_file}")
        return out_file

    for kind, url in SMS_SPAM_SOURCES:
        try:
            print(f"[sms_spam] trying {url}")
            data = _http_get(url)
            if kind == "zip":
                with zipfile.ZipFile(io.BytesIO(data)) as zf:
                    name = next(n for n in zf.namelist() if "SMSSpamCollection" in n)
                    raw = zf.read(name).decode("latin-1")
            else:
                raw = data.decode("utf-8", errors="replace")
            # Normalise: each line "label\ttext".
            lines = [ln for ln in raw.splitlines() if "\t" in ln]
            out_file.write_text("\n".join(lines), encoding="utf-8")
            print(f"[sms_spam] saved {len(lines)} rows -> {out_file}")
            return out_file
        except Exception as exc:  # noqa: BLE001 - best-effort across mirrors
            print(f"[sms_spam] source failed: {exc}")
    print("[sms_spam] all sources failed; skipping.")
    return None


def download_ieee_cis() -> Path | None:
    """Download IEEE-CIS via the Kaggle API when available.

    Requires: `pip install kaggle`, a ~/.kaggle/kaggle.json token, and having
    accepted the competition rules at
    https://www.kaggle.com/c/ieee-fraud-detection/rules
    """
    out_dir = RAW_DIR / "ieee_cis"
    out_dir.mkdir(parents=True, exist_ok=True)
    if (out_dir / "train_transaction.csv").exists():
        print(f"[ieee_cis] already present -> {out_dir}")
        return out_dir

    # Preferred path: kagglehub (cleaner API). Still needs Kaggle credentials
    # (kaggle.json or KAGGLE_USERNAME/KAGGLE_KEY) and accepted competition rules.
    try:
        import kagglehub  # type: ignore

        print("[ieee_cis] trying kagglehub.competition_download...")
        cached = kagglehub.competition_download("ieee-fraud-detection")
        print(f"[ieee_cis] kagglehub cached files at: {cached}")
        for csv in Path(cached).glob("*.csv"):
            target = out_dir / csv.name
            if not target.exists():
                target.write_bytes(csv.read_bytes())
        return out_dir
    except Exception as exc:  # noqa: BLE001 - fall through to kaggle CLI / instructions
        print(f"[ieee_cis] kagglehub unavailable or unauthenticated: {exc}")

    kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
    if not kaggle_json.exists():
        print(
            "[ieee_cis] Kaggle credentials not found.\n"
            "  To fetch this dataset:\n"
            "    1) pip install kaggle\n"
            "    2) create an API token at kaggle.com/settings -> Account -> Create New Token\n"
            "    3) save it to ~/.kaggle/kaggle.json\n"
            "    4) accept rules at kaggle.com/c/ieee-fraud-detection/rules\n"
            "    5) re-run: python -m snaija_ml.data.download\n"
            "  Skipping for now."
        )
        return None

    try:
        print("[ieee_cis] downloading via Kaggle API (large, ~600MB)...")
        subprocess.run(
            ["kaggle", "competitions", "download", "-c", "ieee-fraud-detection",
             "-p", str(out_dir)],
            check=True,
        )
        for zp in out_dir.glob("*.zip"):
            with zipfile.ZipFile(zp) as zf:
                zf.extractall(out_dir)
            zp.unlink()
        print(f"[ieee_cis] done -> {out_dir}")
        return out_dir
    except Exception as exc:  # noqa: BLE001
        print(f"[ieee_cis] download failed: {exc}. Skipping.")
        return None


def download_all() -> dict[str, Path | None]:
    return {
        "sms_spam": download_sms_spam(),
        "ieee_cis": download_ieee_cis(),
    }


if __name__ == "__main__":
    download_all()
