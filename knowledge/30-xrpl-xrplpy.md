# xrpl-py Library Reference

## Overview

`xrpl-py` is an official Python SDK for the XRP Ledger. It provides synchronous and asynchronous clients plus transaction/request models whose exact coverage depends on the installed release. XRPL-Hermes v1.9.0 tests against xrpl-py 4.2.0 and 5.0.0; verify current SDK documentation for any model outside the certified builders.

```bash
pip install xrpl-py
```

---

## 1. Core Imports

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


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

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


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

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


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

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## 8. DEX: OfferCreate

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


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
    fee="<autofill>"
)

# Double-asset deposit
tx = AMMDeposit(
    account=wallet.address,
    asset={"currency": "XRP"},
    asset2={"currency": "USD", "issuer": "rISSUER..."},
    amount=xrp_to_drops(100),       # XRP side
    amount2={"currency": "USD", "issuer": "rISSUER...", "value": "50"},  # token side
    flags=AMMDepositFlag.TF_TWO_ASSET,
    fee="<autofill>"
)
```

---

## 10. NFTokenMint

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


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

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## 14. Signing Without Submitting

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## Related Files

- `knowledge/02-xrpl-payments.md` — Payment building examples
- `knowledge/15-xrpl-transaction-format.md` — transaction serialization
- `knowledge/31-xrpl-xrpljs.md` — JavaScript equivalent
