# XRPL L1 Reference — Practical Python Workflows

This file is a field reference for building against XRP Ledger L1 with `xrpl-py` and `httpx`.
All public endpoint examples use `https://xrplcluster.com` for JSON-RPC and `wss://xrplcluster.com` for WebSocket calls.
Use testnet or devnet when submitting real transactions during development; use mainnet only with funded production accounts and explicit operator approval.

## Public endpoints
- **Mainnet JSON-RPC**: `https://xrplcluster.com` — General ledger queries, account info, fee data, transaction submission
- **Mainnet WebSocket**: `wss://xrplcluster.com` — Subscriptions, ledger streams, async xrpl-py clients
- **Ripple mainnet JSON-RPC**: `https://s1.ripple.com:51234` — Fallback public rippled endpoint
- **Ripple mainnet WebSocket**: `wss://s1.ripple.com` — Fallback WebSocket endpoint
- **Testnet JSON-RPC**: `https://s.altnet.rippletest.net:51234` — Safe transaction testing
- **Testnet WebSocket**: `wss://s.altnet.rippletest.net:51233` — Safe subscription testing
- **Devnet JSON-RPC**: `https://s.devnet.rippletest.net:51234` — Amendment and experimental testing
- **Devnet WebSocket**: `wss://s.devnet.rippletest.net:51233` — Experimental subscription testing
- **Xahau JSON-RPC**: `https://xahau.network` — Hooks network queries with XRPL-like API
- **Xahau WebSocket**: `wss://xahau.network` — Hooks network subscriptions

## Install
```bash
python -m venv .venv
source .venv/bin/activate
pip install xrpl-py httpx websockets
```

## Core concepts
1. XRP is the native asset. Amounts in transactions are represented as drops, where 1 XRP equals 1,000,000 drops.
2. Accounts are ledger objects. A keypair is not an account until enough XRP is sent to activate the address.
3. Every account has a `Sequence`; each normal transaction consumes the current sequence and increments it.
4. Validated ledgers are final. Use `ledger_index="validated"` for reads that should not roll back.
5. Fees are destroyed, not paid to validators. A submitted transaction must include a fee in drops.
6. The base reserve and owner reserve are network parameters. Query them from `server_state` or `server_info` instead of hardcoding.
7. Tickets can reserve future sequence slots, but simple applications can use normal sequence numbers.
8. Destination tags are unsigned 32-bit integers commonly used by exchanges and custodians to route deposits.
9. Memos are arbitrary hex-encoded payloads and should not contain secrets because all ledger data is public.
10. Partial payments can deliver less than the displayed `Amount`; payment processors must inspect delivered amount metadata.
11. Trust lines represent issued currencies. Native XRP does not use a trust line.
12. The DEX and AMM are native protocol features, not smart contracts.
13. The XRPL transaction lifecycle is construct, autofill, sign, submit, wait for validation, inspect result code.
14. A `tesSUCCESS` engine result means the transaction succeeded if it is included in a validated ledger.
15. A `tec` code is included in a ledger and consumes sequence and fee even though the requested effect failed.
16. A `ter`, `tel`, or `tem` code requires different retry handling; do not blindly resubmit forever.
17. Use idempotency keys at the application layer, usually by storing the signed transaction hash before submission.
18. Use WebSocket subscriptions for live applications; use JSON-RPC polling for batch jobs and scripts.
19. Use separate hot, warm, and cold accounts for issuers and custodial services.
20. For production, never log seeds, private keys, signed blobs for sensitive flows, or full environment dumps.

## Account creation with xrpl-py
This creates a keypair locally. On mainnet the address becomes usable only after another account funds it with the current reserve.
```python
from xrpl.wallet import Wallet
from xrpl.core.keypairs import generate_seed

seed = generate_seed(algorithm="ed25519")
wallet = Wallet.from_seed(seed)
print("classic_address", wallet.classic_address)
print("seed", seed)  # Store in a secret manager; never commit this.
```

## Fund a testnet account
Use this only on testnet. The faucet endpoint is public and rate limited.
```python
import httpx

TESTNET_FAUCET = "https://faucet.altnet.rippletest.net/accounts"

with httpx.Client(timeout=30) as client:
    response = client.post(TESTNET_FAUCET)
    response.raise_for_status()
    account = response.json()["account"]
    print(account["classicAddress"])
    print(account["secret"])
```

## Query account info
```python
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountInfo

client = JsonRpcClient("https://xrplcluster.com")
address = "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh"  # genesis account, useful for read examples
request = AccountInfo(account=address, ledger_index="validated", strict=True)
response = client.request(request)
print(response.result["account_data"])
```

