"""Generate Nigeria_Fraud_SMS.csv — a labelled corpus of Nigerian scam and
legitimate messages, categorised by fraud typology and institution.

Scam typologies covered (>= 500 messages): BVN, KYC, POS, Fake Debit Alert,
Fake Credit Alert, Investment, Employment, Fake Transfer, ATM.
Legitimate messages (>= 500): real alerts, OTP, promos, delivery, personal, notices.

Institutions referenced: GTBank, UBA, Access, Zenith, FirstBank, PalmPay,
Moniepoint, OPay (plus a few others for variety).

Output columns: text, label (1=fraud/0=legit), label_name, category, institution, channel.
Deterministic given the seed.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

BANKS = ["GTBank", "UBA", "Access", "Zenith", "FirstBank", "Fidelity", "FCMB",
         "Union Bank", "Sterling", "Wema"]
FINTECHS = ["PalmPay", "Moniepoint", "OPay", "Kuda", "Carbon", "PiggyVest"]
INSTITUTIONS = BANKS + FINTECHS
TELCOS = ["MTN", "Airtel", "Glo", "9mobile"]
NAMES = ["Chidi", "Aisha", "Emeka", "Ngozi", "Tunde", "Bola", "Ifeoma", "Musa",
         "Yusuf", "Amaka", "Segun", "Fatima", "Chinedu", "Blessing", "Ada", "Kelvin"]
SCAM_LINKS = ["http://gtb-verify.top/login", "bit.ly/acct-reactivate",
              "www.cbn-secure.click", "http://opay-bonus.xyz", "tinyurl.com/loan-ng",
              "http://firstbank-update.info", "cutt.ly/bvn-verify", "rb.gy/kyc-now",
              "http://uba-online.link/secure", "wa.me/2348012345678",
              "http://zenith-reward.xyz", "bit.ly/palmpay-claim"]
REAL_LINKS = ["https://gtbank.com", "https://www.jumia.com.ng/track",
              "https://opay.com", "https://moniepoint.com", "https://mtn.ng/promo"]
PHONES = ["08012345678", "07098765432", "+2349011223344", "08155667788",
          "09033445566", "08167788990", "07012349876", "08109988776"]
GREET = ["Dear Customer", "Dear Valued Customer", "Hello", "Attention",
         "Dear Account Holder", "Dear Esteemed Customer", ""]


def _amt(r: random.Random) -> str:
    return f"{r.choice([2300, 5000, 12500, 25000, 50000, 75000, 150000, 300000, 500000, 1000000]):,}"


def _acct(r: random.Random) -> str:
    return f"{r.randint(1000, 9999)}"


# =============================================================================
# SCAM generators — one per required typology
# =============================================================================

def bvn_scam(r: random.Random, inst: str) -> str:
    return (
        f"{r.choice(GREET)}, your {inst} account will be "
        f"{r.choice(['BLOCKED', 'suspended', 'deactivated'])} because your "
        f"{r.choice(['BVN', 'Bank Verification Number'])} is not linked. "
        f"{r.choice(['Update', 'Verify', 'Re-validate'])} it now at "
        f"{r.choice(SCAM_LINKS)} to avoid closure."
    )


def kyc_scam(r: random.Random, inst: str) -> str:
    return (
        f"{r.choice(GREET)}: Your {inst} account KYC is "
        f"{r.choice(['incomplete', 'outdated', 'due for update'])}. To keep your "
        f"account active, complete your KYC/NIN update at {r.choice(SCAM_LINKS)} "
        f"within {r.choice(['24 hours', '48 hours', 'today'])}."
    )


def pos_scam(r: random.Random, inst: str) -> str:
    return (
        f"POS DEBIT of N{_amt(r)} FAILED but was deducted from your {inst} card. "
        f"Call the merchant helpline {r.choice(PHONES)} now and share your "
        f"{r.choice(['card number and PIN', 'CVV and PIN', 'account and OTP'])} to get an instant refund."
    )


def fake_debit_alert(r: random.Random, inst: str) -> str:
    return (
        f"{inst} Alert: A debit of N{_amt(r)} was made on your account. If you did "
        f"NOT authorise this, call {r.choice(PHONES)} immediately and provide your "
        f"{r.choice(['OTP', 'PIN', 'card details'])} to reverse it."
    )


def fake_credit_alert(r: random.Random, inst: str) -> str:
    return (
        f"{inst}: You have received N{_amt(r)} but it is "
        f"{r.choice(['pending', 'on hold', 'awaiting confirmation'])}. To release the "
        f"funds, confirm your account by paying a N{r.choice(['1,500', '2,000', '3,500'])} "
        f"clearance fee to {r.choice(PHONES)}."
    )


def investment_scam(r: random.Random, inst: str) -> str:
    return (
        f"{r.choice(['Double your money', 'Earn N30,000 daily', '100% ROI guaranteed'])} "
        f"in {r.choice(['48 hours', '3 days', 'one week'])}! "
        f"{r.choice(['Crypto', 'Forex', 'USDT'])} trading via {inst}. Invest N{_amt(r)}, "
        f"sign-up bonus for first 100 people. Join {r.choice(SCAM_LINKS)}"
    )


def employment_scam(r: random.Random, inst: str) -> str:
    return (
        f"CONGRATULATIONS! You have been shortlisted for a {r.choice(['remote', 'federal', 'bank'])} "
        f"job at {inst} paying N{_amt(r)}/month. No interview needed. Pay a "
        f"{r.choice(['training', 'registration', 'ID card'])} fee of "
        f"N{r.choice(['5,000', '7,500', '10,000'])} to {r.choice(PHONES)} to secure the role."
    )


def fake_transfer(r: random.Random, inst: str) -> str:
    return r.choice([
        f"Hi, I just sent N{_amt(r)} to your {inst} account by mistake. Please help me "
        f"send it back to {r.choice(PHONES)}. I have attached the receipt.",
        f"{inst}: Transfer of N{_amt(r)} from {r.choice(NAMES)} is awaiting your approval. "
        f"Approve at {r.choice(SCAM_LINKS)} using your login details.",
    ])


def atm_scam(r: random.Random, inst: str) -> str:
    return (
        f"{inst}: Your ATM card has been "
        f"{r.choice(['blocked', 'deactivated', 'flagged for fraud'])}. To reactivate, "
        f"call {r.choice(PHONES)} and provide your "
        f"{r.choice(['16-digit card number, expiry and CVV', 'card number and PIN', 'ATM PIN'])}."
    )


SCAM_GENERATORS = {
    "BVN Scam": bvn_scam,
    "KYC Scam": kyc_scam,
    "POS Scam": pos_scam,
    "Fake Debit Alert": fake_debit_alert,
    "Fake Credit Alert": fake_credit_alert,
    "Investment Scam": investment_scam,
    "Employment Scam": employment_scam,
    "Fake Transfer": fake_transfer,
    "ATM Scam": atm_scam,
}


# =============================================================================
# LEGIT generators (incl. hard negatives with scary keywords)
# =============================================================================

def real_credit_alert(r: random.Random, inst: str) -> str:
    return (f"{inst}: Credit Alert. Acct **{_acct(r)}. Amt:NGN{_amt(r)}. "
            f"Desc:Transfer from {r.choice(NAMES)}. Bal:NGN{_amt(r)}.")


def real_debit_alert(r: random.Random, inst: str) -> str:
    return (f"{inst}: Debit Alert. Acct **{_acct(r)}. Amt:NGN{_amt(r)}. "
            f"Desc:{r.choice(['POS purchase', 'Airtime', 'Transfer', 'Web payment'])}. "
            f"Avail Bal:NGN{_amt(r)}.")


def real_otp(r: random.Random, inst: str) -> str:
    return (f"{r.randint(100000, 999999)} is your {inst} one-time password (OTP). "
            f"Do NOT share it with anyone, including our staff. Expires in "
            f"{r.choice([5, 10, 15])} minutes.")


def real_security_notice(r: random.Random, inst: str) -> str:
    secret = r.choice(["BVN, PIN, OTP or password", "PIN or OTP",
                       "card details or one-time password", "internet banking password"])
    return r.choice([
        f"{inst} will NEVER ask for your {secret}. Never share them with anyone. "
        f"Report suspicious messages to our official customer care.",
        f"{inst} Security: if you did NOT perform the last transaction, please visit "
        f"your nearest branch or call the number on the back of your card.",
        f"Stay safe with {inst}: we will never call to ask for your {secret}. "
        f"If someone does, hang up and report it.",
        f"{inst} advisory: beware of {r.choice(['fake', 'cloned', 'phishing'])} messages "
        f"asking for your {secret}. Only use our official app or *{r.randint(300, 999)}#.",
        f"Security reminder from {inst}: protect your account. Do not share your {secret} "
        f"even if the caller claims to be from the bank.",
    ])


def real_transaction_notice(r: random.Random, inst: str) -> str:
    return r.choice([
        f"{inst}: Your statement for the month is ready. View it on the {inst} app or "
        f"internet banking.",
        f"{inst}: Your standing order of NGN{_amt(r)} to {r.choice(NAMES)} was processed "
        f"successfully.",
        f"{inst}: Your card ending {r.randint(1000, 9999)} was used for a NGN{_amt(r)} "
        f"purchase. Not you? Reply via the app.",
        f"{inst}: Your loan repayment of NGN{_amt(r)} is due on the {r.randint(1, 28)}th. "
        f"Ensure your account is funded.",
    ])


def real_telco_promo(r: random.Random, inst: str) -> str:
    return (f"{r.choice(TELCOS)}: Get {r.choice(['1.5GB', '3GB', '6GB'])} for "
            f"N{r.choice(['500', '1,000', '1,500'])}. Dial *{r.randint(100, 999)}# to "
            f"activate. Valid 30 days. T&Cs apply.")


def real_delivery(r: random.Random, inst: str) -> str:
    return r.choice([
        f"Hi {r.choice(NAMES)}, your Jumia order #{r.randint(100000, 999999)} is out for "
        f"delivery today. Track at {r.choice(REAL_LINKS)}. The rider will call you.",
        f"Your GIG Logistics package has arrived at the pickup station. Bring your ID "
        f"and tracking number to collect it.",
    ])


def real_personal(r: random.Random, inst: str) -> str:
    return r.choice([
        f"Hey {r.choice(NAMES)}, are we still meeting at {r.randint(1, 9)}pm today?",
        f"Good morning, please confirm you received the documents I sent yesterday.",
        f"Happy birthday {r.choice(NAMES)}! Wishing you a wonderful year ahead.",
        f"{r.choice(NAMES)}, I've sent your share. Check your account when you can.",
        f"Please remember to bring the receipt to the office tomorrow.",
    ])


def real_bank_notice(r: random.Random, inst: str) -> str:
    day = r.choice(["Saturday", "Monday", "this weekend", "next week"])
    return r.choice([
        f"{inst}: Our branches open till {r.randint(2, 5)}pm this {day} for account "
        f"opening. Visit any branch with a valid ID. T&Cs apply.",
        f"{inst}: Enjoy zero charges on transfers below NGN{r.choice(['5,000', '10,000'])} "
        f"this {day}. Terms apply.",
        f"{inst}: Scheduled maintenance on {day} from 1am-3am. Some services may be "
        f"briefly unavailable. We apologise for any inconvenience.",
        f"{inst}: Update your contact details at any branch or on the app to keep "
        f"receiving important account notifications.",
        f"{inst}: Our new branch in {r.choice(['Lekki', 'Ikeja', 'Abuja', 'Kano', 'Enugu'])} "
        f"is now open. Come bank with us!",
    ])


def real_school(r: random.Random, inst: str) -> str:
    name = r.choice(NAMES)
    return r.choice([
        f"Dear {name}, your semester result is on the student portal. Log in with your "
        f"matric number to view it.",
        f"Reminder: school fees are due on the {r.randint(1, 28)}th. Pay at the bursary "
        f"or the approved school portal.",
        f"Dear {name}, lectures for {r.choice(['CSC', 'MTH', 'ENG', 'BUS'])}"
        f"{r.randint(100, 400)} resume on Monday. Check the portal for the venue.",
        f"Notice: {r.choice(['first', 'second'])} semester exams begin on the "
        f"{r.randint(1, 28)}th. Clear your outstanding fees to sit for exams.",
        f"Dear {name}, your course registration for the new session is now open on the "
        f"student portal. Deadline is the {r.randint(1, 28)}th.",
    ])


LEGIT_GENERATORS = {
    "Legit Credit Alert": real_credit_alert,
    "Legit Debit Alert": real_debit_alert,
    "Legit OTP": real_otp,
    "Legit Security Notice": real_security_notice,
    "Legit Promo": real_telco_promo,
    "Legit Delivery": real_delivery,
    "Legit Personal": real_personal,
    "Legit Bank Notice": real_bank_notice,
    "Legit School": real_school,
    "Legit Transaction Notice": real_transaction_notice,
}


def _channel(r: random.Random, category: str) -> str:
    if "OTP" in category or "Alert" in category:
        return "sms"
    if "Personal" in category or "Transfer" in category:
        return r.choice(["whatsapp", "sms"])
    return r.choice(["sms", "whatsapp", "sms"])


def _generate(r: random.Random, generators: dict, per_category: int, label: int,
              label_name: str) -> list[dict]:
    rows: list[dict] = []
    for category, fn in generators.items():
        seen: set[str] = set()
        attempts = 0
        while len(seen) < per_category and attempts < per_category * 60:
            attempts += 1
            inst = r.choice(INSTITUTIONS)
            text = fn(r, inst).strip()
            if text and text not in seen:
                seen.add(text)
                rows.append({
                    "text": text, "label": label, "label_name": label_name,
                    "category": category, "institution": inst,
                    "channel": _channel(r, category),
                })
    return rows


@dataclass
class GenConfig:
    scam_per_category: int = 60     # 9 categories -> ~540 scam
    legit_per_category: int = 60    # 9 categories -> ~540 legit
    seed: int = 20260721


def build_nigeria_dataset(config: GenConfig | None = None) -> pd.DataFrame:
    config = config or GenConfig()
    r = random.Random(config.seed)
    scam = _generate(r, SCAM_GENERATORS, config.scam_per_category, 1, "fraud")
    legit = _generate(r, LEGIT_GENERATORS, config.legit_per_category, 0, "legit")
    rows = scam + legit
    r.shuffle(rows)
    return pd.DataFrame(rows)


def write_csv(out_path: Path, config: GenConfig | None = None) -> pd.DataFrame:
    df = build_nigeria_dataset(config)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False, encoding="utf-8")
    return df


if __name__ == "__main__":
    here = Path(__file__).resolve().parents[2]
    out = here / "data" / "generated" / "Nigeria_Fraud_SMS.csv"
    df = write_csv(out)
    print(f"Wrote {len(df)} rows -> {out}")
    print(df["label_name"].value_counts().to_string())
    print(df["category"].value_counts().to_string())
