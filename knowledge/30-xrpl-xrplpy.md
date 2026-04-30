# xrpl-py Library Reference

## Overview

`xrpl-py` is the official Python SDK for the XRP Ledger. Supports synchronous and async clients, wallet management, all transaction types, and multi-client failover.

```bash
pip install xrpl-py
```

---

## 1. Core Imports

```python
# Clients
from xrpl.clients import JsonRpcClient
from xrpl.asyncio.clients import AsyncJsonRpcClient, AsyncWebsocketClient

# Wallet
from xrpl.wallet import Wallet

# Models - Requests
from xrpl.models.requests import (
    AccountInfo,
    AccountLines,
    AccountOffers,
    AccountObjects,
    AccountNFTs,
    AccountChannels,
    AccountTx,
    Ledger,
    LedgerData,
    LedgerEntry,
    Tx,
    Fee,
    ServerInfo,
    Subscribe,
    BookOffers,
    AMMInfo,
    NFTSellOffers,
    NFTBuyOffers,
    NFTInfo,
    SubmitOnly,
)

# Models - Transactions
from xrpl.models.transactions import (
    Payment,
    TrustSet,
    OfferCreate,
    OfferCancel,
    AccountSet,
    SetRegularKey,
    SignerListSet,
    NFTokenMint,
    NFTokenBurn,
    NFTokenCreateOffer,
    NFTokenAcceptOffer,
    NFTokenCancelOffer,
    AMMCreate,
    AMMDeposit,
    AMMWithdraw,
    AMMVote,
    AMMBid,
    EscrowCreate,
    EscrowFinish,
    EscrowCancel,
    PaymentChannelCreate,
    PaymentChannelFund,
    PaymentChannelClaim,
    TicketCreate,
    DepositPreauth,
    Clawback,
)

# Transaction processing
from xrpl.transaction import (
    autofill,
    autofill_and_sign,
    sign,
    submit,
    submit_and_wait,
    multisign,
)

# Utils
from xrpl.utils import (
    xrp_to_drops,
    drops_to_xrp,
    ripple_time_to_datetime,
    datetime_to_ripple_time,
    str_to_hex,
    hex_to_str,
)

# Keypairs
from xrpl.core.keypairs import (
    generate_seed,
    derive_keypair,
    sign as keypairs_sign,
    is_valid_message,
)

# Ledger utils
from xrpl.ledger import get_latest_validated_ledger_sequence
```

---

## 2. Client Initialization

### Synchronous

```python
from xrpl.clients import JsonRpcClient

client = JsonRpcClient("https://xrplcluster.com")
resp = client.request(AccountInfo(account="rN7n...", ledger_index="validated"))
print(resp.result["account_data"])
```

### Asynchronous HTTP

```python
import asyncio
from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.models.requests import AccountInfo

async def main():
    async with AsyncJsonRpcClient("https://xrplcluster.com") as client:
        resp = await client.request(AccountInfo(account="rN7n..."))
        print(resp.result)

asyncio.run(main())
```

### Async WebSocket

```python
from xrpl.asyncio.clients import AsyncWebsocketClient
from xrpl.models.requests import Subscribe
from xrpl.models.requests.subscribe import StreamParameter

async def subscribe_to_ledger():
    async with AsyncWebsocketClient("wss://xrplcluster.com") as client:
        await client.request(Subscribe(streams=[StreamParameter.LEDGER]))
        
        async for message in client:
            if message.get("type") == "ledgerClosed":
                print(f"New ledger: {message['ledger_index']}")
```

---

## 3. Wallet