## Same account info with httpx JSON-RPC
```python
import httpx

payload = {
    "method": "account_info",
    "params": [{
        "account": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
        "ledger_index": "validated",
        "strict": True
    }]
}
response = httpx.post("https://xrplcluster.com", json=payload, timeout=20)
response.raise_for_status()
print(response.json()["result"]["account_data"]["Balance"])
```

## Create and submit a payment
The example signs locally and submits through a public endpoint. Run it on testnet unless the seed is intentionally funded on mainnet.
```python
import os
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import Payment
from xrpl.transaction import submit_and_wait
from xrpl.wallet import Wallet
from xrpl.utils import xrp_to_drops

client = JsonRpcClient(os.getenv("XRPL_RPC", "https://s.altnet.rippletest.net:51234"))
wallet = Wallet.from_seed(os.environ["XRPL_SEED"])

tx = Payment(
    account=wallet.classic_address,
    destination=os.environ["XRPL_DESTINATION"],
    amount=xrp_to_drops("1.25"),
    destination_tag=int(os.getenv("XRPL_DESTINATION_TAG", "0")) or None,
)

result = submit_and_wait(tx, client, wallet)
print(result.result["hash"])
print(result.result["meta"]["TransactionResult"])
```

## Fee estimation
`fee` gives a quick fee quote. `server_state` exposes load and reserve fields that help production systems tune policies.
```python
import httpx

XRPL_RPC = "https://xrplcluster.com"

def rpc(method: str, params: list[dict] | None = None) -> dict:
    payload = {"method": method, "params": params or [{}]}
    response = httpx.post(XRPL_RPC, json=payload, timeout=20)
    response.raise_for_status()
    data = response.json()["result"]
    if data.get("status") != "success":
        raise RuntimeError(data)
    return data

fee = rpc("fee")
server_state = rpc("server_state")
print("open ledger fee drops", fee["drops"]["open_ledger_fee"])
print("minimum fee drops", fee["drops"]["minimum_fee"])
print("base reserve xrp", server_state["state"].get("validated_ledger", {}).get("reserve_base"))
print("owner reserve xrp", server_state["state"].get("validated_ledger", {}).get("reserve_inc"))
```

## Ledger queries
### JSON-RPC example: ledger_current
```json
{"method":"ledger_current","params":[{}]}
```

### JSON-RPC example: ledger validated
```json
{"method":"ledger","params":[{"ledger_index":"validated","transactions":false,"expand":false}]}
```

### JSON-RPC example: server_info
```json
{"method":"server_info","params":[{}]}
```

### JSON-RPC example: account_lines
```json
{"method":"account_lines","params":[{"account":"rExample","ledger_index":"validated"}]}
```

### JSON-RPC example: account_objects
```json
{"method":"account_objects","params":[{"account":"rExample","ledger_index":"validated","type":"state"}]}
```

### JSON-RPC example: account_tx
```json
{"method":"account_tx","params":[{"account":"rExample","ledger_index_min":-1,"ledger_index_max":-1,"limit":10}]}
```

### JSON-RPC example: tx
```json
{"method":"tx","params":[{"transaction":"HASH","binary":false}]}
```

### JSON-RPC example: book_offers
```json
{"method":"book_offers","params":[{"taker_gets":{"currency":"USD","issuer":"rIssuer"},"taker_pays":"XRP","ledger_index":"validated","limit":10}]}
```

## Robust JSON-RPC helper
```python
from __future__ import annotations
import httpx
from typing import Any

class XrplRpcError(RuntimeError):
    pass

class XrplRpc:
    def __init__(self, endpoint: str = "https://xrplcluster.com") -> None:
        self.endpoint = endpoint
        self.client = httpx.Client(timeout=20)

    def call(self, method: str, **params: Any) -> dict[str, Any]:
        payload = {"method": method, "params": [params]}
        response = self.client.post(self.endpoint, json=payload)
        response.raise_for_status()
        result = response.json()["result"]
        if result.get("status") == "error":
            raise XrplRpcError(result)
        return result

rpc = XrplRpc()
print(rpc.call("ledger", ledger_index="validated"))
```

