"""Legit Nigerian bank-alert templates (hard negatives) for the scam model.

The scam detector was over-flagging genuine transaction alerts ("Transfer of
NGN15,000 to CHIDI OKAFOR successful") as Suspicious, because legit alert
vocabulary (credit/debit alert, transfer, salary, POS, balance) was
under-represented among the negatives. These generated, label-0 examples teach
the model that a plain bank alert is normal. Generated in code so retraining is
reproducible (no static data file).
"""

from __future__ import annotations

import random

_BANKS = ["GTBank", "UBA", "Access Bank", "Zenith Bank", "FirstBank", "Fidelity",
          "Union Bank", "Sterling", "Kuda", "PalmPay", "Moniepoint", "OPay"]
_FIRST = ["Chidi", "Ada", "Emeka", "Ngozi", "Tunde", "Bola", "Yusuf", "Aisha", "Ifeoma",
          "Musa", "Kemi", "Segun", "Chioma", "Uche", "Fatima", "Ibrahim", "Blessing", "Femi"]
_LAST = ["Okafor", "Adeyemi", "Okonkwo", "Bello", "Eze", "Balogun", "Abubakar", "Nwosu",
         "Adebayo", "Ogunleye", "Chukwu", "Danjuma", "Okoro", "Mohammed", "Afolabi"]
_COMPANIES = ["ORION LTD", "DANGOTE PLC", "MTN NIGERIA", "GTCO", "ANDELA", "PAYSTACK",
              "FLUTTERWAVE", "SHELL NG", "ZENITH TECH", "FIRST HOLDINGS"]
_MERCHANTS = ["SHOPRITE", "CHICKEN REPUBLIC", "SPAR", "JUMIA", "KONGA", "FILLING STATION",
              "STARTIMES", "DSTV", "MARKET SQUARE", "MEDPLUS PHARMACY"]
_CITIES = ["IKEJA", "LEKKI", "ABUJA", "IBADAN", "KANO", "PORT HARCOURT", "BENIN", "ENUGU"]
_MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
_BILLS = ["EKEDC ELECTRICITY", "DSTV SUBSCRIPTION", "MTN DATA", "GOTV", "IKEDC PREPAID",
          "WATER BILL", "SCHOOL FEES", "AIRTEL DATA"]


def _amt(rng: random.Random, lo: int, hi: int) -> str:
    return f"{rng.randint(lo, hi):,}"


def legit_bank_alerts(n: int = 300, seed: int = 20260722) -> list[str]:
    """Return ``n`` varied, realistic legit Nigerian bank-alert messages."""
    rng = random.Random(seed)
    out: list[str] = []
    for _ in range(n):
        bank = rng.choice(_BANKS)
        acct = rng.randint(1000, 9999)
        bal = _amt(rng, 5_000, 900_000)
        name = f"{rng.choice(_FIRST)} {rng.choice(_LAST)}".upper()
        kind = rng.randint(0, 6)
        if kind == 0:  # salary credit
            out.append(f"{bank}: Credit Alert. Acct **{acct}. Amt:NGN{_amt(rng, 60_000, 900_000)}.00. "
                       f"Desc:{rng.choice(_MONTHS)} SALARY {rng.choice(_COMPANIES)}. Bal:NGN{bal}.")
        elif kind == 1:  # transfer received
            out.append(f"{bank}: NGN{_amt(rng, 1_000, 250_000)} received from {name}. Bal:NGN{bal}.")
        elif kind == 2:  # POS debit
            out.append(f"{bank}: Debit Alert. Acct **{acct}. Amt:NGN{_amt(rng, 500, 90_000)}. "
                       f"Desc:POS {rng.choice(_MERCHANTS)} {rng.choice(_CITIES)}. Bal:NGN{bal}.")
        elif kind == 3:  # transfer sent
            out.append(f"{bank}: Transfer of NGN{_amt(rng, 1_000, 300_000)} to {name} successful. "
                       f"Bal:NGN{bal}. Thank you for banking with us.")
        elif kind == 4:  # airtime
            out.append(f"{bank}: Your airtime purchase of NGN{_amt(rng, 100, 10_000)} was successful. "
                       f"Bal:NGN{bal}.")
        elif kind == 5:  # bill payment
            out.append(f"{bank}: Payment of NGN{_amt(rng, 1_000, 60_000)} for {rng.choice(_BILLS)} "
                       f"was successful. Bal:NGN{bal}.")
        else:  # fintech transfer
            out.append(f"{rng.choice(['OPay', 'PalmPay', 'Moniepoint', 'Kuda'])}: You received "
                       f"NGN{_amt(rng, 500, 150_000)} from {name}. Bal:NGN{bal}.")
    return out