```python
from xrpl.wallet import Wallet

# Generate new wallet (offline — do this once, store seed securely)
wallet = Wallet.create()
print(wallet.address)      # safe to log
print(wallet.public_key)   # safe to log
# wallet.seed and wallet.private_key — NEVER print or log these
# Store wallet.seed in a secrets manager (env var, vault, etc.)

# Load wallet from environment variable (correct pattern for scripts)
import os
wallet = Wallet.from_seed(os.environ["XRPL_WALLET_SEED"])

# From mnemonic (BIP39)
wallet = Wallet.from_mnemonic("word1 word2 ... word12")

# Classic address from public key
from xrpl.core.keypairs import derive_classic_address
address = derive_classic_address(public_key)

# Check balance
from xrpl.account import get_balance

client = JsonRpcClient("https://xrplcluster.com")
balance_drops = get_balance(wallet.address, client)
balance_xrp = drops_to_xrp(str(balance_drops))
```

---

## 4. Account Info & Lines

```python
# Account info
from xrpl.models.requests import AccountInfo

resp = client.request(AccountInfo(
    account="rN7n...",
    ledger_index="validated"
))
acct = resp.result["account_data"]
print(f"Balance: {drops_to_xrp(acct['Balance'])} XRP")
print(f"Sequence: {acct['Sequence']}")
print(f"OwnerCount: {acct['OwnerCount']}")

# Account trust lines (tokens held)
from xrpl.models.requests import AccountLines

resp = client.request(AccountLines(
    account="rN7n...",
    ledger_index="validated"
))
for line in resp.result["lines"]:
    print(f"{line['balance']} {line['currency']} (issuer: {line['account']})")

# With pagination
async def get_all_trust_lines(address: str) -> list:
    lines = []
    marker = None
    
    while True:
        resp = await client.request(AccountLines(
            account=address,
            limit=400,
            marker=marker
        ))
        lines.extend(resp.result["lines"])
        marker = resp.result.get("marker")
        if not marker:
            break
    
    return lines
```

---

## 5. Sending XRP

```python
from xrpl.models.transactions import Payment
from xrpl.transaction import autofill_and_sign, submit_and_wait

client = JsonRpcClient("https://xrplcluster.com")
wallet = Wallet.from_seed("sn...")

tx = Payment(
    account=wallet.address,
    destination="rDEST...",
    amount=xrp_to_drops(10),  # 10 XRP
    destination_tag=1234,
    memos=[{
        "Memo": {
            "MemoData": str_to_hex("Hello XRPL"),
            "MemoType": str_to_hex("text/plain")
        }
    }]
)

signed = autofill_and_sign(tx, wallet, client)
result = submit_and_wait(signed, client)
print(result.result["meta"]["TransactionResult"])
print(f"TX hash: {result.result['hash']}")
```

---

## 6. Token Payment (Issued Currency)

```python
tx = Payment(
    account=wallet.address,
    destination="rDEST...",
    amount={
        "currency": "USD",
        "issuer": "rISSUER...",
        "value": "50"
    },
    # Optional: path finding for cross-currency
    send_max={
        "currency": "XRP",
        "value": xrp_to_drops(100)
    }
)
```

---

## 7. Trust Set

```python
from xrpl.models.transactions import TrustSet

tx = TrustSet(
    account=wallet.address,
    limit_amount={
        "currency": "SOLO",
        "issuer": "rHZwvHEs56GCmHupwjA4RY7oPA3EoAJWuN",
        "value": "1000000"
    },
    fee="12"
)
signed = autofill_and_sign(tx, wallet, client)
submit_and_wait(signed, client)
```

---

## 8. DEX: OfferCreate

```python
from xrpl.models.transactions import OfferCreate

# Buy 1000 SOLO for 10 XRP
tx = OfferCreate(
    account=wallet.address,
    taker_pays={
        "currency": "SOLO",
        "issuer": "rHZwvHEs...",
        "value": "1000"
    },
    taker_gets=xrp_to_drops(10),  # 10 XRP
    flags=0,  # or tfSell = 0x00080000
    fee="12"
)
signed = autofill_and_sign(tx, wallet, client)
result = submit_and_wait(signed, client)
```

---

## 9. AMM Deposit

