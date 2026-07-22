"""Synthetic Nigerian message dataset.

Real fraud SMS/WhatsApp corpora are sensitive and hard to share, so we generate
a labelled dataset from templates grounded in actual Nigerian fraud typologies.

Design goals that make the model *honest* rather than trivially perfect:

  • High slot variety (banks, amounts, links, phrasings, greetings, light typos)
    so deduplication doesn't collapse the set and the model can't memorize strings.
  • **Hard negatives** — genuine messages that contain scary keywords ("OTP",
    "BVN", "expire", a link, a naira amount): real bank reminders, real OTPs that
    say *do not share*, real telco promos, real delivery links.
  • **Hard positives** — subtle scams with *no* link that just ask you to call a
    number and read out a code.

The overlap between classes forces the model to learn intent, producing a
realistic probability spread (not a degenerate 0/1 split) and a sensible
decision threshold.

Deterministic given a seed. Swap for a real labelled corpus when available — the
training and serving code do not change.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

import pandas as pd

LABEL_FRAUD = 1
LABEL_LEGIT = 0

_BANKS = ["GTBank", "GTB", "Access Bank", "First Bank", "Zenith Bank", "UBA",
          "FCMB", "Union Bank", "Fidelity", "Sterling", "Wema", "Polaris"]
_FINTECHS = ["OPay", "PalmPay", "Moniepoint", "Kuda", "Carbon", "PiggyVest", "Cowrywise"]
_TELCOS = ["MTN", "Airtel", "Glo", "9mobile"]
_NAMES = ["Chidi", "Aisha", "Emeka", "Ngozi", "Tunde", "Bola", "Ifeoma", "Musa",
          "Yusuf", "Amaka", "Segun", "Fatima", "Chinedu", "Blessing", "Ada"]
_GREETINGS = ["Dear Customer", "Dear Valued Customer", "Hello", "Hi", "Attention",
              "Dear Account Holder", ""]
_SCAM_LINKS = ["http://gtb-verify.top/login", "bit.ly/acct-reactivate",
               "www.cbn-secure.click", "http://opay-bonus.xyz", "tinyurl.com/loan-ng",
               "http://firstbank-update.info", "cutt.ly/bvn-verify", "rb.gy/win-now",
               "http://verify-ng.link/secure", "wa.me/2348012345678"]
_REAL_LINKS = ["https://gtbank.com", "https://www.jumia.com.ng/track",
               "https://opay.com", "https://kuda.com/app", "https://mtn.ng/promo"]
_PHONES = ["08012345678", "07098765432", "+2349011223344", "08155667788",
           "09033445566", "08167788990"]


def _amt(r: random.Random) -> str:
    n = r.choice([2300, 5000, 12500, 25000, 50000, 75000, 150000, 500000, 1000000])
    return f"{n:,}"


def _acct(r: random.Random) -> int:
    return r.randint(1000, 9999)


def _maybe_typo(r: random.Random, s: str) -> str:
    """Occasionally add light noise humans and scammers both produce."""
    roll = r.random()
    if roll < 0.15:
        return s.upper()
    if roll < 0.25:
        return s.replace("your", "ur").replace("you", "u")
    if roll < 0.30:
        return s + " " + r.choice(["Thank you.", "Regards.", "God bless.", ""])
    return s


# =============================================================================
# FRAUD generators
# =============================================================================

def _bvn_phishing(r: random.Random) -> str:
    return (
        f"{r.choice(_GREETINGS)}, your {r.choice(_BANKS)} account will be "
        f"{r.choice(['BLOCKED', 'suspended', 'deactivated', 'restricted'])} "
        f"{r.choice(['today', 'in 24 hours', 'immediately'])}. "
        f"{r.choice(['Update', 'Verify', 'Confirm'])} your "
        f"{r.choice(['BVN', 'BVN and ATM PIN', 'account details'])} now via "
        f"{r.choice(_SCAM_LINKS)} to avoid closure."
    )


def _fake_bank_alert(r: random.Random) -> str:
    return (
        f"{r.choice(_BANKS)}: A transfer of N{_amt(r)} is "
        f"{r.choice(['pending', 'on hold', 'awaiting approval'])} on your account. "
        f"To {r.choice(['cancel', 'reverse', 'stop'])} it, call {r.choice(_PHONES)} "
        f"and provide your {r.choice(['OTP', 'card PIN', 'account details'])} for verification."
    )


def _otp_social_engineering(r: random.Random) -> str:
    return (
        f"This is {r.choice(_FINTECHS + _BANKS)} "
        f"{r.choice(['customer care', 'fraud team', 'security desk'])}. "
        f"To {r.choice(['resolve your failed transaction', 'secure your account', 'reverse the debit'])}, "
        f"kindly {r.choice(['read out', 'confirm', 'send'])} the "
        f"{r.choice(['6-digit OTP', 'one time password', 'code'])} sent to your phone now."
    )


def _loan_scam(r: random.Random) -> str:
    return (
        f"{r.choice(['CONGRATULATIONS', 'Good news', 'Approved'])}! You are "
        f"{r.choice(['pre-approved', 'qualified', 'selected'])} for an instant loan of "
        f"N{_amt(r)}, NO collateral. Pay a small "
        f"{r.choice(['processing', 'activation', 'clearance'])} fee to unlock. "
        f"Apply: {r.choice(_SCAM_LINKS)}"
    )


def _investment_scam(r: random.Random) -> str:
    return (
        f"{r.choice(['Double your money', 'Earn N20,000 daily', '100% ROI guaranteed'])} "
        f"in {r.choice(['48 hours', '3 days', 'one week'])}! "
        f"{r.choice(['Crypto', 'Forex', 'USDT'])} trading with guaranteed profit. "
        f"Invest N{_amt(r)}, sign-up bonus for the first 100 people. "
        f"Join now {r.choice(_SCAM_LINKS)}"
    )


def _prize_bait(r: random.Random) -> str:
    return (
        f"CONGRATULATIONS!!! Your line has WON N{_amt(r)} in the {r.choice(_TELCOS)} "
        f"{r.choice(['promo', 'anniversary draw', 'loyalty reward'])}. To claim, call "
        f"{r.choice(_PHONES)} and buy a recharge card of N{_amt(r)} for processing."
    )


def _pos_scam(r: random.Random) -> str:
    return (
        f"POS DEBIT of N{_amt(r)} FAILED but was deducted. Call the merchant helpline "
        f"{r.choice(_PHONES)} now and share your "
        f"{r.choice(['card number and PIN', 'CVV', 'account and OTP'])} to get an instant refund."
    )


def _subtle_scam_no_link(r: random.Random) -> str:
    """HARD positive: no link, no obvious bait — pure social engineering."""
    return r.choice([
        f"Hello {r.choice(_NAMES)}, it's your {r.choice(['pastor', 'oga', 'landlord', 'uncle'])}. "
        f"I'm stuck and can't talk now. Please help me buy a recharge card of N{_amt(r)} "
        f"and send the code here, I'll refund you tomorrow.",
        f"Good day, we are calling from {r.choice(_BANKS)}. For your security we need to "
        f"confirm the {r.choice(['OTP', 'code'])} you just received. Please read it to me now.",
        f"Your account has been flagged. Kindly call {r.choice(_PHONES)} and confirm your "
        f"date of birth and mother's maiden name to lift the restriction.",
    ])


_FRAUD_GENERATORS = [
    _bvn_phishing, _fake_bank_alert, _otp_social_engineering, _loan_scam,
    _investment_scam, _prize_bait, _pos_scam, _subtle_scam_no_link,
]


# =============================================================================
# LEGIT generators (including HARD negatives with scary keywords)
# =============================================================================

def _real_credit_alert(r: random.Random) -> str:
    return (
        f"{r.choice(_BANKS)}: Credit Alert. Acct **{_acct(r)}. Amt:NGN{_amt(r)}. "
        f"Desc:Transfer from {r.choice(_NAMES)}. Bal:NGN{_amt(r)}."
    )


def _real_debit_alert(r: random.Random) -> str:
    return (
        f"{r.choice(_BANKS)}: Debit Alert. Acct **{_acct(r)}. Amt:NGN{_amt(r)}. "
        f"Desc:{r.choice(['POS purchase', 'Airtime', 'Transfer', 'Web payment'])}. "
        f"Avail Bal:NGN{_amt(r)}."
    )


def _real_otp(r: random.Random) -> str:
    """HARD negative: contains 'OTP'/'one-time password' but is genuine."""
    return (
        f"{r.randint(100000, 999999)} is your {r.choice(_FINTECHS + _BANKS)} one-time "
        f"password (OTP). Do NOT share it with anyone, including our staff. "
        f"It expires in {r.choice([5, 10, 15])} minutes."
    )


def _real_bank_security_notice(r: random.Random) -> str:
    """HARD negative: mentions BVN/PIN/OTP and urgency but warns you, no link."""
    return r.choice([
        f"{r.choice(_BANKS)} will NEVER ask for your BVN, PIN, OTP or password. "
        f"Never share them. Report suspicious messages to our official customer care.",
        f"{r.choice(_BANKS)} Security: if you did NOT perform the last transaction, "
        f"please visit your nearest branch or call the number on the back of your card.",
    ])


def _real_telco_promo(r: random.Random) -> str:
    """HARD negative: promo + naira amount + a real short code, but genuine."""
    return (
        f"{r.choice(_TELCOS)}: Get {r.choice(['1.5GB', '3GB', '6GB'])} for "
        f"N{r.choice(['500', '1,000', '1,500'])}. Dial "
        f"*{r.randint(100, 999)}# to activate. Valid for 30 days. T&Cs apply."
    )


def _real_delivery(r: random.Random) -> str:
    """HARD negative: contains a (legit) link."""
    return r.choice([
        f"Hi {r.choice(_NAMES)}, your Jumia order #{r.randint(100000, 999999)} is out for "
        f"delivery today. Track it at {r.choice(_REAL_LINKS)}. The rider will call you.",
        f"Your GIG Logistics package has arrived at the pickup station. Bring your ID "
        f"and tracking number to collect it.",
    ])


def _real_personal(r: random.Random) -> str:
    return _maybe_typo(r, r.choice([
        f"Hey {r.choice(_NAMES)}, are we still meeting at {r.randint(1, 9)}pm today?",
        f"Good morning, please confirm if you received the documents I sent yesterday.",
        f"Happy birthday {r.choice(_NAMES)}! Wishing you a wonderful year ahead.",
        f"Please remember to bring the receipt when you come to the office tomorrow.",
        f"{r.choice(_NAMES)}, I've sent your share of the money. Check your account.",
    ]))


def _real_bank_notice(r: random.Random) -> str:
    return (
        f"{r.choice(_BANKS)}: Our branches will be open till 4pm this Saturday for "
        f"account opening. Visit any branch with a valid ID. T&Cs apply."
    )


def _real_school(r: random.Random) -> str:
    return r.choice([
        f"Dear {r.choice(_NAMES)}, your semester result has been uploaded to the "
        f"student portal. Log in with your matric number to view it.",
        f"Reminder: School fees for this term are due next Friday. Kindly make payment "
        f"at the bursary or via the approved school portal.",
    ])


_LEGIT_GENERATORS = [
    _real_credit_alert, _real_debit_alert, _real_otp, _real_bank_security_notice,
    _real_telco_promo, _real_delivery, _real_personal, _real_bank_notice, _real_school,
]


@dataclass
class DatasetConfig:
    n_fraud: int = 1300
    n_legit: int = 1300
    seed: int = 20260720
    max_attempts_factor: int = 40


def _generate_unique(r: random.Random, generators: list, target: int, label: int,
                     max_attempts: int) -> list[dict]:
    seen: set[str] = set()
    rows: list[dict] = []
    attempts = 0
    while len(rows) < target and attempts < max_attempts:
        attempts += 1
        text = r.choice(generators)(r).strip()
        if text and text not in seen:
            seen.add(text)
            rows.append({"text": text, "label": label})
    return rows


def build_dataset(config: DatasetConfig | None = None) -> pd.DataFrame:
    """Return a shuffled, class-balanced DataFrame with columns: text, label."""
    config = config or DatasetConfig()
    r = random.Random(config.seed)

    fraud = _generate_unique(r, _FRAUD_GENERATORS, config.n_fraud, LABEL_FRAUD,
                             config.n_fraud * config.max_attempts_factor)
    legit = _generate_unique(r, _LEGIT_GENERATORS, config.n_legit, LABEL_LEGIT,
                             config.n_legit * config.max_attempts_factor)

    # Balance to the smaller class so metrics aren't skewed.
    n = min(len(fraud), len(legit))
    rows = fraud[:n] + legit[:n]
    r.shuffle(rows)
    return pd.DataFrame(rows).reset_index(drop=True)


if __name__ == "__main__":
    df = build_dataset()
    print(df["label"].value_counts())
    print(df.sample(8, random_state=1).to_string(index=False))
