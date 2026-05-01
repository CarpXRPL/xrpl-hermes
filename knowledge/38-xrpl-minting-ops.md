# Advanced Token Minting Operations

## Token Architecture Overview

Before minting, choose the right token type:

| Type | Standard | Reserve | Best For |
|------|----------|---------|---------|
| IOU (Trust Line) | Native | 5 XRP/holder | Stablecoins, rewards, complex permissions |
| NFToken | XLS-20 | 0.2 XRP/page (16-32 per page) | Unique digital items, collectibles |
| MPToken | XLS-33 | ~0.1 XRP/issuance | High-volume tokens, regulated assets |

---

## IOU Issuance: Complete Setup

```python
import xrpl
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import AccountSet, TrustSet, Payment
from xrpl.models.transactions.account_set import AccountSetFlag
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.transaction import submit_and_wait

client = JsonRpcClient("https://xrplcluster.com")

# NEVER hardcode secrets — load from environment or vault
import os
issuer = Wallet.from_secret(os.environ["ISSUER_SECRET"])

# Step 1: Configure issuer account
# asfDefaultRipple: allows tokens to ripple through (essential for DEX trading)
# asfRequireDestTag: requires destination tag for incoming payments
setup_tx = AccountSet(
    account=issuer.classic_address,
    set_flag=AccountSetFlag.ASF_DEFAULT_RIPPLE,
    # NOTE: Never set DefaultRipple if you intend to use Clawback
)
resp = submit_and_wait(setup_tx, client, issuer)
print(f"Issuer setup: {resp.result['meta']['TransactionResult']}")

# Step 2: Holder must set a trust line BEFORE receiving tokens
holder = Wallet.from_secret(os.environ["HOLDER_SECRET"])
trust_tx = TrustSet(
    account=holder.classic_address,
    limit_amount=IssuedCurrencyAmount(
        currency="TOKEN",
        issuer=issuer.classic_address,
        value="1000000000",  # Max they're willing to hold
    ),
)
resp = submit_and_wait(trust_tx, client, holder)
print(f"Trust line: {resp.result['meta']['TransactionResult']}")

# Step 3: Issue tokens (payment from issuer "creates" them)
issue_tx = Payment(
    account=issuer.classic_address,
    destination=holder.classic_address,
    amount=IssuedCurrencyAmount(
        currency="TOKEN",
        issuer=issuer.classic_address,
        value="500000",  # Issue 500K tokens
    ),
)
resp = submit_and_wait(issue_tx, client, issuer)
print(f"Issued: {resp.result['meta']['TransactionResult']}")
```

---

## Batch Minting with Tickets (High-Throughput)

The XRPL normally requires sequential `Sequence` numbers. Tickets let you pre-allocate a block and submit transactions in any order — essential for batch operations.

```python
from xrpl.models.transactions import TicketCreate
from xrpl.models.requests import AccountInfo
import asyncio, concurrent.futures

def create_ticket_block(client, wallet, count: int) -> list[int]:
    """Create N tickets and return their sequence numbers."""
    tx = TicketCreate(
        account=wallet.classic_address,
        ticket_count=count,
    )
    resp = submit_and_wait(tx, client, wallet)
    if resp.result['meta']['TransactionResult'] != 'tesSUCCESS':
        raise RuntimeError(f"TicketCreate failed: {resp.result['meta']['TransactionResult']}")

    # Extract ticket sequences from created ledger objects
    tickets = []
    for node in resp.result['meta'].get('AffectedNodes', []):
        created = node.get('CreatedNode', {})
        if created.get('LedgerEntryType') == 'Ticket':
            tickets.append(created['NewFields']['TicketSequence'])
    tickets.sort()
    return tickets


def batch_issue_tokens(
    client, issuer, recipients: list[dict], currency: str
) -> list[dict]:
    """
    recipients: [{"address": "r...", "amount": "1000"}, ...]
    Returns list of {address, hash, result}
    """
    count = len(recipients)
    tickets = create_ticket_block(client, issuer, count)

    results = []
    for ticket_seq, recipient in zip(tickets, recipients):
        tx = Payment(
            account=issuer.classic_address,
            destination=recipient["address"],
            amount=IssuedCurrencyAmount(
                currency=currency,
                issuer=issuer.classic_address,
                value=str(recipient["amount"]),
            ),
            ticket_sequence=ticket_seq,
            sequence=0,  # MUST be 0 when using ticket
        )
        # Fire-and-forget; collect hashes for later verification
        resp = client.submit(tx, issuer)
        tx_hash = resp.result.get("tx_json", {}).get("hash", "")
        results.append({
            "address": recipient["address"],
            "hash": tx_hash,
            "preliminary": resp.result.get("engine_result"),
        })

    return results


def verify_batch(client, hashes: list[str], timeout_s: int = 60) -> dict:
    """Poll until all hashes are validated or timeout."""
    import time
    from xrpl.models.requests import Tx

    pending = set(hashes)
    final = {}
    start = time.time()

    while pending and time.time() - start < timeout_s:
        for tx_hash in list(pending):
            try:
                resp = client.request(Tx(transaction=tx_hash))
                if resp.result.get("validated"):
                    result = resp.result["meta"]["TransactionResult"]
                    final[tx_hash] = result
                    pending.remove(tx_hash)
            except Exception:
                pass
        if pending:
            time.sleep(4)  # Wait one ledger close

    for h in pending:
        final[h] = "TIMEOUT"
    return final
```

