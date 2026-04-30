# Treasury Management Patterns on XRPL

## Wallet Hierarchy Architecture

A well-designed treasury uses defense-in-depth: the cold wallet never touches the internet, the hot wallet has limited authority, and all large operations require multi-signature.

```
COLD WALLET (Air-gapped hardware)
  ├── Master key: 3-of-5 hardware security keys (Ledger Nano / YubiKey)
  ├── Flags: RequireDestTag=ON, DefaultRipple=OFF, DisallowXRP=OFF
  ├── Balance: Minimum XRP (just enough for reserve)
  └── Signs: Key rotation, SignerList changes, emergency recovery
  
  └── TREASURY WALLET (Semi-Hot, Multi-Sig)
       ├── RegularKey → rotated weekly
       ├── SignerList: 2-of-3 for amounts > 10K XRP
       ├── Flags: DepositPreAuth=ON (whitelist outflows)
       └── Disburses to:
            ├── HOT WALLET → daily operations (<1K XRP limit)
            ├── LIQUIDITY WALLET → DEX/AMM ops (<50K XRP)
            └── RESERVE WALLET → 90-day lock via Escrow
```

---

## Account Setup: Security Flags

```python
import xrpl, os
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import AccountSet
from xrpl.models.transactions.account_set import AccountSetFlag
from xrpl.transaction import submit_and_wait

client = JsonRpcClient("https://xrplcluster.com")
treasury = Wallet.from_secret(os.environ["TREASURY_SECRET"])

# Configure treasury account security
config = AccountSet(
    account=treasury.classic_address,
    # Require destination tag on all incoming payments (avoids misrouted funds)
    set_flag=AccountSetFlag.ASF_REQUIRE_DEST,
    # Optional: ASF_DISABLE_MASTER if using RegularKey + SignerList only
    # set_flag=AccountSetFlag.ASF_DISABLE_MASTER,
    email_hash="d41d8cd98f00b204e9800998ecf8427e",  # Optional MD5 of contact email
)
resp = submit_and_wait(config, client, treasury)
print(f"Account configured: {resp.result['meta']['TransactionResult']}")
```

---

## Multi-Signature Setup

```python
from xrpl.models.transactions import SignerListSet
from xrpl.models.transactions.signer_list_set import SignerEntry

# Create a 2-of-3 SignerList
signer_setup = SignerListSet(
    account=treasury.classic_address,
    signer_quorum=2,   # Need 2 of 3 signers
    signer_entries=[
        SignerEntry(
            account="rSigner1...",
            signer_weight=1,
        ),
        SignerEntry(
            account="rSigner2...",
            signer_weight=1,
        ),
        SignerEntry(
            account="rSigner3...",
            signer_weight=2,  # CTO key counts as 2 (can solo-approve emergencies)
        ),
    ],
)
resp = submit_and_wait(signer_setup, client, treasury)

# To REMOVE a SignerList (restore to single-key): set signer_quorum=0, signer_entries=[]
```

### Submitting a Multi-Sig Transaction

```python
from xrpl.models.transactions import Payment
from xrpl.transaction import multisign, sign

signer1 = Wallet.from_secret(os.environ["SIGNER1_SECRET"])
signer2 = Wallet.from_secret(os.environ["SIGNER2_SECRET"])

# Step 1: Build the transaction (don't sign yet)
payment = Payment(
    account=treasury.classic_address,
    destination="rRecipient...",
    amount=xrpl.utils.xrp_to_drops("5000"),
    sequence=treasury_sequence,
    last_ledger_sequence=treasury_sequence + 50,
    fee="20",  # Multi-sig fee = base_fee * (1 + signers)
    signing_public_key="",  # Empty for multi-sig
)

# Step 2: Each signer signs independently
tx_blob = payment.to_xrpl()  # Get unsigned dict
signed1 = sign(payment, signer1, multisign=True)
signed2 = sign(payment, signer2, multisign=True)

# Step 3: Combine signatures
combined = multisign(payment, [signed1, signed2])

# Step 4: Submit combined transaction
resp = client.submit_multisigned(combined)
print(f"Multi-sig submit: {resp.result.get('engine_result')}")
```

