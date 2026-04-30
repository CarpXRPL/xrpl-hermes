# XRPL Transaction Costs

## Overview

Every XRPL transaction requires a fee (destroyed, not redistributed) and every account object increases the reserve requirement. Understanding both is essential for accurate balance checks and avoiding failed transactions.

---

## 1. Transaction Fees

### Base Fee

```
Base fee: 10 drops (0.00001 XRP)
```

The minimum fee is **10 drops** under normal network load. Fees are **burned** permanently — not paid to validators.

```python
# Convert between XRP and drops
DROPS_PER_XRP = 1_000_000

def xrp_to_drops(xrp: float) -> int:
    return int(xrp * DROPS_PER_XRP)

def drops_to_xrp(drops: int) -> float:
    return drops / DROPS_PER_XRP

base_fee_drops = 10
base_fee_xrp = drops_to_xrp(10)  # 0.00001 XRP
```

### Special Fee Rules

| Transaction Type | Minimum Fee |
|-----------------|-------------|
| Most transactions | 10 drops |
| AccountDelete | 2,000,000 drops (2 XRP) |
| EscrowFinish with condition | 10 + (33 × fulfillment_bytes / 16) drops |
| Multi-signed | 10 × (N_signers + 1) drops |
| TicketCreate (N tickets) | 10 drops (flat, not per ticket) |
| PaymentChannelCreate | 10 drops |

---

## 2. Fee Escalation

During high network load, the required fee increases exponentially:

```
fee_level = reference_fee_level = 256 (normal)
fee = (base_fee × fee_level) / 256

# Escalated example:
fee_level = 5120  (20× congestion)
fee = (10 × 5120) / 256 = 200 drops
```

Formula from rippled source:

```python
def calculate_escalated_fee(
    base_fee: int,
    fee_level: int,
    ref_fee_level: int = 256
) -> int:
    """
    fee_level comes from server_info.load_factor
    """
    return (base_fee * fee_level + ref_fee_level - 1) // ref_fee_level

# Query current escalated fee
def get_current_fee(client) -> int:
    from xrpl.models.requests import Fee
    resp = client.request(Fee())
    return int(resp.result["drops"]["open_ledger_fee"])
```

### Checking Fee from Server

```python
from xrpl.models.requests import Fee

resp = client.request(Fee())
print(f"Base fee: {resp.result['drops']['base_fee']} drops")
print(f"Open ledger fee: {resp.result['drops']['open_ledger_fee']} drops")
print(f"Median fee: {resp.result['drops']['median_fee']} drops")
print(f"Minimum fee: {resp.result['drops']['minimum_fee']} drops")

# Use open_ledger_fee for immediate inclusion
# Use median_fee for batching later
```

### Fee Cushion Strategy

```python
def safe_fee(client, multiplier: float = 1.2) -> str:
    """Add 20% cushion to open ledger fee."""
    resp = client.request(Fee())
    base = int(resp.result["drops"]["open_ledger_fee"])
    return str(max(10, int(base * multiplier)))
```

---

## 3. Account Reserve

Every XRPL account must hold a minimum XRP balance to exist on-ledger. This is the **base reserve** plus an **owner reserve** per ledger object.

### Current Values (as of 2025)

```
Base reserve:  1 XRP (1,000,000 drops)
Owner reserve:  0.2 XRP  (200,000 drops) per object

Total required = 1 XRP + (owner_count × 0.2 XRP)
```

> **Important:** Reserve values can change via validator voting; always query `server_info` → `validated_ledger.reserve_base_xrp` for live values.

### Objects That Consume Reserve

| Object | Reserve Cost |
|--------|-------------|
| Trust line | 0.2 XRP |
| DEX Offer | 0.2 XRP |
| Escrow | 0.2 XRP |
| Payment Channel | 0.2 XRP |
| Signer List | 0.2 XRP |
| NFT page (up to 32 NFTs) | 0.2 XRP |
| Ticket | 0.2 XRP |
| AMM LP token trust line | 0.2 XRP |
| Check | 0.2 XRP |
| DepositPreauth | 0.2 XRP |
| DID | 0.2 XRP |

### Computing Required Reserve

```python
def compute_reserve(owner_count: int) -> int:
    """Returns minimum required balance in drops. Always fetch live values from server_info."""
    BASE_RESERVE = 1_000_000    # 1 XRP (as of 2025 — verify with server_info)
    OWNER_RESERVE = 200_000     # 0.2 XRP per object
    return BASE_RESERVE + (owner_count * OWNER_RESERVE)

# Check if account can afford new object
def can_afford_object(balance: int, owner_count: int) -> bool:
    required = compute_reserve(owner_count + 1)  # after adding object
    return balance >= required

# Example
balance_drops = 2_000_000    # 2 XRP
owner_count = 2              # 2 existing objects
current_reserve = compute_reserve(owner_count)  # 1.4 XRP
print(f"Spendable: {balance_drops - current_reserve} drops")  # 0.6 XRP
```

### Querying from Ledger