---

## Airdrop at Scale: Holder Snapshot

```python
import requests
from xrpl.models.requests import AccountLines
from dataclasses import dataclass

@dataclass
class HolderPosition:
    address: str
    balance: float
    trust_limit: float


def snapshot_holders(
    issuer: str,
    currency: str,
    ledger_index: int | str = "validated",
    min_balance: float = 0.0,
) -> list[HolderPosition]:
    """
    Get all holders of issuer/currency at a specific ledger.
    Uses marker-based pagination to handle large holder counts.
    """
    holders = []
    marker = None

    while True:
        req = AccountLines(
            account=issuer,
            ledger_index=ledger_index,
            limit=400,  # Max per page
        )
        if marker:
            req.marker = marker

        resp = client.request(req)
        if not resp.is_successful():
            raise RuntimeError(f"AccountLines error: {resp.result}")

        for line in resp.result.get("lines", []):
            if line["currency"] != currency:
                continue
            # From issuer's perspective, positive balance = issuer owes holder
            # balance is negative from issuer's view (it's a liability)
            bal = float(line["balance"])
            # Issuer sees negative balance; absolute value = tokens in circulation
            holder_bal = abs(bal) if bal < 0 else bal
            if holder_bal >= min_balance:
                holders.append(HolderPosition(
                    address=line["account"],
                    balance=holder_bal,
                    trust_limit=float(line["limit_peer"]),
                ))

        marker = resp.result.get("marker")
        if not marker:
            break

    return holders


def proportional_airdrop(
    holders: list[HolderPosition],
    total_airdrop: float,
    airdrop_currency: str,
) -> list[dict]:
    """
    Calculate airdrop amounts proportional to current holdings.
    Returns list of {address, amount} ready for batch_issue_tokens.
    """
    total_held = sum(h.balance for h in holders)
    if total_held == 0:
        return []

    recipients = []
    for h in holders:
        share = h.balance / total_held
        amount = round(total_airdrop * share, 6)
        if amount > 0:
            recipients.append({
                "address": h.address,
                "amount": str(amount),
                "share_pct": share * 100,
            })

    return recipients


# Full workflow example
holders = snapshot_holders(
    issuer="rIssuer...",
    currency="TOKEN",
    ledger_index=12345678,   # Historical snapshot
    min_balance=100.0,       # Exclude dust holders
)
print(f"Snapshot: {len(holders)} eligible holders")

airdrop_plan = proportional_airdrop(holders, total_airdrop=1_000_000, airdrop_currency="REWARD")

# Verify trust lines exist before sending
# (holders must have REWARD trust line or payment fails)
def filter_trusted(
    client, recipients: list[dict], currency: str, issuer_addr: str
) -> tuple[list, list]:
    trusted, no_trust = [], []
    for r in recipients:
        lines = client.request(AccountLines(account=r["address"]))
        has_trust = any(
            l["currency"] == currency and l["account"] == issuer_addr
            for l in lines.result.get("lines", [])
        )
        (trusted if has_trust else no_trust).append(r)
    return trusted, no_trust

trusted, no_trust = filter_trusted(client, airdrop_plan, "REWARD", issuer.classic_address)
print(f"Ready to airdrop: {len(trusted)}, missing trust lines: {len(no_trust)}")
```

---

## Circulating Supply & Burned Supply Tracking