```python
from xrpl.models.transactions import AMMDeposit
from xrpl.models.transactions.amm_deposit import AMMDepositFlag

# Single-asset deposit (XRP only)
tx = AMMDeposit(
    account=wallet.address,
    asset={
        "currency": "XRP"
    },
    asset2={
        "currency": "USD",
        "issuer": "rISSUER..."
    },
    amount=xrp_to_drops(100),   # deposit 100 XRP
    flags=AMMDepositFlag.TF_SINGLE_ASSET,
    fee="12"
)

# Double-asset deposit
tx = AMMDeposit(
    account=wallet.address,
    asset={"currency": "XRP"},
    asset2={"currency": "USD", "issuer": "rISSUER..."},
    amount=xrp_to_drops(100),       # XRP side
    amount2={"currency": "USD", "issuer": "rISSUER...", "value": "50"},  # token side
    flags=AMMDepositFlag.TF_TWO_ASSET,
    fee="12"
)
```

---

## 10. NFTokenMint

```python
from xrpl.models.transactions import NFTokenMint
import binascii

tx = NFTokenMint(
    account=wallet.address,
    nftoken_taxon=0,
    flags=0x0000000B,
    transfer_fee=5000,  # 5%
    uri=binascii.hexlify("ipfs://QmXXX...".encode()).decode().upper(),
    fee="12"
)
signed = autofill_and_sign(tx, wallet, client)
result = submit_and_wait(signed, client)
```

---

## 11. get_balance_in_drops / drops_to_xrp

```python
from xrpl.utils import xrp_to_drops, drops_to_xrp
from xrpl.account import get_balance

# Convert
drops = xrp_to_drops(10)         # "10000000"
xrp = drops_to_xrp("10000000")   # Decimal("10")

# Get live balance
drops_bal = get_balance("rN7n...", client)  # int
xrp_bal = float(drops_to_xrp(str(drops_bal)))
```

---

## 12. Multi-Client Failover Pattern

```python
import asyncio
from xrpl.asyncio.clients import AsyncJsonRpcClient

NODES = [
    "https://xrplcluster.com",
    "https://xrpl.ws",
    "https://s1.ripple.com"
]

class FailoverClient:
    def __init__(self, nodes: list):
        self.nodes = nodes
        self.current = 0
    
    async def request(self, req, retries=3):
        for attempt in range(retries):
            url = self.nodes[self.current % len(self.nodes)]
            try:
                async with AsyncJsonRpcClient(url) as client:
                    resp = await client.request(req)
                    if resp.is_successful():
                        return resp
                    raise Exception(f"API error: {resp.result.get('error')}")
            except Exception as e:
                self.current += 1
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(1)

client = FailoverClient(NODES)
```

---

## 13. Async Signing and Submission

```python
import asyncio
from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.asyncio.transaction import (
    autofill,
    autofill_and_sign,
    submit_and_wait
)

async def send_payment_async(seed: str, destination: str, amount_xrp: float):
    wallet = Wallet.from_seed(seed)
    
    async with AsyncJsonRpcClient("https://xrplcluster.com") as client:
        tx = Payment(
            account=wallet.address,
            destination=destination,
            amount=xrp_to_drops(amount_xrp)
        )
        
        # Async autofill fills Sequence, Fee, LastLedgerSequence
        signed = await autofill_and_sign(tx, wallet, client)
        result = await submit_and_wait(signed, client)
        
        return result.result["meta"]["TransactionResult"]

result = asyncio.run(send_payment_async("sn...", "rDEST...", 10))
```

---

## 14. Signing Without Submitting

```python
from xrpl.transaction import autofill, sign

# Useful for offline signing
tx = Payment(...)
tx_autofilled = autofill(tx, client)
tx_signed = sign(tx_autofilled, wallet)

# Get the blob and hash
blob = tx_signed.to_hex()
hash = tx_signed.get_hash()

# Submit later
from xrpl.models.requests import SubmitOnly
resp = client.request(SubmitOnly(tx_blob=blob))
```
