"""Quick end-to-end smoke test of the trained predictor.

Run after training:  python smoke_test.py
"""

from snaija_ml.serving.predictor import get_predictor

CASES = [
    # Borderline / ambiguous — should score in the middle, not 0 or 100.
    "Your BVN update is due this month. Please visit any branch with a valid ID.",
    "Hi, please send me 5k, I go pay you back tomorrow. Thanks.",
    "Reminder: your subscription expires soon. Renew to keep your account active.",
    "Dear Customer, your GTBank account will be BLOCKED today. Update your BVN "
    "now via http://gtb-verify.top/login to avoid deactivation.",
    "CONGRATULATIONS! You are pre-approved for an instant loan of N150,000, NO "
    "collateral. Pay a small processing fee to unlock. Apply: bit.ly/loan-ng",
    "Access Bank: Credit Alert. Acct **4821. Amt:NGN25,000. Desc:Transfer from "
    "Chidi. Bal:NGN61,300.",
    "Hey Ada, are we still meeting at 4pm today? Let me know.",
]


def main() -> None:
    predictor = get_predictor()
    print(f"Model version: {predictor.version}\n")
    for text in CASES:
        p = predictor.predict(text)
        print(f"[{p.risk_band.upper():8}] {p.fraud_probability:5.1%}  {text[:60]}...")
        for c in p.contributions[:3]:
            arrow = "^" if c.signal == "fraud" else "v"
            print(f"            {arrow} {c.label} ({c.weight:.3f})")
        print()


if __name__ == "__main__":
    main()