```python
def token_metrics(client, issuer_addr: str, currency: str) -> dict:
    """
    Returns circulating supply, number of holders, and burned amount.
    Burned = issued - still in circulation (payments back to issuer "burn").
    """
    holders = snapshot_holders(issuer_addr, currency)
    circulating = sum(h.balance for h in holders)
    holder_count = len(holders)

    # Check issuer's own account for any "burn" balance
    # (when tokens are sent back to issuer they are retired/burned)
    acc_info = client.request(
        xrpl.models.requests.AccountInfo(account=issuer_addr, ledger_index="validated")
    )
    # Transfer fee revenue accumulates as positive balance on issuer's side
    # It's not circulating — it's issuer-owned revenue
    fee_revenue = 0.0
    for line in holders:
        pass  # Already counted above from holder perspective

    return {
        "currency": currency,
        "issuer": issuer_addr,
        "circulating_supply": circulating,
        "holder_count": holder_count,
        "ledger": "validated",
    }
```

---

## TransferRate (Fee) Revenue Collection

```python
# TransferRate encodes as: (1 + fee%) * 10^9
# 1% fee = 1_010_000_000
# 0.5% fee = 1_005_000_000
# 0.1% fee = 1_001_000_000
# 0% fee = 1_000_000_000 (or leave unset)

from xrpl.models.transactions import AccountSet

set_fee = AccountSet(
    account=issuer.classic_address,
    transfer_rate=1_005_000_000,  # 0.5% fee on all transfers
)
resp = submit_and_wait(set_fee, client, issuer)
```

When a transfer occurs, the fee stays on the issuer's trust line as a positive balance. Collect it via a Payment back to your treasury:

```python
# Sweep collected TransferFee revenue
# From issuer's perspective: positive balance on their own trust line
def sweep_fee_revenue(client, issuer, currency, treasury_addr):
    """Send accumulated fee revenue to treasury."""
    # Get issuer's self-balance (fee income)
    lines = client.request(AccountLines(account=issuer.classic_address))
    fee_income = 0.0
    for line in lines.result.get("lines", []):
        if line["currency"] == currency and float(line["balance"]) > 0:
            fee_income += float(line["balance"])

    if fee_income < 1.0:
        return None  # Not worth sweeping

    sweep = Payment(
        account=issuer.classic_address,
        destination=treasury_addr,
        amount=IssuedCurrencyAmount(
            currency=currency,
            issuer=issuer.classic_address,
            value=str(fee_income),
        ),
        # tfNoRippleDirect prevents path-finding issues
        flags=0x00010000,
    )
    return submit_and_wait(sweep, client, issuer)
```

---

## Global Freeze & Individual Freeze

```python
from xrpl.models.transactions.account_set import AccountSetFlag

# GLOBAL FREEZE: freezes ALL trust lines for this issuer's token
# No transfers possible until thawed; DEX offers cancelled
freeze_all = AccountSet(
    account=issuer.classic_address,
    set_flag=AccountSetFlag.ASF_GLOBAL_FREEZE,
)
resp = submit_and_wait(freeze_all, client, issuer)

# THAW (after remediation)
thaw_all = AccountSet(
    account=issuer.classic_address,
    clear_flag=AccountSetFlag.ASF_GLOBAL_FREEZE,
)
resp = submit_and_wait(thaw_all, client, issuer)


# INDIVIDUAL FREEZE: freeze one specific holder's trust line
def freeze_holder(client, issuer, holder_addr: str, currency: str):
    freeze_tx = TrustSet(
        account=issuer.classic_address,
        limit_amount=IssuedCurrencyAmount(
            currency=currency,
            issuer=holder_addr,   # When issuer sets TrustSet, it targets the holder
            value="0",            # Limit doesn't matter for freeze
        ),
        flags=0x00100000,  # tfSetFreeze
    )
    return submit_and_wait(freeze_tx, client, issuer)


def unfreeze_holder(client, issuer, holder_addr: str, currency: str):
    unfreeze_tx = TrustSet(
        account=issuer.classic_address,
        limit_amount=IssuedCurrencyAmount(
            currency=currency,
            issuer=holder_addr,
            value="0",
        ),
        flags=0x00200000,  # tfClearFreeze
    )
    return submit_and_wait(unfreeze_tx, client, issuer)
```

---

## Multi-Currency Issuer Pattern

