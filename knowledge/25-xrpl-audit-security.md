# XRPL Security & Audit Guide

## Overview

XRPL transactions are irreversible. Security failures mean permanent loss. This document covers key management, offline signing, attack vectors (partial payments, trust line phishing, destination tag confusion), and treasury monitoring.

---

## 1. Key Management

### Key Hierarchy

```
Master Key (offline, air-gapped)
    │
    ├── Regular Key (online, hot)
    │       Used for daily operations
    │
    └── Signer List (multisig for large transactions)
```

### Never store seeds in code or git

```python
# BAD
wallet = Wallet.from_seed("snMySeedIsHere...")

# GOOD: Use environment variables
import os
seed = os.environ["XRPL_WALLET_SEED"]
wallet = Wallet.from_seed(seed)

# BETTER: Use secrets manager
import boto3
secrets = boto3.client("secretsmanager")
seed = secrets.get_secret_value(SecretId="xrpl/prod/wallet-seed")["SecretString"]
wallet = Wallet.from_seed(seed)
```

### Hardware Security Modules (HSM)

For treasury wallets:
- Use FIPS 140-2 HSM (AWS CloudHSM, Yubikey, Ledger)
- Never export private keys
- Sign transactions inside the HSM
- Audit all signing events

### Key Rotation

```python
# Rotate regular key
from xrpl.models.transactions import SetRegularKey

new_regular_key = Wallet.create()

tx = SetRegularKey(
    account=master_wallet.address,
    regular_key=new_regular_key.address,
    fee="12"
)
# Sign with MASTER key (or old regular key)
signed = autofill_and_sign(tx, master_wallet, client)
submit_and_wait(signed, client)

# Now master_wallet's operations use new_regular_key
```

---

## 2. Offline Signing

Never expose private keys on internet-connected machines for high-value transactions:

```python
# OFFLINE machine: prepare and sign
from xrpl.wallet import Wallet
from xrpl.models.transactions import Payment
import json

# Load seed from secure storage (USB, paper, HSM)
wallet = Wallet.from_seed("sn...")

# Transaction pre-built on online machine and transferred
# (via QR code, USB stick, etc.)
unsigned_tx = {
    "TransactionType": "Payment",
    "Account": wallet.address,
    "Destination": "rDEST...",
    "Amount": "10000000000",
    "Fee": "12",
    "Sequence": 100,
    "LastLedgerSequence": 87700000,
    "SigningPubKey": wallet.public_key
}

tx = Payment.from_xrpl(unsigned_tx)
signed = wallet.sign(tx)
print(json.dumps({"tx_blob": signed.tx_blob}))
# Transfer tx_blob to online machine for submission
```

```python
# ONLINE machine: submit the pre-signed blob
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import SubmitOnly

client = JsonRpcClient("https://xrplcluster.com")
tx_blob = "1200002200..."  # received from offline machine

resp = client.request(SubmitOnly(tx_blob=tx_blob))
print(resp.result)
```

---

## 3. Partial Payment Attack Detection

**THE #1 XRPL EXPLOIT**: An attacker sends a partial payment, and a naive receiver checks `Amount` instead of `meta.delivered_amount`.

### Vulnerable Code (DO NOT USE)

```python
# VULNERABLE: Checking Amount field
def process_payment(tx: dict) -> float:
    amount = tx["Amount"]  # WRONG: could be different from delivered
    return float(amount) / 1_000_000  # Reports wrong amount!
```

### Secure Code

```python
# SECURE: Always check delivered_amount
def process_payment(result: dict) -> float:
    meta = result.get("meta", {})
    
    # Check partial payment flag
    flags = result.get("Flags", 0)
    is_partial = bool(flags & 0x00020000)  # tfPartialPayment
    
    delivered = meta.get("delivered_amount")
    
    if delivered is None:
        raise ValueError("No delivered_amount in tx meta — don't process")
    
    if delivered == "unavailable":
        raise ValueError("delivered_amount unavailable (very old tx) — verify manually")
    
    if isinstance(delivered, str):
        # XRP in drops
        return int(delivered) / 1_000_000
    elif isinstance(delivered, dict):
        # Token
        return {
            "currency": delivered["currency"],
            "issuer": delivered.get("issuer"),
            "value": delivered["value"]
        }

# When subscribing to payments:
def on_payment_received(tx):
    if tx["TransactionType"] != "Payment":
        return
    if tx["meta"]["TransactionResult"] != "tesSUCCESS":
        return
    
    destination = tx.get("Destination")
    dest_tag = tx.get("DestinationTag")
    
    # ALWAYS use delivered_amount
    delivered = tx["meta"].get("delivered_amount")
    if not delivered:
        log.error(f"No delivered_amount: {tx['hash']}")
        return
    
    credit_account(destination, dest_tag, delivered)
```

