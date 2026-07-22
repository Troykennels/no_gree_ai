"""Live-feed simulator - drives the Automation Engine with Nigerian traffic.

Real deployments feed the engine from bank/telco webhooks. For a self-contained
demo, this generates a realistic stream of Nigerian scam SMS and card
transactions - real banks (GTBank, UBA, Access, Zenith, FirstBank) and fintechs
(PalmPay, Moniepoint, OPay), Naira amounts, Nigerian names and cities - and pushes
them through the exact same ingest path, so the whole dashboard animates on its
own, end to end, with no external integration.

Only one simulation runs at a time (starting again replaces the previous run).
"""

from __future__ import annotations

import asyncio
import random

from app.infrastructure.automation.engine import NIGERIA_REGIONS, AutomationEngine

# Nigerian banks + fintechs.
BANKS = ["GTBank", "UBA", "Access Bank", "Zenith Bank", "FirstBank",
         "PalmPay", "Moniepoint", "OPay"]

# Nigerian names spanning the major regions.
FIRST_NAMES = ["Chidi", "Ada", "Emeka", "Ngozi", "Tunde", "Bola", "Yusuf", "Aisha",
               "Ifeoma", "Musa", "Kemi", "Segun", "Chioma", "Uche", "Fatima",
               "Ibrahim", "Blessing", "Femi", "Amaka", "Obinna", "Zainab", "Nnamdi"]
LAST_NAMES = ["Okafor", "Adeyemi", "Okonkwo", "Bello", "Eze", "Balogun", "Abubakar",
              "Nwosu", "Adebayo", "Ogunleye", "Chukwu", "Danjuma", "Okoro",
              "Mohammed", "Afolabi", "Onyeka", "Ibrahim", "Oluwaseun"]

_SCAM_MESSAGES = [
    "Dear GTBank customer, your account will be BLOCKED today. Update your BVN via http://gtb-verify.top to avoid deactivation.",
    "UBA ALERT: Your account has been suspended. Reactivate now at http://uba-reactivate.click or lose access permanently.",
    "Access Bank: You have a pending transfer of N250,000. Confirm your OTP and card PIN to receive it: http://access-claim.top",
    "Zenith Bank: Revalidate your NIN to avoid deactivation of your account. Click http://nin-zenith.xyz now.",
    "FirstBank: Your token has expired. Call 08031234567 and share your OTP to restore access immediately.",
    "CONGRATULATIONS! You won N2,000,000 in the MTN promo. Send your BVN and ATM PIN to claim your prize now.",
    "PalmPay: You received N50,000. Click http://palmpay-credit.top and enter your PIN to withdraw the funds.",
    "OPay reward: Your N30,000 cashback is pending. Verify your card number and OTP at http://opay-reward.click.",
    "Moniepoint: Your agent wallet is locked. Send your transaction PIN to 07011122233 to unlock it now.",
    "FG palliative of N35,000 approved for you. Pay a N1,500 processing fee to 08039876543 to receive your money.",
    "Hi, this is Ada from GTBank fraud desk. We noticed suspicious activity - confirm your BVN and PIN to secure your account.",
    "Pre-approved instant loan of N150,000, NO collateral. Pay a small fee to unlock: bit.ly/loan-ng-now",
]
_LEGIT_MESSAGES = [
    "GTBank: Debit Alert. Acct **4821. Amt:NGN12,500.00. Desc:POS SHOPRITE IKEJA. Bal:NGN61,300.15.",
    "Access Bank: Credit Alert. NGN25,000 from CHIDI OKAFOR. Bal:NGN142,000.00.",
    "Zenith Bank: You spent NGN3,500 at CHICKEN REPUBLIC on card **2290. Bal:NGN88,700.",
    "UBA: Your airtime purchase of NGN2,000 was successful. Bal:NGN33,120.",
    "Hi Tunde, abeg send me 5k for transport, I go pay back on Friday. Thank you.",
    "Your Jumia order NG18823 has shipped and arrives in Ibadan on Thursday.",
    "FirstBank: Your DSTV subscription of NGN9,900 was successful. Enjoy!",
    "Moniepoint: You received NGN8,000 from NGOZI EZE. Bal:NGN51,200.",
    "OPay: Transfer of NGN15,000 to EMEKA received. Bal:NGN47,300.",
    "PalmPay: Your electricity token for meter 4551 is 1234-5678. Amount NGN5,000.",
]
_CHANNELS = ["sms", "whatsapp", "email", "pos"]


def _name() -> str:
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def _random_transaction() -> tuple[dict, str, str]:
    """Return (model features with a Naira TransactionAmt, bank, payer name).

    Weighted toward legit, with a minority of high-value, high-risk transfers.
    """
    risky = random.random() < 0.35
    bank = random.choice(BANKS)
    payer = _name()
    if risky:
        feats = {
            "TransactionAmt": round(random.uniform(200_000, 5_000_000), 2),  # Naira
            "ProductCD": random.choice(["C", "S", "R"]),
            "card4": random.choice(["mastercard", "verve"]),
            "card6": "credit",
            "P_emaildomain": random.choice(["outlook.com", "hotmail.com", "yahoo.co.uk"]),
            "C1": random.randint(20, 70),
            "C13": random.randint(25, 80),
        }
    else:
        feats = {
            "TransactionAmt": round(random.uniform(500, 150_000), 2),  # Naira
            "ProductCD": "W",
            "card4": random.choice(["visa", "mastercard", "verve"]),
            "card6": "debit",
            "P_emaildomain": random.choice(["gmail.com", "yahoo.com"]),
            "C1": random.randint(1, 4),
            "C13": random.randint(1, 6),
        }
    return feats, bank, payer


class SimulationManager:
    def __init__(self) -> None:
        self._task: asyncio.Task | None = None

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    def start(self, engine: AutomationEngine, count: int = 40,
              interval_ms: int = 900) -> bool:
        if self.running:
            return False
        self._task = asyncio.create_task(self._run(engine, count, interval_ms / 1000.0))
        return True

    def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
        self._task = None

    async def _run(self, engine: AutomationEngine, count: int, interval: float) -> None:
        try:
            for _ in range(count):
                region = random.choice(NIGERIA_REGIONS)
                if random.random() < 0.55:
                    scam = random.random() < 0.45
                    msg = random.choice(_SCAM_MESSAGES if scam else _LEGIT_MESSAGES)
                    await engine.ingest_message(msg, channel=random.choice(_CHANNELS), region=region)
                else:
                    feats, bank, payer = _random_transaction()
                    await engine.ingest_transaction(feats, region=region, bank=bank, payer=payer)
                await asyncio.sleep(interval)
            await engine.generate_daily_report_and_publish()
        except asyncio.CancelledError:
            pass


_manager: SimulationManager | None = None


def get_simulation_manager() -> SimulationManager:
    global _manager
    if _manager is None:
        _manager = SimulationManager()
    return _manager
