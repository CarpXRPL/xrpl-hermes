# XRPL Token Issuance: Step by Step

## Overview

Complete guide to issuing a fungible token on the XRPL mainnet. Covers wallet setup, issuer configuration, trust line setup, token distribution, AMM creation, and optional blackholing.

---

## 1. Architecture

```
    [ISSUER WALLET]           [DISTRIBUTION WALLET]
    - AccountSet flags         - Hold initial supply
    - Sets DefaultRipple       - Create DEX offers
    - Sets TransferRate        - Manage liquidity
    - Issues to distributor
    - (Optionally blackholed)
```

Keep issuer and distributor separate. The issuer is a cold wallet; the distributor is the hot operational wallet.

---

## 2. Fund Wallets

```python
from xrpl.wallet import Wallet
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import Payment
from xrpl.transaction import autofill_and_sign, submit_and_wait

client = JsonRpcClient("https://xrplcluster.com")

# Load wallets from environment variables (NEVER hardcode seeds)
import os

issuer_seed = os.environ.get("ISSUER_SEED")
distributor_seed = os.environ.get("DISTRIBUTOR_SEED")

if not issuer_seed or not distributor_seed:
    raise EnvironmentError("Set ISSUER_SEED and DISTRIBUTOR_SEED env vars before running")

issuer_wallet = Wallet.from_seed(issuer_seed)
distributor_wallet = Wallet.from_seed(distributor_seed)

# To generate new wallets offline (first time only):
#   new_wallet = Wallet.create()
#   print(new_wallet.address)   # safe to log
#   # Store new_wallet.seed in a secrets manager, NOT in code or logs

print(f"Issuer: {issuer_wallet.address}")
print(f"Distributor: {distributor_wallet.address}")

# Fund each with at least 25 XRP from an existing funded account
def fund_account(from_wallet: Wallet, to_address: str, xrp_amount: str):
    tx = Payment(
        account=from_wallet.address,
        destination=to_address,
        amount=str(int(float(xrp_amount) * 1_000_000))
    )
    signed = autofill_and_sign(tx, from_wallet, client)
    result = submit_and_wait(signed, client)
    assert result.result["meta"]["TransactionResult"] == "tesSUCCESS"
    print(f"Funded {to_address}")

# fund_account(funder_wallet, issuer_wallet.address, "25")
# fund_account(funder_wallet, distributor_wallet.address, "15")
```

---

## 3. Configure the Issuer Account

```python
from xrpl.models.transactions import AccountSet
from xrpl.models.transactions.account_set import AccountSetAsfFlag
import binascii

CURRENCY = "MYTKN"  # 3-char ISO or 20-char hex currency code
TOKEN_NAME = "My Token"
DOMAIN = "mytoken.com"
TICK_SIZE = 5       # decimal places for DEX (2-8)
TRANSFER_RATE_PCT = 0.5  # 0.5% transfer fee

def encode_domain(domain: str) -> str:
    return binascii.hexlify(domain.encode()).decode().upper()

# Step 3a: Set DefaultRipple (CRITICAL: before any trust lines)
tx_ripple = AccountSet(
    account=issuer_wallet.address,
    set_flag=AccountSetAsfFlag.ASF_DEFAULT_RIPPLE,
    fee="12"
)
signed = autofill_and_sign(tx_ripple, issuer_wallet, client)
result = submit_and_wait(signed, client)
print(f"DefaultRipple: {result.result['meta']['TransactionResult']}")

# Step 3b: Set TickSize
tx_tick = AccountSet(
    account=issuer_wallet.address,
    tick_size=TICK_SIZE,
    fee="12"
)
signed = autofill_and_sign(tx_tick, issuer_wallet, client)
submit_and_wait(signed, client)
print("TickSize set")

# Step 3c: Set Domain
tx_domain = AccountSet(
    account=issuer_wallet.address,
    domain=encode_domain(DOMAIN),
    fee="12"
)
signed = autofill_and_sign(tx_domain, issuer_wallet, client)
submit_and_wait(signed, client)
print("Domain set")

# Step 3d: Set TransferRate (0.5%)
transfer_rate = int((1 + TRANSFER_RATE_PCT / 100) * 1_000_000_000)
tx_rate = AccountSet(
    account=issuer_wallet.address,
    transfer_rate=transfer_rate,
    fee="12"
)
signed = autofill_and_sign(tx_rate, issuer_wallet, client)
submit_and_wait(signed, client)
print(f"TransferRate set to {TRANSFER_RATE_PCT}%")
```

---

## 4. Optional: Require Authorization (KYC)

```python
# Only if you want to manually authorize each trust line
tx_auth = AccountSet(
    account=issuer_wallet.address,
    set_flag=AccountSetAsfFlag.ASF_REQUIRE_AUTH,
    fee="12"
)
signed = autofill_and_sign(tx_auth, issuer_wallet, client)
submit_and_wait(signed, client)
```

---

## 5. Distributor Creates Trust Line

```python
from xrpl.models.transactions import TrustSet

TOTAL_SUPPLY = "1000000000"  # 1 billion tokens

tx_trust = TrustSet(
    account=distributor_wallet.address,
    limit_amount={
        "currency": CURRENCY,
        "issuer": issuer_wallet.address,
        "value": TOTAL_SUPPLY
    },
    fee="12"
)
signed = autofill_and_sign(tx_trust, distributor_wallet, client)
result = submit_and_wait(signed, client)
print(f"Trust line created: {result.result['meta']['TransactionResult']}")
```