---

## 4. Trust Line Phishing

Attackers create tokens with names identical to legitimate ones and airdrop them.

### Verification Checklist

```python
def verify_token(currency: str, issuer: str) -> dict:
    """Multi-source token verification."""
    
    issues = []
    
    # 1. Check issuer account flags
    from xrpl.models.requests import AccountInfo
    resp = client.request(AccountInfo(account=issuer))
    acct = resp.result.get("account_data")
    
    if not acct:
        issues.append("CRITICAL: Issuer account not found")
        return {"trusted": False, "issues": issues}
    
    flags = acct.get("Flags", 0)
    
    # Good signs
    if flags & 0x00200000:  # lsfNoFreeze
        pass  # Cannot freeze, good for holders
    
    # Bad signs
    if flags & 0x00080000:  # lsfGlobalFreeze
        issues.append("WARNING: Global freeze active")
    
    if not (flags & 0x00800000):  # lsfDefaultRipple
        issues.append("WARNING: DefaultRipple not set (unusual for issuer)")
    
    # 2. Check domain
    domain_hex = acct.get("Domain", "")
    if not domain_hex:
        issues.append("WARNING: No domain set on issuer")
    else:
        domain = bytes.fromhex(domain_hex).decode()
        # TODO: fetch TOML, verify token listed there
    
    # 3. Check XRPLMeta
    # (as shown in data-api doc)
    
    # 4. Check age of issuer account
    # (older = more trustworthy generally)
    
    return {
        "trusted": len(issues) == 0,
        "issues": issues,
        "issuer": issuer,
        "currency": currency
    }
```

### Identifying Fake Tokens

| Red Flag | What It Means |
|----------|---------------|
| No domain on issuer | Unprofessional |
| Very new issuer account | Possible scam |
| Issuer not on XRPLMeta | Unregistered |
| Identical name to known token | Impersonation |
| No TOML file at domain | Not verifiable |
| TransferRate = 100% | Unspendable trap |

---

## 5. Destination Tag Confusion

Exchanges and services use destination tags to route payments. Mistakes cause permanent loss.

### Implementation

```python
# ALWAYS enforce destination tags for multi-user wallets
def create_deposit_address(user_id: int) -> dict:
    return {
        "address": "rHOT_WALLET...",  # shared hot wallet
        "destination_tag": user_id,   # unique per user
        "memo": f"Deposit for user {user_id}"
    }

# When processing deposits, ALWAYS check destination tag
def credit_deposit(tx: dict):
    destination = tx.get("Destination")
    dest_tag = tx.get("DestinationTag")
    
    if destination != HOT_WALLET_ADDRESS:
        return  # Not for us
    
    if dest_tag is None:
        # No tag — cannot attribute to user
        # Hold in suspense account, contact support
        hold_for_manual_review(tx)
        return
    
    user = get_user_by_tag(dest_tag)
    if not user:
        hold_for_manual_review(tx)
        return
    
    delivered = tx["meta"]["delivered_amount"]
    credit_user(user, delivered)
```

### Enforce Destination Tag on Hot Wallet

```python
# Set RequireDest so senders MUST provide a tag
from xrpl.models.transactions import AccountSet
from xrpl.models.transactions.account_set import AccountSetAsfFlag

tx = AccountSet(
    account=hot_wallet.address,
    set_flag=AccountSetAsfFlag.ASF_REQUIRE_DEST,
    fee="12"
)
```

---

## 6. Treasury Wallet Monitoring