```python
# One issuer can issue multiple currencies
CURRENCIES = ["USDC", "EURC", "GBPC", "BTCR"]

# Currency codes:
# 3-char ASCII: "USD", "EUR", "GBP"
# Custom ASCII (up to 20 chars, right-padded with 0x00): convert to 40-char hex
# Full hex code: 40 hex chars starting with 0x00 for non-standard

def currency_to_hex(code: str) -> str:
    """Convert a currency code to the 40-char hex format XRPL uses internally."""
    if len(code) == 3 and code.isalpha():
        return code  # Standard 3-letter code, used as-is
    # Pad to 20 bytes
    encoded = code.encode("ascii")[:20]
    padded = encoded.ljust(20, b"\x00")
    return padded.hex().upper()

# Issue USDC
issue_usdc = Payment(
    account=issuer.classic_address,
    destination=holder.classic_address,
    amount=IssuedCurrencyAmount(
        currency="USDC",
        issuer=issuer.classic_address,
        value="10000",
    ),
)

# Issue with hex code (non-standard)
issue_hex = Payment(
    account=issuer.classic_address,
    destination=holder.classic_address,
    amount=IssuedCurrencyAmount(
        currency="544F4B454E000000000000000000000000000000",  # "TOKEN" padded (16 chars → 40 hex)
        issuer=issuer.classic_address,
        value="5000",
    ),
)
```

---

## DEX Offer for Initial Liquidity

After issuing tokens, create initial DEX buy orders to establish price discovery:

```python
from xrpl.models.transactions import OfferCreate
from xrpl.models.transactions.offer_create import OfferCreateFlag

# Sell 100,000 TOKEN for 1,000 XRP → price = 0.01 XRP per TOKEN
initial_offer = OfferCreate(
    account=issuer.classic_address,
    taker_gets=IssuedCurrencyAmount(
        currency="TOKEN",
        issuer=issuer.classic_address,
        value="100000",
    ),
    taker_pays=xrpl.utils.xrp_to_drops("1000"),
    flags=OfferCreateFlag.TF_SELL,  # Sell order
)
resp = submit_and_wait(initial_offer, client, issuer)

# Buy side: purchase 50,000 TOKEN for up to 600 XRP
buy_offer = OfferCreate(
    account=market_maker.classic_address,
    taker_gets=xrpl.utils.xrp_to_drops("600"),
    taker_pays=IssuedCurrencyAmount(
        currency="TOKEN",
        issuer=issuer.classic_address,
        value="50000",
    ),
)
resp = submit_and_wait(buy_offer, client, market_maker)
```

---

## Error Recovery in Batch Operations

```python
RETRYABLE_ERRORS = {
    "tefPAST_SEQ",      # Sequence too low — refetch
    "tefMAX_LEDGER",    # LastLedgerSequence exceeded — resubmit
    "telCAN_NOT_QUEUE", # Temporarily full queue
    "tooBusy",          # Node overloaded — rotate endpoint
}

def robust_issue(client, issuer, recipient, amount, currency, max_retries=3):
    for attempt in range(max_retries):
        try:
            acc = client.request(AccountInfo(account=issuer.classic_address, ledger_index="current"))
            seq = acc.result["account_data"]["Sequence"]
            tx = Payment(
                account=issuer.classic_address,
                destination=recipient,
                amount=IssuedCurrencyAmount(
                    currency=currency,
                    issuer=issuer.classic_address,
                    value=str(amount),
                ),
                sequence=seq,
                last_ledger_sequence=seq + 20,  # 20-ledger window ≈ 80s
                fee="12",
            )
            resp = submit_and_wait(tx, client, issuer)
            result = resp.result["meta"]["TransactionResult"]
            if result == "tesSUCCESS":
                return True, resp
            elif result in RETRYABLE_ERRORS:
                print(f"Retry {attempt+1}/{max_retries}: {result}")
                import time; time.sleep(4)
            else:
                return False, resp  # Non-retryable failure
        except Exception as e:
            print(f"Exception on attempt {attempt+1}: {e}")
            import time; time.sleep(4)
    return False, None
```

---

## Related Files
- `knowledge/22-xrpl-token-issuance.md` — initial issuance guide
- `knowledge/07-xrpl-clawback.md` — clawback use cases
- `knowledge/03-xrpl-trustlines.md` — trust line mechanics
- `knowledge/13-xrpl-tickets.md` — ticket sequence system
- `knowledge/39-xrpl-nft-ops.md` — NFT-specific minting operations