If `RequireAuth` is enabled, issuer must authorize first:
```python
tx_authorize = TrustSet(
    account=issuer_wallet.address,
    limit_amount={
        "currency": CURRENCY,
        "issuer": distributor_wallet.address,
        "value": "0"
    },
    flags=0x00010000,  # tfSetfAuth
    fee="12"
)
signed = autofill_and_sign(tx_authorize, issuer_wallet, client)
submit_and_wait(signed, client)
```

---

## 6. Issue Tokens

```python
from xrpl.models.transactions import Payment

# Issuer sends tokens to distributor
tx_issue = Payment(
    account=issuer_wallet.address,
    destination=distributor_wallet.address,
    amount={
        "currency": CURRENCY,
        "issuer": issuer_wallet.address,
        "value": TOTAL_SUPPLY
    },
    fee="12"
)
signed = autofill_and_sign(tx_issue, issuer_wallet, client)
result = submit_and_wait(signed, client)
print(f"Issued {TOTAL_SUPPLY} {CURRENCY}: {result.result['meta']['TransactionResult']}")

# Verify distributor balance
from xrpl.models.requests import AccountLines
resp = client.request(AccountLines(account=distributor_wallet.address))
for line in resp.result["lines"]:
    if line["currency"] == CURRENCY:
        print(f"Distributor balance: {line['balance']} {CURRENCY}")
```

---

## 7. Create AMM Pool

```python
from xrpl.models.transactions import AMMCreate

# Add liquidity: 100 XRP + 1,000,000 MYTKN (initial price: 0.0001 XRP/MYTKN)
tx_amm = AMMCreate(
    account=distributor_wallet.address,
    amount="100000000",  # 100 XRP in drops
    amount2={
        "currency": CURRENCY,
        "issuer": issuer_wallet.address,
        "value": "1000000"  # 1 million tokens
    },
    trading_fee=500,  # 0.5% fee (in 1/100000 units)
    fee="12"
)
signed = autofill_and_sign(tx_amm, distributor_wallet, client)
result = submit_and_wait(signed, client)
print(f"AMM created: {result.result['meta']['TransactionResult']}")

# Get AMM ID
for node in result.result["meta"]["AffectedNodes"]:
    if node.get("CreatedNode", {}).get("LedgerEntryType") == "AMM":
        amm_id = node["CreatedNode"]["NewFields"]["Account"]
        print(f"AMM account: {amm_id}")
```

---

## 8. Create DEX Offers (Optional)

```python
from xrpl.models.transactions import OfferCreate

# Sell 1,000,000 MYTKN for 100 XRP (0.0001 XRP per token)
tx_offer = OfferCreate(
    account=distributor_wallet.address,
    taker_pays="100000000",  # 100 XRP
    taker_gets={
        "currency": CURRENCY,
        "issuer": issuer_wallet.address,
        "value": "1000000"
    },
    fee="12"
)
signed = autofill_and_sign(tx_offer, distributor_wallet, client)
submit_and_wait(signed, client)
```

---

## 9. Blackhole the Issuer

Only after confirming all tokens are issued correctly:

```python
from xrpl.models.transactions import SetRegularKey

BLACK_HOLE = "rrrrrrrrrrrrrrrrrrrrBZbvji"

# Step 9a: Set regular key to black hole address
tx_key = SetRegularKey(
    account=issuer_wallet.address,
    regular_key=BLACK_HOLE,
    fee="12"
)
signed = autofill_and_sign(tx_key, issuer_wallet, client)
submit_and_wait(signed, client)

# Step 9b: Disable master key (now PERMANENTLY inaccessible)
tx_disable = AccountSet(
    account=issuer_wallet.address,
    set_flag=AccountSetAsfFlag.ASF_DISABLE_MASTER,
    fee="12"
)
# Must sign with the regular key (which is now black hole — use master one last time)
signed = autofill_and_sign(tx_disable, issuer_wallet, client)
submit_and_wait(signed, client)

print("Issuer is now blackholed. No more tokens can be minted.")
```

---

## 10. Verify on Explorer

```python
# Verify issuer account flags
from xrpl.models.requests import AccountInfo

resp = client.request(AccountInfo(
    account=issuer_wallet.address,
    ledger_index="validated"
))
acct = resp.result["account_data"]
flags = acct["Flags"]

# Check flags
lsf_default_ripple = 0x00800000
lsf_disable_master = 0x00100000
lsf_no_freeze = 0x00200000

print(f"DefaultRipple: {bool(flags & lsf_default_ripple)}")
print(f"MasterDisabled: {bool(flags & lsf_disable_master)}")
print(f"NoFreeze: {bool(flags & lsf_no_freeze)}")
print(f"TransferRate: {acct.get('TransferRate', 'Not set')}")
print(f"TickSize: {acct.get('TickSize', 'Not set')}")
print(f"Domain: {bytes.fromhex(acct.get('Domain', '')).decode()}")
```

Verify on explorers:
- `https://xrpl.org/explorer/#/{issuer_address}`
- `https://bithomp.com/explorer/{issuer_address}`
- `https://xrpscan.com/account/{issuer_address}`

---

## 11. Register Token Metadata

Submit to XRPLMeta, xrpl.to, and Bithomp:
- Contact each service with: currency code, issuer address, token name, logo, website, social links
- TOML file at `https://yourdomain.com/.well-known/xrp-ledger.toml`

```toml
# .well-known/xrp-ledger.toml
[METADATA]
modified = 2024-01-01

[[ACCOUNTS]]
address = "rISSUER..."
desc = "MYTKN issuer account"

[[CURRENCIES]]
code = "MYTKN"
issuer = "rISSUER..."
display_decimals = 6
name = "My Token"
desc = "The utility token for MyProject"
icon = "https://mytoken.com/icon.png"
```
