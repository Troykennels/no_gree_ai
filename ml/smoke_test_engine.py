"""End-to-end smoke test of the whole SecureNaija AI Engine.

Loads and exercises every trained model and prints a concise pass/fail so a
reviewer can verify the engine in one command:

    python smoke_test_engine.py
"""

from __future__ import annotations

import sys


def test_scam() -> bool:
    from snaija_ml.serving.scam_predictor import get_scam_detector

    d = get_scam_detector()
    print(f"\n== Model 1: Scam Detection (v{d.version}) ==")
    cases = [
        ("Scam", "Your GTBank account will be BLOCKED. Update your BVN via "
                 "http://gtb-verify.top now to avoid deactivation."),
        ("Safe", "Access Bank: Credit Alert. Acct **4821. Amt:NGN25,000. Bal:NGN61,300."),
        ("Safe", "Hey Ada, are we still meeting at 4pm today?"),
    ]
    ok = True
    for expect, text in cases:
        p = d.predict(text)
        good = (expect == "Scam" and p.label == "Scam") or (expect == "Safe" and p.label != "Scam")
        ok = ok and good
        flag = "OK " if good else "XX "
        words = ", ".join(w.word for w in p.highlighted_words[:3])
        print(f"  {flag}[{p.label:10}] {p.scam_probability:5.1%}  {text[:44]}...  ({words})")
    return ok


def test_transaction() -> bool:
    from snaija_ml.serving.transaction_predictor import get_transaction_predictor

    p = get_transaction_predictor()
    print(f"\n== Model 2: Transaction Fraud (v{p.version}, {p.algorithm}) ==")
    cases = [
        ("low-ish", {"TransactionAmt": 25.0, "ProductCD": "W", "card4": "visa",
                     "card6": "debit", "P_emaildomain": "gmail.com"}),
        ("higher", {"TransactionAmt": 1899.0, "ProductCD": "C", "card4": "mastercard",
                    "card6": "credit", "P_emaildomain": "protonmail.com", "C1": 48, "C13": 62}),
        ("empty", {}),
    ]
    ok = True
    for name, feats in cases:
        r = p.predict(feats)
        good = 0.0 <= r.fraud_probability <= 1.0 and r.decision in {"approve", "review", "decline"}
        ok = ok and good
        top = r.factors[0].label if r.factors else "-"
        print(f"  {'OK ' if good else 'XX '}[{r.decision:7}] {r.fraud_probability:5.1%}  "
              f"band={r.risk_band:8}  {name:7}  top: {top}")
    return ok


def main() -> None:
    results = {}
    try:
        results["scam"] = test_scam()
    except Exception as exc:  # noqa: BLE001
        print(f"  Model 1 FAILED to load/predict: {exc}")
        results["scam"] = False
    try:
        results["transaction"] = test_transaction()
    except Exception as exc:  # noqa: BLE001
        print(f"  Model 2 FAILED to load/predict: {exc}")
        results["transaction"] = False

    print("\n" + "-" * 48)
    for k, v in results.items():
        print(f"  {k:12} {'PASS' if v else 'FAIL'}")
    sys.exit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    main()
