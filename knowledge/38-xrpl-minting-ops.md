# Advanced Token Minting Operations

## Token Architecture Overview

Before minting, choose the right token type:

| Type | Standard | Reserve model | Best For |
|------|----------|---------------|---------|
| IOU (Trust Line) | Native | Trust-line ownership; query live incremental reserve | Stablecoins, rewards, complex permissions |
| NFToken | XLS-20 | NFTokenPage ownership; query live incremental reserve | Unique digital items, collectibles |
| MPToken | XLS-33 | Amendment-specific issuance/holder objects; query live state | High-volume tokens, regulated assets |

---

## IOU Issuance: Complete Setup

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## Batch Minting with Tickets (High-Throughput)

The XRPL normally requires sequential `Sequence` numbers. Tickets let you pre-allocate a block and submit transactions in any order — essential for batch operations.

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


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
    currency="TKN",
    ledger_index=12345678,   # Historical snapshot
    min_balance=100.0,       # Exclude dust holders
)
print(f"Snapshot: {len(holders)} eligible holders")

airdrop_plan = proportional_airdrop(holders, total_airdrop=1_000_000, airdrop_currency="RWD")

# Verify trust lines exist before sending
# (holders must have a RWD trust line or payment fails)
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

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


When a transfer occurs, the fee stays on the issuer's trust line as a positive balance. Collect it via a Payment back to your treasury:

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## Global Freeze & Individual Freeze

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


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

# Issue USDC — "USDC" is 4 chars, so it must go through currency_to_hex()
issue_usdc = Payment(
    account=issuer.classic_address,
    destination=holder.classic_address,
    amount=IssuedCurrencyAmount(
        currency=currency_to_hex("USDC"),  # 5553444300000000000000000000000000000000
        issuer=issuer.classic_address,
        value="10000",
    ),
)

# Issue with hex code (non-standard)
issue_hex = Payment(
    account=issuer.classic_address,
    destination=holder.classic_address,
    amount=IssuedCurrencyAmount(
        currency="544F4B454E000000000000000000000000000000",  # "TOKEN" (5 ASCII bytes, zero-padded to 20 bytes / 40 hex)
        issuer=issuer.classic_address,
        value="5000",
    ),
)
```

---

## DEX Offer for Initial Liquidity

After issuing tokens, create initial DEX buy orders to establish price discovery:

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## Error Recovery in Batch Operations

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## Related Files
- `knowledge/22-xrpl-token-issuance.md` — initial issuance guide
- `knowledge/07-xrpl-clawback.md` — clawback use cases
- `knowledge/03-xrpl-trustlines.md` — trust line mechanics
- `knowledge/13-xrpl-tickets.md` — ticket sequence system
- `knowledge/39-xrpl-nft-ops.md` — NFT-specific minting operations