---

## Regular Key Management

```python
from xrpl.models.transactions import SetRegularKey

# Set a regular key (used for day-to-day signing; master key stays offline)
new_hot_key = Wallet.create()

set_key = SetRegularKey(
    account=treasury.classic_address,
    regular_key=new_hot_key.classic_address,
)
# MUST be signed with the MASTER key (or current regular key)
resp = submit_and_wait(set_key, client, treasury)

# Now save new_hot_key securely, revoke old one
# To remove regular key entirely:
remove_key = SetRegularKey(
    account=treasury.classic_address,
    # Omit regular_key field to clear it
)
```

### Rotation Schedule Enforcer

```python
import time, json
from pathlib import Path

KEY_ROTATION_INTERVAL = 7 * 24 * 3600  # 1 week

def check_key_rotation_needed(state_file: str = "key_state.json") -> bool:
    try:
        state = json.loads(Path(state_file).read_text())
        last_rotation = state.get("last_rotation", 0)
        return time.time() - last_rotation > KEY_ROTATION_INTERVAL
    except FileNotFoundError:
        return True

def record_rotation(state_file: str = "key_state.json"):
    Path(state_file).write_text(json.dumps({
        "last_rotation": time.time(),
        "rotated_at_ledger": client.request(xrpl.models.requests.ServerInfo()).result["info"]["validated_ledger"]["seq"],
    }))
```

---

## Escrow Vault (Time-Locked Reserves)

```python
from xrpl.models.transactions import EscrowCreate, EscrowFinish, EscrowCancel
import time

def create_time_locked_reserve(
    client,
    treasury: Wallet,
    destination: str,
    amount_xrp: float,
    lock_days: int,
) -> dict:
    """Lock XRP in escrow; recipient can claim after lock_days."""
    # Get current ledger time (ripple epoch = Unix - 946684800)
    RIPPLE_EPOCH = 946684800
    lock_seconds = lock_days * 24 * 3600
    finish_after = int(time.time() - RIPPLE_EPOCH) + lock_seconds
    cancel_after = finish_after + 3600  # 1-hour window to claim before auto-cancel

    escrow = EscrowCreate(
        account=treasury.classic_address,
        destination=destination,
        amount=xrpl.utils.xrp_to_drops(str(amount_xrp)),
        finish_after=finish_after,
        cancel_after=cancel_after,
    )
    resp = submit_and_wait(escrow, client, treasury)

    # Extract escrow sequence from result
    escrow_seq = None
    for node in resp.result['meta']['AffectedNodes']:
        created = node.get('CreatedNode', {})
        if created.get('LedgerEntryType') == 'Escrow':
            escrow_seq = created['NewFields']['Sequence']

    return {
        "hash": resp.result['hash'],
        "escrow_sequence": escrow_seq,
        "finish_after_unix": finish_after + RIPPLE_EPOCH,
        "amount_xrp": amount_xrp,
    }


def claim_escrow(client, claimer: Wallet, escrow_owner: str, escrow_sequence: int):
    """Claim a time-locked escrow after finish_after."""
    finish = EscrowFinish(
        account=claimer.classic_address,
        owner=escrow_owner,
        offer_sequence=escrow_sequence,
    )
    return submit_and_wait(finish, client, claimer)


def cancel_expired_escrow(client, creator: Wallet, escrow_sequence: int):
    """Cancel escrow after cancel_after window."""
    cancel = EscrowCancel(
        account=creator.classic_address,
        owner=creator.classic_address,
        offer_sequence=escrow_sequence,
    )
    return submit_and_wait(cancel, client, creator)
```

---

## Payment Channels for High-Frequency Disbursements

