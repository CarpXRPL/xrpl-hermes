# RLUSD Operations — Compliance, Freeze, Clawback, Monitoring

## Overview

RLUSD is Ripple-issued USD stablecoin on the XRP Ledger. It is designed for regulated financial use cases: cross-border payments, treasury operations, and DeFi — with built-in compliance controls via the Clawback amendment and issuer-managed trust lines.

**Key Properties:**
- **Issuer:** Ripple — `rMxCKbEDwqr76QuheSUMdEGf4B9xJ8m5De` (XRPL mainnet, verify against official Ripple announcements)
- **Currency code:** `524C555344000000000000000000000000000000` — "RLUSD" is 5 characters, so the 160-bit hex form is **required** in every transaction and API field. Explorers display it as "RLUSD", but the ledger never accepts the 5-letter literal.
- **Standard:** XRPL issued currency (IOU) with Clawback enabled
- **Supply control:** Issuer can mint/burn and clawback under regulatory requirements
- **Compliance:** Travel rule integration, freeze via clawback, KYC-gated trust lines
- **On-chain visibility:** validated XRPL JSON-RPC/Clio evidence; third-party supply/holder APIs require separate acceptance

---

## Compliance Architecture

### KYC-Gated Trust Lines

RLUSD uses the standard XRPL trust line model with an important compliance twist: the issuer does NOT automatically accept trust lines from arbitrary accounts. Each holder must go through KYC before the issuer sets up the trust line or allows one to be established.

```
User completes KYC (off-chain)
        ↓
Issuer authorizes trust line or user is whitelisted
        ↓
User establishes trust line to RLUSD issuer
        ↓
Issuer sends RLUSD payment to user's account
```

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


### Travel Rule Integration

For transactions over the FATF threshold (typically $1,000–$10,000 depending on jurisdiction), RLUSD payments should include Travel Rule data in transaction memos:

```python
import json, base64
from xrpl.models.transactions import Payment, Memo

def rlusd_payment_with_travel_rule(
    wallet: Wallet,
    destination: str,
    amount: str,
    originator_info: dict,
    beneficiary_info: dict
) -> Payment:
    """Create RLUSD payment with embedded Travel Rule data."""
    tr_payload = {
        "originator": {
            "name": originator_info.get("name"),
            "account": wallet.classic_address,
            "jurisdiction": originator_info.get("jurisdiction")
        },
        "beneficiary": {
            "name": beneficiary_info.get("name"),
            "account": destination,
            "jurisdiction": beneficiary_info.get("jurisdiction")
        },
        "asset": "RLUSD",
        "amount": amount,
        "timestamp": int(__import__("time").time())
    }

    memo_data = base64.b64encode(
        json.dumps(tr_payload).encode()
    ).hex().upper()

    return Payment(
        account=wallet.classic_address,
        destination=destination,
        amount={
            "currency": RLUSD_CUR,
            "issuer": RLUSD_ISSUER,
            "value": amount
        },
        memos=[{
            "Memo": {
                "MemoData": memo_data,
                "MemoType": "54524156454c52554C45",  # "TRAVELRULE"
                "MemoFormat": "6170706C69636174696F6E2F6A736F6E"  # "application/json"
            }
        }]
    )
```

---

## Freeze & Clawback Operations

RLUSD has the Clawback amendment enabled on the issuer account. This gives the issuer the ability to claw back tokens from holders for regulatory compliance (e.g., sanctioned addresses, fraud, legal orders).

### Check if Clawback is Enabled

```python
from xrpl.models.requests import AccountInfo

def has_clawback_enabled(address: str) -> bool:
    """Check if an account has the Clawback flag (lsfAllowTrustLineClawback)."""
    resp = client.request(AccountInfo(
        account=address,
        ledger_index="validated"
    ))
    flags = resp.result["account_data"].get("Flags", 0)
    # lsfAllowTrustLineClawback = 0x80000000 (high 32-bit flag)
    CLAWBACK_FLAG = 0x80000000
    return bool(flags & CLAWBACK_FLAG)

print(f"RLUSD issuer clawback enabled: {has_clawback_enabled(RLUSD_ISSUER)}")
```

### Execute a Clawback

The issuer can claw back RLUSD from a specific holder when required by regulation or legal order:

```bash
# Using the build-clawback tool
python3 scripts/xrpl_tools.py build-clawback \
  --from rIssuerAddress \
  --destination rHolderAddress \
  --currency 524C555344000000000000000000000000000000 \
  --amount 1000
```

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


### Clawback Safeguards

