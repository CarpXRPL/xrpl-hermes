# Clawback Flow

Issuer reclaims tokens from a holder. XRPL requires `lsfAllowTrustLineClawback` enabled on the issuer account before any clawback can occur.

## Prerequisites

- Issuer account must have `lsfAllowTrustLineClawback` set (AccountSet, `asfAllowTrustLineClawback = 16`).
- This flag cannot be unset once enabled — verify intent before proceeding.
- Clawback is only valid for issued tokens (IOUs), not XRP.

---

## Step 1 — Verify Issuer Has Clawback Enabled

```bash
python3 scripts/xrpl_tools.py account rISSUER_ADDRESS
# Look for: "lsfAllowTrustLineClawback" in Flags bitmask
```

```python
import xrpl
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountInfo

client = JsonRpcClient("https://xrplcluster.com")
resp = client.request(AccountInfo(account="rISSUER", ledger_index="validated"))
flags = resp.result["account_data"]["Flags"]
CLAWBACK_FLAG = 0x80000000  # lsfAllowTrustLineClawback
print("Clawback enabled:", bool(flags & CLAWBACK_FLAG))
```

**If not enabled:** Build an AccountSet transaction to enable it first:

```bash
python3 scripts/xrpl_tools.py build-payment --from rISSUER --to rISSUER --amount 0
# Actually use AccountSet:
python3 -c "
import json
from xrpl.models.transactions import AccountSet
tx = AccountSet(account='rISSUER', set_flag=16)  # 16 = asfAllowTrustLineClawback
print(json.dumps(tx.to_xrpl(), indent=2))
"
```

---

## Step 2 — Check Holder Balance

Before clawing back, verify the holder actually holds the token and their balance:

```bash
python3 scripts/xrpl_tools.py trustlines rHOLDER_ADDRESS USD
```

```python
from xrpl.models.requests import AccountLines
resp = client.request(AccountLines(account="rHOLDER", ledger_index="validated"))
for line in resp.result.get("lines", []):
    if line["account"] == "rISSUER" and line["currency"] == "USD":
        print(f"Balance: {line['balance']} USD")
        print(f"Limit: {line['limit']}")
```

**Common mistake:** The `balance` field is from the holder's perspective — a positive balance means the holder has tokens.

---

## Step 3 — Build the Clawback Transaction

```bash
python3 scripts/xrpl_tools.py build-clawback \
  --from rISSUER \
  --destination rHOLDER \
  --currency USD \
  --issuer rISSUER \
  --amount 100 \
  --memo "compliance-clawback-2025-01"
```

Expected output:
```json
{
  "Account": "rISSUER",
  "TransactionType": "Clawback",
  "Amount": {
    "currency": "USD",
    "issuer": "rHOLDER",
    "value": "100"
  }
}
```

**Note:** In the Clawback TX, `Amount.issuer` is the **holder** address (not the issuer). This is the XRPL protocol requirement — it identifies which trust line to clawback from.

---

## Step 4 — Sign and Submit

Sign with Xaman, Crossmark, or xrpl-py wallet:

```python
from xrpl.wallet import Wallet
from xrpl.transaction import submit_and_wait
from xrpl.models.transactions import Clawback
from xrpl.models.amounts import IssuedCurrencyAmount

issuer_wallet = Wallet.from_seed("sISSUER_SEED")
tx = Clawback(
    account=issuer_wallet.classic_address,
    amount=IssuedCurrencyAmount(currency="USD", issuer="rHOLDER", value="100"),
)
result = submit_and_wait(tx, client, issuer_wallet)
print(result.result["meta"]["TransactionResult"])  # tesSUCCESS
```

---

## Step 5 — Verify the Clawback

```bash
python3 scripts/xrpl_tools.py trustlines rHOLDER_ADDRESS USD
# Balance should be reduced by 100
```

```python
resp = client.request(AccountLines(account="rHOLDER", ledger_index="validated"))
for line in resp.result.get("lines", []):
    if line["account"] == "rISSUER" and line["currency"] == "USD":
        print(f"New balance: {line['balance']}")
```

---

## Common Mistakes

| Mistake | Fix |
|---|---|
| Clawback on XRP | Not possible — IOUs only |
| `Amount.issuer` set to issuer, not holder | Must be holder address |
| Flag not enabled before clawback | Enable `asfAllowTrustLineClawback` first |
| Clawing back more than holder's balance | Amount must be ≤ holder's positive balance |
| Calling clawback from holder account | Must be signed by issuer |

---

## Compliance Notes

- Log each clawback event with: timestamp, holder address, amount, reason code.
- Clawback is irreversible on-ledger — verify amounts and addresses before signing.
- For RLUSD, compliance clawback requires Ripple's authorization layer (see `knowledge/58-rlusd-operations.md`).