```python
from xrpl.models.transactions import (
    PaymentChannelCreate, PaymentChannelClaim, PaymentChannelFund
)
import xrpl.core.keypairs as kp

def create_disbursement_channel(
    client,
    treasury: Wallet,
    recipient: str,
    capacity_xrp: float,
    settle_delay_seconds: int = 86400,
) -> str:
    """
    Create payment channel for recurring payouts.
    Returns the channel ID.
    settle_delay: how long recipient must wait after submitting final claim.
    """
    channel_tx = PaymentChannelCreate(
        account=treasury.classic_address,
        destination=recipient,
        amount=xrpl.utils.xrp_to_drops(str(capacity_xrp)),
        settle_delay=settle_delay_seconds,
        public_key=treasury.public_key,
    )
    resp = submit_and_wait(channel_tx, client, treasury)

    channel_id = None
    for node in resp.result['meta']['AffectedNodes']:
        created = node.get('CreatedNode', {})
        if created.get('LedgerEntryType') == 'PayChannel':
            channel_id = created['NewFields'].get('Channel') or resp.result['hash']

    return channel_id


def sign_channel_claim(treasury: Wallet, channel_id: str, amount_drops: int) -> str:
    """Sign an off-ledger payment channel claim."""
    claim_data = xrpl.core.keypairs.sign_payment_channel_claim(
        channel=channel_id,
        amount=str(amount_drops),
        private_key=treasury.private_key,
    )
    return claim_data


def submit_channel_claim(client, recipient: Wallet, channel_id: str, amount_drops: int, signature: str):
    """Recipient submits the accumulated claim to the ledger."""
    claim = PaymentChannelClaim(
        account=recipient.classic_address,
        channel=channel_id,
        amount=str(amount_drops),
        balance=str(amount_drops),
        signature=signature,
        public_key=recipient.public_key,
        flags=0x00010000,  # tfClose after claiming
    )
    return submit_and_wait(claim, client, recipient)
```

---

## Spending Limit Enforcement

```python
import sqlite3, time
from contextlib import contextmanager

class SpendingLimiter:
    LIMITS = {
        "hot":        {"daily_xrp": 5_000,   "single_xrp": 1_000},
        "liquidity":  {"daily_xrp": 50_000,  "single_xrp": 10_000},
        "treasury":   {"daily_xrp": 500_000, "single_xrp": 100_000},
    }

    def __init__(self, db_path: str = "treasury.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS spend_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wallet_label TEXT,
                amount_xrp REAL,
                tx_hash TEXT,
                timestamp REAL DEFAULT (unixepoch())
            )
        """)
        self.conn.commit()

    def daily_spend(self, label: str) -> float:
        cutoff = time.time() - 86400
        row = self.conn.execute(
            "SELECT COALESCE(SUM(amount_xrp), 0) FROM spend_log WHERE wallet_label=? AND timestamp > ?",
            (label, cutoff)
        ).fetchone()
        return row[0]

    def can_spend(self, label: str, amount_xrp: float) -> tuple[bool, str]:
        limits = self.LIMITS.get(label, {})
        if not limits:
            return False, f"Unknown wallet label: {label}"

        single_limit = limits["single_xrp"]
        daily_limit = limits["daily_xrp"]

        if amount_xrp > single_limit:
            return False, f"Exceeds single-tx limit ({single_limit} XRP)"

        daily = self.daily_spend(label)
        if daily + amount_xrp > daily_limit:
            return False, f"Exceeds daily limit: {daily:.2f}/{daily_limit} XRP spent"

        return True, "OK"

    def record_spend(self, label: str, amount_xrp: float, tx_hash: str):
        self.conn.execute(
            "INSERT INTO spend_log (wallet_label, amount_xrp, tx_hash) VALUES (?, ?, ?)",
            (label, amount_xrp, tx_hash)
        )
        self.conn.commit()


# Usage
limiter = SpendingLimiter()
ok, reason = limiter.can_spend("hot", 500)
if not ok:
    raise PermissionError(f"Spend rejected: {reason}")
# ... submit tx ...
limiter.record_spend("hot", 500, tx_hash)
```

---

## DCA (Dollar-Cost Averaging) Pattern