```python
from xrpl.models.requests import AccountInfo, ServerInfo

# Get owner count
resp = client.request(AccountInfo(account="rN7n...", ledger_index="validated"))
acct = resp.result["account_data"]
owner_count = acct["OwnerCount"]
balance = int(acct["Balance"])

# Get reserve values from server
server_resp = client.request(ServerInfo())
server_info = server_resp.result["info"]["validated_ledger"]
base_reserve = int(float(server_info["reserve_base_xrp"]) * 1_000_000)
owner_reserve = int(float(server_info["reserve_inc_xrp"]) * 1_000_000)

total_reserve = base_reserve + (owner_count * owner_reserve)
spendable = balance - total_reserve
print(f"Balance: {balance / 1e6:.6f} XRP")
print(f"Reserve locked: {total_reserve / 1e6:.6f} XRP")
print(f"Spendable: {spendable / 1e6:.6f} XRP")
```

---

## 4. Maximum Object Count

An account can hold at most **4,294,967,295** objects technically, but practical limits are:
- Each object locks 0.2 XRP
- At 250 objects: 1 + 50 = 51 XRP locked as reserve
- At 1000 objects: 1 + 200 = 201 XRP locked

### NFT Exception

NFTs are packed into **NFTokenPage** objects:
- Each NFTokenPage holds up to 32 NFTs
- Only 1 owner reserve per page (not per NFT)
- 32 NFTs = 1 page = 2 XRP reserve

```python
def nft_reserve(nft_count: int) -> int:
    """Owner reserve for NFTs in drops."""
    pages = (nft_count + 31) // 32  # ceiling division
    return pages * 2_000_000
```

---

## 5. Reserve Optimization

### Remove Unnecessary Trust Lines

```json
{
  "TransactionType": "TrustSet",
  "Account": "rN7n...",
  "LimitAmount": {
    "currency": "USD",
    "issuer": "rISSUER...",
    "value": "0"
  },
  "Fee": "12",
  "Sequence": 10
}
```

Trust line is removed only if:
- Limit is 0
- Balance is 0
- No outstanding offers in that asset

### Cancel Stale Offers

```python
# Get all offers
from xrpl.models.requests import AccountObjects

resp = client.request(AccountObjects(
    account="rN7n...",
    type="offer"
))

# Cancel them
for offer in resp.result["account_objects"]:
    cancel_tx = {
        "TransactionType": "OfferCancel",
        "Account": "rN7n...",
        "OfferSequence": offer["Sequence"],
        "Fee": "12",
        "Sequence": get_sequence()
    }
    submit(cancel_tx)
```

### Account Deletion (2 XRP fee)

Requirements for account deletion — **all must be met**:
- Account Sequence ≥ 256 (or current ledger index - 256, whichever is higher)
- Owner count = 0 (all trust lines, offers, escrows, etc. must be removed first)
- Destination account exists and is different from sender
- If the destination requires a `DestinationTag` (lsfRequireDestTag flag), you **must** include one

```json
{
  "TransactionType": "AccountDelete",
  "Account": "rOLD...",
  "Destination": "rNEW...",
  "DestinationTag": 0,
  "Fee": "2000000",
  "Sequence": 300
}
```

> **Note:** AccountDelete does **not** unconditionally return all XRP. The remaining balance (total XRP minus the 2 XRP fee) is sent to the destination only if **all** requirements above are satisfied. Failure to meet any condition results in `tecNO_DST`, `tecTOO_SOON`, or `tecHAS_OBLIGATIONS`.

---

## 6. Fee Voting Changes

Validators can vote to change reserve values. Process:

1. Validator sets fee vote in config:
```ini
[voting]
account_reserve = 1000000    # 1 XRP (current mainnet as of 2025)
owner_reserve = 200000       # 0.2 XRP
fee_default = 10             # drops
```

2. Network median becomes new value after enough validators agree
3. Changes take effect in next ledger

Current values are unlikely to change without broad validator consensus.

---

## 7. Cost Summary Table

```
Action                          XRP Cost
─────────────────────────────────────────
Send XRP                        0.00001 XRP fee
Send token                      0.00001 XRP fee
Create trust line               0.00001 fee + 2 XRP reserve
Create DEX offer                0.00001 fee + 2 XRP reserve
Cancel DEX offer                0.00001 fee, -2 XRP reserve returned
Mint NFT (first, new page)      0.00001 fee + 2 XRP reserve
Mint NFT (same page)            0.00001 fee (no extra reserve)
Create escrow                   0.00001 fee + 2 XRP reserve
Finish escrow                   0.00001+ fee, -2 XRP reserve returned
Open payment channel            0.00001 fee + 2 XRP reserve + funded amount
Create ticket                   0.00001 fee + 2 XRP/ticket reserve
Delete account                  2.0000 XRP fee, all reserve returned
Set signer list (5 signers)     0.00001 fee + 2 XRP reserve
AccountSet                      0.00001 XRP fee (no reserve)
```

---

## 8. Production Fee Recommendation

```python
async def get_recommended_fee(client, safety_margin: float = 1.5) -> str:
    """
    For immediate inclusion: use open_ledger_fee × 1.5
    For queued (next few ledgers): use median_fee
    """
    resp = await client.request(Fee())
    drops = resp.result["drops"]
    
    open_fee = int(drops["open_ledger_fee"])
    median_fee = int(drops["median_fee"])
    
    immediate_fee = max(10, int(open_fee * safety_margin))
    return str(immediate_fee)
```
