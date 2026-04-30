# Token Launch Flow

End-to-end process for launching an issued currency (IOU) on XRPL — from issuer configuration through distribution.

## Overview

```
AccountSet (DefaultRipple + domain + tickSize + transferRate)
  → TrustSet (market maker / distributor sets trust)
    → Payment (issuer mints to distributor)
      → OfferCreate (distributor lists on DEX)
        → Payment (end users receive via DEX or direct)
```

---

## Step 1 — Configure Issuer Account

Set all parameters **before** minting any supply. Parameters cannot be changed once significant supply is in circulation without breaking existing trust lines.

```python
from xrpl.models.transactions import AccountSet, AccountSetAsfFlag

# Enable DefaultRipple so trust lines can ripple through
tx_defaultripple = AccountSet(
    account="rISSUER",
    set_flag=AccountSetAsfFlag.ASF_DEFAULT_RIPPLE,  # flag 8
)

# Set domain (verifies issuer identity via TOML)
tx_domain = AccountSet(
    account="rISSUER",
    domain="7878726c2e6578616d706c652e636f6d",  # hex-encoded "xxrl.example.com"
)

# Set tick size (1–15, controls DEX price precision)
tx_ticksize = AccountSet(account="rISSUER", tick_size=5)

# Set transfer rate (0 = no fee, 1005000000 = 0.5% fee)
# transferRate: 1000000000 (no fee) to 2000000000 (100% fee)
tx_transferrate = AccountSet(account="rISSUER", transfer_rate=1005000000)
```

```bash
# Verify domain via xrpl.toml at: https://yourdomain.com/.well-known/xrp-ledger.toml
# Required fields: [ACCOUNTS], [[CURRENCIES]]
```

---

## Step 2 — Set Up xrpl.toml

At `https://yourdomain.com/.well-known/xrp-ledger.toml`:

```toml
[[ACCOUNTS]]
address = "rISSUER"
desc = "Token issuer hot wallet"

[[CURRENCIES]]
code = "USD"
issuer = "rISSUER"
display_decimals = 2
name = "Example USD"
desc = "USD-pegged stablecoin"
is_asset_backed = true
```

Verify with:
```bash
python3 scripts/xrpl_tools.py account rISSUER
# Check Domain field in account_data
```

---

## Step 3 — Distributor Sets Trust Line

The distributor (or market maker) must set a trust line before the issuer can send tokens:

```bash
python3 scripts/xrpl_tools.py build-trustset \
  --from rDISTRIBUTOR \
  --currency USD \
  --issuer rISSUER \
  --value 1000000000
```

```python
from xrpl.models.transactions import TrustSet
from xrpl.models.amounts import IssuedCurrencyAmount

tx = TrustSet(
    account="rDISTRIBUTOR",
    limit_amount=IssuedCurrencyAmount(currency="USD", issuer="rISSUER", value="1000000000"),
)
```

---

## Step 4 — Issuer Mints to Distributor

The issuer sends tokens to the distributor. This "mints" them (XRPL has no separate mint TX):

```bash
python3 scripts/xrpl_tools.py build-payment \
  --from rISSUER \
  --to rDISTRIBUTOR \
  --amount USD:rISSUER:500000 \
  --cur USD
```

```python
from xrpl.models.transactions import Payment
from xrpl.models.amounts import IssuedCurrencyAmount

tx = Payment(
    account="rISSUER",
    destination="rDISTRIBUTOR",
    amount=IssuedCurrencyAmount(currency="USD", issuer="rISSUER", value="500000"),
)
```

**Verify mint:**
```bash
python3 scripts/xrpl_tools.py trustlines rDISTRIBUTOR USD
```

---

## Step 5 — List on DEX (Optional)

Distributor creates an offer to sell tokens for XRP:

```bash
python3 scripts/xrpl_tools.py build-offer \
  --from rDISTRIBUTOR \
  --sell USD:rISSUER:1000 \
  --buy XRP:2000000000
```

Check the order book:
```bash
python3 scripts/xrpl_tools.py book-offers USD:rISSUER XRP
```

---

## Step 6 — End-User Distribution

**Direct (trust line required on recipient):**

```bash
# Recipient sets trust first
python3 scripts/xrpl_tools.py build-trustset \
  --from rUSER \
  --currency USD \
  --issuer rISSUER \
  --value 100000

# Then distributor sends
python3 scripts/xrpl_tools.py build-payment \
  --from rDISTRIBUTOR \
  --to rUSER \
  --amount USD:rISSUER:1000
```

**Via DEX (no prior trust line needed if using tfNoRippleDirect path):**

```bash
python3 scripts/xrpl_tools.py path-find rUSER rDISTRIBUTOR 1000 USD:rISSUER
python3 scripts/xrpl_tools.py build-cross-currency-payment \
  --from rUSER \
  --to rUSER \
  --deliver USD:rISSUER:100 \
  --send-max XRP:500000
```

---

## Verification Checklist

```bash
# 1. Issuer flags
python3 scripts/xrpl_tools.py account rISSUER
# Flags should include: lsfDefaultRipple, Domain set, TransferRate set

# 2. Total supply
python3 scripts/xrpl_tools.py trustlines rISSUER USD
# Sum of all positive balances = total in circulation

# 3. DEX liquidity
python3 scripts/xrpl_tools.py book-offers USD:rISSUER XRP

# 4. xrpl.toml reachable
curl https://yourdomain.com/.well-known/xrp-ledger.toml
```

---

## Common Mistakes

| Mistake | Fix |
|---|---|
| DefaultRipple not set before minting | Set it first — else trust lines won't ripple |
| Domain not verified in xrpl.toml | XUMM/Xaman will show "Unknown issuer" warning |
| TickSize changed after offers exist | Cancel all offers before changing tick size |
| TransferRate too high | 0.5% (1005000000) is typical max for mass adoption |
| No trust line on recipient | Recipient must set TrustSet before receiving tokens |
| Issuer holds own token | Issuer's balance is always 0 — tokens exist on trust lines |