```python
import schedule, threading
from xrpl.models.transactions import OfferCreate
from xrpl.models.transactions.offer_create import OfferCreateFlag
from xrpl.models.amounts import IssuedCurrencyAmount

def dca_buy(
    client,
    wallet: Wallet,
    currency: str,
    issuer: str,
    xrp_per_run: float,
    max_slippage_pct: float = 1.0,
):
    """Buy `currency` with XRP at market, with slippage protection."""
    from xrpl.models.requests import BookOffers

    # Check best ask price
    asks = client.request(BookOffers(
        taker_pays={"currency": currency, "issuer": issuer},
        taker_gets={"currency": "XRP"},
        limit=5,
    )).result.get("offers", [])

    if not asks:
        print("No sell orders available")
        return

    best_ask_xrp = int(asks[0]["TakerGets"]) / 1e6
    best_ask_token = float(asks[0]["TakerPays"]["value"])
    market_price = best_ask_xrp / best_ask_token

    # Apply slippage protection
    max_price = market_price * (1 + max_slippage_pct / 100)
    token_amount = xrp_per_run / max_price

    buy = OfferCreate(
        account=wallet.classic_address,
        taker_pays=IssuedCurrencyAmount(
            currency=currency,
            issuer=issuer,
            value=str(round(token_amount, 6)),
        ),
        taker_gets=xrpl.utils.xrp_to_drops(str(xrp_per_run)),
        flags=OfferCreateFlag.TF_IMMEDIATE_OR_CANCEL,  # Don't leave resting order
    )
    resp = submit_and_wait(buy, client, wallet)
    result = resp.result['meta']['TransactionResult']
    print(f"DCA buy: {result} — {xrp_per_run} XRP → {currency}")


# Schedule DCA every 24 hours
def start_dca_scheduler(client, wallet, currency, issuer, daily_xrp):
    schedule.every(24).hours.do(
        dca_buy, client, wallet, currency, issuer, daily_xrp
    )
    while True:
        schedule.run_pending()
        time.sleep(60)

dca_thread = threading.Thread(
    target=start_dca_scheduler,
    args=(client, hot_wallet, "USD", "rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B", 100),
    daemon=True,
)
dca_thread.start()
```

---

## DepositPreAuth (Whitelist Incoming Payments)

```python
from xrpl.models.transactions import DepositPreauth

# Treasury only accepts payments from whitelisted addresses
whitelist = ["rOperations...", "rLiquidityBot...", "rPartner..."]

for addr in whitelist:
    preauth = DepositPreauth(
        account=treasury.classic_address,
        authorize=addr,
    )
    submit_and_wait(preauth, client, treasury)

# Revoke an authorization
revoke = DepositPreauth(
    account=treasury.classic_address,
    unauthorize="rOldPartner...",
)
submit_and_wait(revoke, client, treasury)
```

---

## Treasury Health Report

```python
from xrpl.models.requests import AccountInfo, AccountLines, AccountOffers, EscrowObjects

def treasury_report(client, wallets: dict[str, str]) -> dict:
    """
    wallets: {label: address}
    Returns full balance + open positions report.
    """
    report = {}

    for label, address in wallets.items():
        wallet_data = {}

        # XRP balance
        acc = client.request(AccountInfo(account=address, ledger_index="validated"))
        drops = int(acc.result["account_data"]["Balance"])
        reserve = int(acc.result["account_data"].get("OwnerCount", 0)) * 2 + 10
        wallet_data["xrp_balance"] = drops / 1e6
        wallet_data["xrp_available"] = (drops / 1e6) - reserve

        # Token balances
        lines = client.request(AccountLines(account=address, ledger_index="validated"))
        wallet_data["tokens"] = {
            f"{l['currency']}@{l['account'][:8]}": float(l["balance"])
            for l in lines.result.get("lines", [])
        }

        # Open DEX offers
        offers = client.request(AccountOffers(account=address))
        wallet_data["open_offers"] = len(offers.result.get("offers", []))

        report[label] = wallet_data

    return report
```

---

## Related Files
- `knowledge/09-xrpl-escrow.md` — escrow mechanics in depth
- `knowledge/11-xrpl-payment-channels.md` — payment channel guide
- `knowledge/12-xrpl-multisig.md` — multi-signature setup
- `knowledge/25-xrpl-audit-security.md` — security best practices
- `knowledge/41-xrpl-bots-patterns.md` — bot patterns used with treasury wallets