Before executing a clawback, always:
1. Verify the holder address is not an exchange hot wallet (coordinate first)
2. Check the holder's actual RLUSD balance
3. Log the legal/compliance order reference in a memo
4. Consider partial clawback (only the flagged amount, not the full balance)
5. Have a multi-signature governance process for clawback approval

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## Monitoring RLUSD Supply

### Supply and holder-distribution boundary

No third-party RLUSD obligations/holder route is certified in this release. `trustlines` can provide
a paginated ledger sample, but it is not total supply or a complete holder count. Report those values
as unavailable unless a separately contract-tested provider route is current, named and timestamped.

### Transaction Monitoring

```python
async def monitor_rlusd_transactions(
    webhook_url: str = None,
    min_amount: float = 10000.0
):
    """Monitor large RLUSD transfers via WebSocket."""
    import asyncio, json
    import websockets

    async with websockets.connect("wss://xrplcluster.com") as ws:
        await ws.send(json.dumps({
            "command": "subscribe",
            "accounts": [RLUSD_ISSUER]
        }))

        while True:
            msg = json.loads(await ws.recv())
            if msg.get("type") == "transaction":
                tx = msg.get("transaction", {})
                if tx.get("TransactionType") == "Payment":
                    amount = tx.get("Amount", {})
                    if isinstance(amount, dict) and amount.get("currency") == RLUSD_CUR:
                        value = float(amount.get("value", 0))
                        if value >= min_amount:
                            alert = {
                                "type": "LARGE_RLUSD_TRANSFER",
                                "from": tx.get("Account"),
                                "to": tx.get("Destination"),
                                "amount": value,
                                "tx_hash": msg.get("hash"),
                                "ledger": msg.get("ledger_index")
                            }
                            print(f"[ALERT] {json.dumps(alert, indent=2)}")
                            if webhook_url:
                                await client.post(webhook_url, json=alert)
```

---

## Practical Workflows

### Workflow 1: Onboard a New RLUSD User

1. User completes KYC through issuer's compliance portal
2. User submits XRPL address for whitelisting
3. Issuer adds address to approved list (off-chain or via on-chain whitelist)
4. User creates trust line: `python3 scripts/xrpl_tools.py build-trustset --from rUSER --currency 524C555344000000000000000000000000000000 --issuer rISSUER --value 100000`
5. User sends signed TrustSet to network
6. Issuer verifies trust line exists: `python3 scripts/xrpl_tools.py trustlines rUSER | grep -i 524C555344`
7. Issuer sends initial RLUSD: `python3 scripts/xrpl_tools.py build-payment --from rISSUER --to rUSER --cur 524C555344000000000000000000000000000000 --iss rISSUER --amount 10000`

### Workflow 2: Monthly Compliance Review

1. Export all RLUSD holders and balances
2. Cross-reference against sanctions lists (off-chain)
3. Flag accounts with unusual activity patterns
4. Execute clawbacks for flagged accounts
5. Update supply reconciliation report
6. Submit compliance report to regulators

### Workflow 3: Travel Rule for Large Transfer

1. User initiates a $50,000 RLUSD transfer
2. Sender's VASP collects originator info (name, address, jurisdiction)
3. Beneficiary VASP provides beneficiary info
4. Payment is constructed with Travel Rule memo
5. Transaction is submitted and monitored
6. Both VASPs store the transaction hash for audit

---

## Regulation & Compliance Notes by Jurisdiction

| Jurisdiction | RLUSD Status | Key Requirements |
|-------------|-------------|------------------|
| **USA** | Regulated stablecoin | NYDFS (if Ripple licensed), Travel Rule >$3k, OFAC screening |
| **EU** | MiCA stablecoin | MiCA Art. 43 compliance, e-money license, Travel Rule |
| **Singapore** | DPT stablecoin | MAS stablecoin framework, Travel Rule mandatory |
| **Dubai** | VARA stablecoin | VARA license, stablecoin-specific regulations |
| **UK** | FCA-regulated | FCA registration, Travel Rule (Jan 2024) |

---

## Validated-ledger sources

Use a currently selected XRPL JSON-RPC/Clio endpoint and validated ledger indices. No third-party
explorer route is certified here. Reconfirm the official RLUSD issuer/currency information against
current first-party Ripple documentation before any value-bearing workflow.

---

## Related Files

- `knowledge/03-xrpl-trustlines.md` — trust line + freeze flags
- `knowledge/07-xrpl-clawback.md` — regulatory clawback semantics
- `knowledge/25-xrpl-audit-security.md` — compliance audit checklist
- `knowledge/42-xrpl-treasury.md` — treasury monitoring patterns
- `knowledge/59-rwa-tokenization.md` — RWA tokenization framework
