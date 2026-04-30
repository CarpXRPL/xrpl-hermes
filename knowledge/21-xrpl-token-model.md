# XRPL Token Model

## Overview

The XRPL supports two primary mechanisms for tokens: **Issued Currency** (the original trust line-based system) and **MPT (Multi-Purpose Tokens)**, a newer compact format. This document covers both, focusing on issued currency which dominates current usage.

---

## 1. Issued Currency Mechanics

Issued currency requires a **trust line** between a token holder and the **issuer** (also called the gateway). The issuer has unlimited ability to mint tokens by crediting trust lines.

### The Trust Line Model

```
    Issuer Account (rISSUER)
         │
         │  [trust line: limit=10000, balance=500, USD]
         │
    Holder Account (rHOLDER)
```

- Holder creates trust line with a limit
- Issuer sends tokens to the holder (increases balance, decreases issuer's "obligations")
- Rippling allows tokens to move through chains of trust lines
- No central ledger — each trust line IS the balance record

### Internal Representation

XRPL stores trust line amounts as:
```
value × 10^exponent  where 1 ≤ value < 10, exponent in [-96, +80]
```

This allows very large and very small amounts, but with 15 significant decimal digits.

---

## 2. Issuer Requirements

For an account to issue tokens:
1. Must be funded (≥ 1 XRP reserve)
2. Should set `DefaultRipple` flag (for rippling between holders)
3. Should set `TickSize` for DEX precision (2–8 decimal places)
4. Optional: set `TransferRate`, `Domain`, `RequireAuth`

```python
from xrpl.models.transactions import AccountSet
from xrpl.models.transactions.account_set import AccountSetAsfFlag

# Enable DefaultRipple (required for token to flow between holders)
tx = AccountSet(
    account="rISSUER...",
    set_flag=AccountSetAsfFlag.ASF_DEFAULT_RIPPLE,
    fee="12",
    sequence=1
)
```

---

## 3. Transfer Fees

Issuers can charge a fee on every transfer of their token:

```
transfer_fee = (TransferRate / 1,000,000,000) - 1

TransferRate range: 1,000,000,000 (0%) to 2,000,000,000 (100%)
```

Examples:
| TransferRate | Effective Fee |
|-------------|--------------|
| 1,000,000,000 | 0% |
| 1,002,000,000 | 0.2% |
| 1,010,000,000 | 1% |
| 1,050,000,000 | 5% |
| 2,000,000,000 | 100% |

```python
def transfer_rate_to_pct(transfer_rate: int) -> float:
    return (transfer_rate / 1_000_000_000 - 1) * 100

def pct_to_transfer_rate(pct: float) -> int:
    return int((1 + pct / 100) * 1_000_000_000)

# Set 0.5% transfer fee
from xrpl.models.transactions import AccountSet

tx = AccountSet(
    account="rISSUER...",
    transfer_rate=1_005_000_000,  # 0.5%
    fee="12",
    sequence=2
)
```

Transfer fee is paid by the **sender**, added on top of the amount received:
```
sender_debited = amount / (1 - fee_pct)
# Example: receiving 100 tokens at 0.5% fee
# sender pays: 100 / 0.995 = 100.5025... tokens
```

---

## 4. Holder Risk and Trust Lines

When you hold tokens, you trust the issuer. The issuer can:
- Freeze your trust line (prevent transfers)
- Clawback tokens (if clawback is enabled)
- Become insolvent and tokens become worthless

Trust line from holder side:

```json
{
  "LedgerEntryType": "RippleState",
  "Account": "rHOLDER...",
  "HighAccount": "rISSUER...",
  "Balance": {
    "currency": "USD",
    "issuer": "rrrrrrrrrrrrrrrrrrrrBZbvji",
    "value": "500"
  },
  "HighLimit": {
    "currency": "USD",
    "issuer": "rISSUER...",
    "value": "0"
  },
  "LowLimit": {
    "currency": "USD",
    "issuer": "rHOLDER...",
    "value": "10000"
  },
  "Flags": 131072
}
```

Flags:
- `lsfLowNoRipple` (0x00040000): No rippling from this side
- `lsfHighNoRipple` (0x00080000): No rippling from issuer side
- `lsfLowFreeze` (0x00400000): Issuer has frozen this line
- `lsfHighFreeze` (0x00800000): Holder has frozen this line
- `lsfLowAuth` (0x00010000): Trust line authorized by issuer

---

## 5. Authorization (RequireAuth)

Issuers with `RequireAuth` enabled must authorize each trust line before tokens can flow:

```python
# Issuer sets RequireAuth
tx = AccountSet(
    account="rISSUER...",
    set_flag=AccountSetAsfFlag.ASF_REQUIRE_AUTH,
    fee="12",
    sequence=3
)

# Holder creates trust line
trust_tx = TrustSet(
    account="rHOLDER...",
    limit_amount={
        "currency": "USD",
        "issuer": "rISSUER...",
        "value": "10000"
    }
)

# Issuer authorizes
auth_tx = TrustSet(
    account="rISSUER...",
    limit_amount={
        "currency": "USD",
        "issuer": "rHOLDER...",
        "value": "0"
    },
    flags=0x00010000  # tfSetfAuth
)
```

---

## 6. Freezing

### Individual Trust Line Freeze

```python
# Issuer freezes one holder
freeze_tx = TrustSet(
    account="rISSUER...",
    limit_amount={
        "currency": "USD",
        "issuer": "rHOLDER...",
        "value": "0"
    },
    flags=0x00100000  # tfSetFreeze
)
```

### Global Freeze (all trust lines)

```python
# Freeze all trust lines for this token
global_freeze = AccountSet(
    account="rISSUER...",
    set_flag=AccountSetAsfFlag.ASF_GLOBAL_FREEZE
)
```

### No Freeze (permanent, irreversible)

```python
# Permanently disable freeze capability
no_freeze = AccountSet(
    account="rISSUER...",
    set_flag=AccountSetAsfFlag.ASF_NO_FREEZE
)
```

---

## 7. Clawback

If the issuer sets `AllowTrustLineClawback`, they can reclaim tokens:

```json
{
  "TransactionType": "Clawback",
  "Account": "rISSUER...",
  "Amount": {
    "currency": "USD",
    "issuer": "rHOLDER...",
    "value": "100"
  },
  "Fee": "12",
  "Sequence": 10
}
```

Note: Enabling clawback disables NoFreeze and global freeze.

---

## 8. Trust Line vs MPT (Multi-Purpose Token)

| Feature | Issued Currency | MPT |
|---------|----------------|-----|
| Storage | Trust line objects | MPT objects |
| Reserve per holder | 2 XRP | Much less |
| Maximum holders | Millions | Millions |
| Fractional amounts | 15 sig digits | Configurable precision |
| Transfer fee | Yes | Yes |
| Freeze | Yes | Yes |
| DEX trading | Yes | Limited (evolving) |
| AMM support | Yes | Evolving |
| Maturity | Production | Amendment (2024+) |

MPT (MPTokensV1 amendment):
```json
{
  "TransactionType": "MPTokenIssuanceCreate",
  "Account": "rISSUER...",
  "AssetScale": 6,
  "MaximumAmount": "1000000000000",
  "TransferFee": 500,
  "Flags": 0
}
```

---

## 9. Blackholing the Issuer

Blackholing makes the issuer account permanently unable to transact, making the token supply truly fixed. Steps:

1. Set regular key to an account nobody controls (e.g., `rrrrrrrrrrrrrrrrrrrrBZbvji`)
2. Disable master key
3. Optionally remove signer list

```python
# Step 1: Set regular key to black hole address
set_key = SetRegularKey(
    account="rISSUER...",
    regular_key="rrrrrrrrrrrrrrrrrrrrBZbvji",  # the "black hole"
    fee="12",
    sequence=99
)

# Step 2: Disable master key
disable_master = AccountSet(
    account="rISSUER...",
    set_flag=AccountSetAsfFlag.ASF_DISABLE_MASTER,
    fee="12",
    sequence=100
)
```

After blackholing: no new tokens can be minted, no trust lines can be frozen or authorized, no clawback possible.

---

## 10. Issuance Checklist

Before issuing tokens on mainnet:

- [ ] Fund issuer wallet with enough XRP (≥ 30 XRP for operations)
- [ ] Set `DefaultRipple` flag
- [ ] Set `TickSize` (recommended: 5)
- [ ] Set `Domain` (hex-encoded domain name)
- [ ] Set `TransferRate` if needed
- [ ] Set `RequireAuth` if KYC required
- [ ] Enable `NoFreeze` if committing to no-freeze
- [ ] Test trust line creation with a test wallet
- [ ] Issue initial token supply to distributing wallet
- [ ] Create AMM or DEX offers for liquidity
- [ ] Register on XRPLMeta / Bithomp / xrpl.to
- [ ] Blackhole issuer if supply should be fixed

---

## 11. Rippling

Rippling allows tokens to flow automatically through shared trust lines. Essential for IOU tokens to trade on DEX without direct trust between counterparties.

```
Alice ←→ Bank (USD trust line)
Bob ←→ Bank (USD trust line)

Alice can pay Bob through Bank without Bob trusting Alice directly.
Bank's trust lines with Alice and Bob "ripple" the payment.
```

Enable rippling on issuer:
```python
# DefaultRipple = rippling enabled for all trust lines
# Must be set BEFORE any trust lines are created for it to apply automatically
```

Disable rippling on individual holder:
```python
trust_tx = TrustSet(
    ...
    flags=0x00020000  # tfSetNoRipple
)
```