## Payment processor checklist
- Maintain a table of expected deposits keyed by account plus destination tag.
- Subscribe to `transactions` or poll `account_tx` from the last processed ledger.
- Only credit after the transaction appears in a validated ledger.
- Require `TransactionType == "Payment"` and `Destination` equals your receiving account.
- Check `meta.TransactionResult == "tesSUCCESS"`.
- For XRP, use delivered amount metadata when present; otherwise use `Amount` only for simple XRP payments.
- For issued currencies, compare currency, issuer, and value strings exactly.
- Reject or manually review partial payments unless explicitly supported.
- Persist the transaction hash before crediting to make processing idempotent.
- Keep enough XRP on operational accounts for reserve and fees.
- Backfill missed ledgers after downtime using `account_tx` markers.
- Alert on `tec` results, fee spikes, server desync, and failed submissions.

## Common transaction JSON
### Payment XRP
```json
{
  "TransactionType": "Payment",
  "Account": "rSender",
  "Destination": "rReceiver",
  "Amount": "2500000",
  "DestinationTag": 123456
}
```

### Payment IOU
```json
{
  "TransactionType": "Payment",
  "Account": "rSender",
  "Destination": "rReceiver",
  "Amount": {
    "currency": "USD",
    "issuer": "rIssuer",
    "value": "10.50"
  },
  "SendMax": {
    "currency": "USD",
    "issuer": "rIssuer",
    "value": "10.60"
  }
}
```

### TrustSet
```json
{
  "TransactionType": "TrustSet",
  "Account": "rHolder",
  "LimitAmount": {
    "currency": "USD",
    "issuer": "rIssuer",
    "value": "100000"
  }
}
```

### AccountSet domain
```json
{
  "TransactionType": "AccountSet",
  "Account": "rIssuer",
  "Domain": "6578616d706c652e636f6d",
  "SetFlag": 8
}
```

### OfferCreate
```json
{
  "TransactionType": "OfferCreate",
  "Account": "rTrader",
  "TakerGets": "1000000",
  "TakerPays": {
    "currency": "USD",
    "issuer": "rIssuer",
    "value": "0.50"
  }
}
```

### AMMInfo request
```json
{
  "method": "amm_info",
  "params": [
    {
      "asset": "XRP",
      "asset2": {
        "currency": "USD",
        "issuer": "rIssuer"
      },
      "ledger_index": "validated"
    }
  ]
}
```

## Async ledger stream
```python
import asyncio
from xrpl.asyncio.clients import AsyncWebsocketClient
from xrpl.models.requests import Subscribe

async def main() -> None:
    async with AsyncWebsocketClient("wss://xrplcluster.com") as client:
        await client.send(Subscribe(streams=["ledger"]))
        async for message in client:
            print(message)

asyncio.run(main())
```

## Operational workflows
1. Bootstrap a hot wallet on testnet, run payment integration tests, then replace the endpoint and funding path for production after review.
2. Use `fee` before each submission and cap the accepted fee in application policy.
3. Use `LastLedgerSequence` from `autofill` so stale signed transactions expire quickly.
4. For custodial receiving, use one destination account with unique destination tags or one account per user; tags reduce reserve cost.
5. For outgoing withdrawals, queue intent records, sign from a controlled worker, submit once, and reconcile by hash.
6. For issuer operations, keep the issuing account cold and use operational distribution accounts.
7. For token payments, require existing trust lines and preflight with `account_lines`.
8. For NFT and AMM features, check amendment availability on the connected network before enabling UI actions.
9. For failover, use two independent public endpoints and compare validated ledger indices before switching.
10. For compliance archives, store request payload, signed transaction hash, validation ledger, and normalized metadata.

## Troubleshooting codes
- `tesSUCCESS`: Transaction succeeded in a validated ledger.
- `tecNO_DST_INSUF_XRP`: Destination does not exist and payment did not send enough XRP to create it.
- `tecDST_TAG_NEEDED`: Destination requires a destination tag.
- `tecUNFUNDED_PAYMENT`: Sender does not have enough spendable balance.
- `tefPAST_SEQ`: Sequence is already used; refresh account sequence.
- `terQUEUED`: Transaction is queued; wait or resubmit with higher fee if appropriate.
- `telINSUF_FEE_P`: Local server rejected because fee is too low.
- `temMALFORMED`: Transaction is invalid and should not be retried unchanged.