```python
import asyncio
from xrpl.asyncio.clients import AsyncWebsocketClient
from xrpl.models.requests import Subscribe
from xrpl.models.requests.subscribe import StreamParameter

TREASURY_ADDRESSES = [
    "rTREASURY1...",
    "rTREASURY2...",
    "rRESERVE..."
]

ALERT_THRESHOLD_XRP = 1000  # Alert if >1000 XRP moves

async def monitor_treasury():
    async with AsyncWebsocketClient("wss://xrplcluster.com") as client:
        # Subscribe to account transactions
        await client.request(Subscribe(
            accounts=TREASURY_ADDRESSES,
            streams=[StreamParameter.LEDGER]
        ))
        
        async for message in client:
            if message.get("type") == "transaction":
                tx = message["transaction"]
                meta = message.get("meta", {})
                
                if meta.get("TransactionResult") != "tesSUCCESS":
                    continue
                
                await analyze_treasury_tx(tx, meta)

async def analyze_treasury_tx(tx: dict, meta: dict):
    tx_type = tx.get("TransactionType")
    account = tx.get("Account")
    destination = tx.get("Destination")
    
    # Large XRP movement
    delivered = meta.get("delivered_amount")
    if isinstance(delivered, str):
        xrp_amount = int(delivered) / 1_000_000
        
        if xrp_amount >= ALERT_THRESHOLD_XRP:
            alert = (
                f"🚨 TREASURY ALERT: {xrp_amount:.2f} XRP "
                f"moved {'from' if account in TREASURY_ADDRESSES else 'to'} "
                f"treasury in tx {tx['hash']}"
            )
            await send_alert(alert)
    
    # Unauthorized account set
    if tx_type == "AccountSet" and account in TREASURY_ADDRESSES:
        await send_alert(
            f"⚠️ AccountSet on treasury {account}: {tx['hash']}"
        )
    
    # Signer list change
    if tx_type == "SignerListSet" and account in TREASURY_ADDRESSES:
        await send_alert(
            f"🔴 CRITICAL: SignerListSet on treasury {account}: {tx['hash']}"
        )

async def send_alert(message: str):
    import httpx
    webhook = "https://hooks.slack.com/services/..."
    async with httpx.AsyncClient() as client:
        await client.post(webhook, json={"text": message})
```

---

## 7. Secure Transaction Submission Pattern

```python
import hashlib

class SecureXRPLSubmitter:
    def __init__(self, client, wallet):
        self.client = client
        self.wallet = wallet
        self.submitted_hashes = set()
    
    async def submit(self, tx, max_retries=3):
        # Autofill and sign
        signed = autofill_and_sign(tx, self.wallet, self.client)
        tx_hash = signed.get_hash()
        
        # Idempotency check
        if tx_hash in self.submitted_hashes:
            return await self.client.request(Tx(transaction=tx_hash))
        
        for attempt in range(max_retries):
            try:
                result = await submit_and_wait(signed, self.client)
                self.submitted_hashes.add(tx_hash)
                
                # Log every transaction
                self._audit_log({
                    "hash": tx_hash,
                    "type": tx.transaction_type,
                    "result": result.result["meta"]["TransactionResult"],
                    "fee": result.result["Fee"],
                    "ledger": result.result.get("ledger_index")
                })
                
                return result
            
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise
    
    def _audit_log(self, entry: dict):
        import json, datetime
        entry["timestamp"] = datetime.datetime.utcnow().isoformat()
        with open("/var/log/xrpl-audit.log", "a") as f:
            f.write(json.dumps(entry) + "\n")
```

---

## 8. Common Attack Vectors Summary

| Attack | Method | Defense |
|--------|--------|---------|
| Partial payment | Send with `tfPartialPayment` | Always check `delivered_amount` |
| Token impersonation | Create token with same name | Verify issuer + domain + XRPLMeta |
| Seed exposure | Leaked .env file | Use secrets manager, never commit |
| Destination tag loss | Missing tag in deposit | Enforce `RequireDest`, hold tagless |
| Trust line freezing | Issuer freezes your balance | Choose issuers with `NoFreeze` |
| Clawback | Issuer reclaims tokens | Avoid issuers with clawback enabled |
| AMM sandwich attack | Front-run large AMM trade | Use limit orders + AMM bid slot |
| Missing `LastLedgerSequence` | Tx queued forever | Always set LLS + 20 |

---

## 9. Security Checklist for Production

- [ ] Seeds stored in secrets manager (never in code or git)
- [ ] Hot wallet uses regular key (master key offline)
- [ ] Treasury uses multisig (3-of-5 or similar)
- [ ] `delivered_amount` always checked for payments
- [ ] `RequireDest` set on multi-user wallets
- [ ] All transactions logged to immutable audit log
- [ ] Treasury addresses monitored with real-time alerts
- [ ] Token issuers verified via TOML + XRPLMeta
- [ ] SSL/TLS on all API endpoints
- [ ] Firewall restricts admin ports to VPN only
- [ ] Dependency audits: `pip audit` / `npm audit`
- [ ] `LastLedgerSequence` set on all transactions