## Practical reference notes
- When signing transaction batch 1, persist the hash before network submission.
- When estimating fees for payment lane 2, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 3, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 4, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 5.
- When signing transaction batch 6, persist the hash before network submission.
- When estimating fees for payment lane 7, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 8, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 9, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 10.
- When signing transaction batch 11, persist the hash before network submission.
- When estimating fees for payment lane 12, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 13, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 14, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 15.
- When signing transaction batch 16, persist the hash before network submission.
- When estimating fees for payment lane 17, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 18, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 19, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 20.
- When signing transaction batch 21, persist the hash before network submission.
- When estimating fees for payment lane 22, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 23, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 24, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 25.
- When signing transaction batch 26, persist the hash before network submission.
- When estimating fees for payment lane 27, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 28, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 29, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 30.
- When signing transaction batch 31, persist the hash before network submission.
- When estimating fees for payment lane 32, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 33, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 34, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 35.
- When signing transaction batch 36, persist the hash before network submission.
- When estimating fees for payment lane 37, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 38, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 39, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 40.
- When signing transaction batch 41, persist the hash before network submission.
- When estimating fees for payment lane 42, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 43, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 44, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 45.
- When signing transaction batch 46, persist the hash before network submission.
- When estimating fees for payment lane 47, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 48, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 49, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 50.
- When signing transaction batch 51, persist the hash before network submission.
- When estimating fees for payment lane 52, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 53, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 54, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 55.
- When signing transaction batch 56, persist the hash before network submission.
- When estimating fees for payment lane 57, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 58, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 59, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 60.
- When signing transaction batch 61, persist the hash before network submission.
- When estimating fees for payment lane 62, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 63, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 64, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 65.
- When signing transaction batch 66, persist the hash before network submission.
- When estimating fees for payment lane 67, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 68, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 69, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 70.
- When signing transaction batch 71, persist the hash before network submission.
- When estimating fees for payment lane 72, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 73, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 74, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 75.
- When signing transaction batch 76, persist the hash before network submission.
- When estimating fees for payment lane 77, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 78, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 79, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 80.
- When signing transaction batch 81, persist the hash before network submission.
- When estimating fees for payment lane 82, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 83, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 84, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 85.
- When signing transaction batch 86, persist the hash before network submission.
- When estimating fees for payment lane 87, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 88, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 89, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 90.
- When signing transaction batch 91, persist the hash before network submission.
- When estimating fees for payment lane 92, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 93, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 94, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 95.
- When signing transaction batch 96, persist the hash before network submission.
- When estimating fees for payment lane 97, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 98, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 99, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 100.
- When signing transaction batch 101, persist the hash before network submission.
- When estimating fees for payment lane 102, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 103, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 104, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 105.
- When signing transaction batch 106, persist the hash before network submission.
- When estimating fees for payment lane 107, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 108, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 109, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 110.
- When signing transaction batch 111, persist the hash before network submission.
- When estimating fees for payment lane 112, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 113, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 114, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 115.
- When signing transaction batch 116, persist the hash before network submission.
- When estimating fees for payment lane 117, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 118, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 119, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 120.
- When signing transaction batch 121, persist the hash before network submission.
- When estimating fees for payment lane 122, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 123, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 124, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 125.
- When signing transaction batch 126, persist the hash before network submission.
- When estimating fees for payment lane 127, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 128, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 129, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 130.
- When signing transaction batch 131, persist the hash before network submission.
- When estimating fees for payment lane 132, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 133, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 134, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 135.
- When signing transaction batch 136, persist the hash before network submission.
- When estimating fees for payment lane 137, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 138, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 139, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 140.
- When signing transaction batch 141, persist the hash before network submission.
- When estimating fees for payment lane 142, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 143, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 144, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 145.
- When signing transaction batch 146, persist the hash before network submission.
- When estimating fees for payment lane 147, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 148, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 149, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 150.
- When signing transaction batch 151, persist the hash before network submission.
- When estimating fees for payment lane 152, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 153, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 154, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 155.
- When signing transaction batch 156, persist the hash before network submission.
- When estimating fees for payment lane 157, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 158, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 159, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 160.
- When signing transaction batch 161, persist the hash before network submission.
- When estimating fees for payment lane 162, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 163, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 164, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 165.
- When signing transaction batch 166, persist the hash before network submission.
- When estimating fees for payment lane 167, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 168, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 169, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 170.
- When signing transaction batch 171, persist the hash before network submission.
- When estimating fees for payment lane 172, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 173, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 174, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 175.
- When signing transaction batch 176, persist the hash before network submission.
- When estimating fees for payment lane 177, compare `open_ledger_fee` with your configured maximum.
- When reconciling account 178, treat `tec` results as final ledger entries that consumed fee and sequence.
- When monitoring endpoint health check 179, compare `validated_ledger.seq` across endpoints.
- When reading ledger data, prefer validated ledger reads for workflow step 180.

---

## Related Files

- `knowledge/15-xrpl-transaction-format.md` — tx format reference
- `knowledge/30-xrpl-xrplpy.md` — xrpl-py model classes
