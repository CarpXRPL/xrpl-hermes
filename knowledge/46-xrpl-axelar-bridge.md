# Axelar Bridge — XRPL Cross-Chain Communication

## Overview

Axelar is a decentralized cross-chain communication network connecting the XRP Ledger to 50+ blockchains including Ethereum, BNB Chain, Polygon, Avalanche, Fantom, Moonbeam, and others. It enables both token transfers and General Message Passing (GMP) — the ability to invoke smart contracts on any connected chain from any other connected chain.

**Key capabilities:**
- Bridging XRP, RLUSD, USDC, USDT, and AXL between XRPL and EVM chains
- General Message Passing: encode arbitrary payloads and execute them cross-chain
- Decentralized validator set staking AXL tokens — no trusted third party
- Axelarscan: real-time bridge monitoring dashboard

**Status:** XRPL integration live on mainnet. Check axelarscan.io for current supported assets.

---

## Architecture

```
┌─────────────┐     Payment tx       ┌──────────────────┐
│   XRPL L1   │ ──── with memo ────► │  Axelar Gateway  │
│  (sender)   │                      │  (XRPL account)  │
└─────────────┘                      └────────┬─────────┘
                                              │
                              AXL validators observe
                              and reach consensus
                                              │
                                     ┌────────▼─────────┐
                                     │  Axelar Network  │
                                     │  (validators +   │
                                     │   relayers)      │
                                     └────────┬─────────┘
                                              │
                             signed mint/release instruction
                                              │
┌─────────────┐     mint wXRP        ┌────────▼─────────┐
│  EVM Chain  │ ◄── to user addr ─── │  EVM Gateway     │
│ (Ethereum,  │                      │  contract        │
│  Polygon…)  │                      └──────────────────┘
└─────────────┘
```

### Bridge Flow: XRPL → EVM

1. User sends XRP to the Axelar gateway account on XRPL L1
2. Memo encodes the destination chain and EVM address
3. Axelar validators observe the Payment transaction
4. After sufficient confirmations, validators reach consensus
5. Gateway contract on the destination EVM chain mints wrapped XRP (wXRP) to the user's address

### Bridge Flow: EVM → XRPL

1. User calls `sendToken()` on the EVM Gateway contract, specifying "xrpl" as destination chain and XRPL address
2. Axelar validators observe the EVM event
3. After consensus, federators sign a Payment transaction on XRPL
4. XRP/tokens released to the user's XRPL address

### General Message Passing (GMP)

GMP allows arbitrary data payloads to be sent cross-chain alongside (or without) token transfers:

```
Source chain: callContract(destinationChain, destinationAddress, payload)
    → Axelar validators encode and relay
        → Destination chain: execute(sourceChain, sourceAddress, payload)
```

Use cases: cross-chain governance, NFT bridging with metadata, DeFi composability across chains.

---

## Token Support

| Token | XRPL Currency | EVM Representation | Notes |
|-------|---------------|-------------------|-------|
| XRP | Native XRP | wXRP (ERC-20) | Bridge locks on L1, mints on EVM |
| RLUSD | RLUSD (Ripple issuer) | RLUSD (ERC-20) | Stablecoin |
| USDC | USDC trust line | USDC (native ERC-20) | Circle-issued |
| USDT | USDT trust line | USDT (ERC-20) | Tether |
| AXL | AXL trust line | AXL (ERC-20) | Axelar native |

Fees are paid in AXL or the native gas token of the destination chain. Always check current supported assets at docs.axelar.dev/resources/mainnet.

---

## Python: Bridge XRP from XRPL to EVM via Axelar

```python
import httpx
import json
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import Payment, Memo, MemoData, MemoType
from xrpl.wallet import Wallet
from xrpl.transaction import submit_and_wait
from xrpl.utils import xrp_to_drops

# Axelar gateway account on XRPL (verify from official docs)
AXELAR_GATEWAY_XRPL = "rAxelarGatewayAddressHere"  # replace with real address
XRPL_RPC = "https://s1.ripple.com:51234"

def encode_axelar_memo(destination_chain: str, destination_address: str) -> dict:
    """
    Axelar expects a memo encoding the destination chain and address.
    Format varies — check latest Axelar XRPL docs for exact encoding.
    """
    payload = {
        "destination_chain": destination_chain,
        "destination_address": destination_address
    }
    memo_data = json.dumps(payload).encode().hex().upper()
    return {
        "Memo": {
            "MemoData": memo_data,
            "MemoType": "6178656C61722D62726964676500"  # "axelar-bridge" hex
        }
    }

def bridge_xrp_to_evm(
    wallet: Wallet,
    destination_chain: str,        # e.g. "ethereum"
    destination_evm_address: str,  # e.g. "0xabc..."
    amount_xrp: float
) -> dict:
    client = JsonRpcClient(XRPL_RPC)

    memo = encode_axelar_memo(destination_chain, destination_evm_address)

    tx = Payment(
        account=wallet.classic_address,
        destination=AXELAR_GATEWAY_XRPL,
        amount=str(xrp_to_drops(amount_xrp)),
        memos=[Memo(
            memo_data=MemoData(memo["Memo"]["MemoData"]),
            memo_type=MemoType(memo["Memo"]["MemoType"])
        )]
    )

    result = submit_and_wait(tx, client, wallet)
    return {
        "xrpl_tx_hash": result.result["hash"],
        "status": result.result["meta"]["TransactionResult"],
        "axelar_tracking": f"https://axelarscan.io/transfer/{result.result['hash']}"
    }

# Usage
wallet = Wallet.from_seed("sYOURSEEDHERE")
result = bridge_xrp_to_evm(
    wallet=wallet,
    destination_chain="ethereum",
    destination_evm_address="0xYourEthAddress",
    amount_xrp=10.0
)
print(result)
```

---

## Python: Query Axelar Transfer Status

```python
import httpx

AXELARSCAN_API = "https://api.axelarscan.io"

async def get_transfer_status(tx_hash: str) -> dict:
    """Query Axelar for the status of a cross-chain transfer."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{AXELARSCAN_API}/transfer",
            params={"txHash": tx_hash}
        )
        response.raise_for_status()
        data = response.json()

    transfer = data.get("data", {})
    return {
        "status": transfer.get("status", "unknown"),
        "source_chain": transfer.get("source", {}).get("chain"),
        "destination_chain": transfer.get("destination", {}).get("chain"),
        "amount": transfer.get("amount"),
        "asset": transfer.get("asset"),
        "created_at": transfer.get("created_at"),
        "axelarscan_url": f"https://axelarscan.io/transfer/{tx_hash}"
    }

async def get_supported_assets(chain: str = "xrpl") -> list:
    """Get all assets supported for a given chain."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{AXELARSCAN_API}/assets",
            params={"chain": chain}
        )
        response.raise_for_status()
        return response.json().get("data", [])

async def get_chain_configs() -> dict:
    """Get all chain configs including XRPL gateway addresses."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{AXELARSCAN_API}/chains")
        response.raise_for_status()
        return response.json()

# Usage
import asyncio
status = asyncio.run(get_transfer_status("YOUR_XRPL_TX_HASH"))
print(status)
```

---

## Python: Monitor Bridge Events via Axelarscan

```python
import httpx
import asyncio
from datetime import datetime, timedelta

AXELARSCAN_API = "https://api.axelarscan.io"

async def poll_transfer_until_complete(
    tx_hash: str,
    timeout_minutes: int = 30,
    poll_interval_seconds: int = 15
) -> dict:
    """Poll Axelarscan until a cross-chain transfer completes or times out."""
    deadline = datetime.utcnow() + timedelta(minutes=timeout_minutes)

    async with httpx.AsyncClient() as client:
        while datetime.utcnow() < deadline:
            try:
                response = await client.get(
                    f"{AXELARSCAN_API}/transfer",
                    params={"txHash": tx_hash}
                )
                data = response.json().get("data", {})
                status = data.get("status")

                print(f"[{datetime.utcnow().isoformat()}] Status: {status}")

                if status in ("executed", "success"):
                    return {"status": "complete", "data": data}
                if status in ("failed", "error"):
                    return {"status": "failed", "data": data}

            except httpx.HTTPError as e:
                print(f"HTTP error polling status: {e}")

            await asyncio.sleep(poll_interval_seconds)

    return {"status": "timeout", "tx_hash": tx_hash}

async def get_recent_xrpl_transfers(limit: int = 20) -> list:
    """Get recent transfers involving the XRPL chain."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{AXELARSCAN_API}/transfers",
            params={
                "sourceChain": "xrpl",
                "size": limit
            }
        )
        response.raise_for_status()
        return response.json().get("data", [])
```

---

## JSON: XRPL Payment to Axelar Gateway

```json
{
  "TransactionType": "Payment",
  "Account": "rSenderAddress",
  "Destination": "rAxelarGatewayAccount",
  "Amount": "10000000",
  "Fee": "12",
  "Sequence": 123456,
  "Flags": 0,
  "Memos": [
    {
      "Memo": {
        "MemoType": "64657374696E6174696F6E5F636861696E",
        "MemoData": "657468657265756D"
      }
    },
    {
      "Memo": {
        "MemoType": "64657374696E6174696F6E5F61646472657373",
        "MemoData": "307861626331323300000000000000000000000000000000000000"
      }
    }
  ]
}
```

Note: Always consult official Axelar XRPL bridge docs for the exact memo format and gateway address. The format changes as the protocol evolves.

---

## API Endpoints

### Axelarscan API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `https://api.axelarscan.io/transfer` | GET | Query transfer by txHash |
| `https://api.axelarscan.io/transfers` | GET | List recent transfers |
| `https://api.axelarscan.io/assets` | GET | Supported assets per chain |
| `https://api.axelarscan.io/chains` | GET | All chain configs |
| `https://api.axelarscan.io/stats` | GET | Bridge volume stats |

### Query Parameters (transfers)

| Parameter | Description |
|-----------|-------------|
| `txHash` | XRPL or EVM transaction hash |
| `sourceChain` | Source chain name (e.g. "xrpl") |
| `destinationChain` | Destination chain name (e.g. "ethereum") |
| `size` | Number of results (default 20) |
| `from` | Offset for pagination |

---

## Error Handling Patterns

```python
import httpx
from typing import Optional

class AxelarBridgeError(Exception):
    pass

class TransferStuckError(AxelarBridgeError):
    pass

async def safe_get_transfer_status(tx_hash: str) -> Optional[dict]:
    """Error-safe status check with retries."""
    retries = 3
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.axelarscan.io/transfer",
                    params={"txHash": tx_hash}
                )
                if response.status_code == 404:
                    # Transfer not yet indexed — normal for first few minutes
                    print(f"Transfer not yet indexed (attempt {attempt+1}/{retries})")
                    await asyncio.sleep(15)
                    continue
                response.raise_for_status()
                return response.json().get("data")

        except httpx.TimeoutException:
            print(f"Timeout on attempt {attempt+1}")
            await asyncio.sleep(5 * (attempt + 1))
        except httpx.HTTPStatusError as e:
            if e.response.status_code >= 500:
                print(f"Axelarscan server error: {e}")
                await asyncio.sleep(10)
            else:
                raise

    return None

def validate_axelar_destination(chain: str, address: str) -> bool:
    """Validate destination chain/address before sending."""
    supported_chains = {
        "ethereum": lambda a: a.startswith("0x") and len(a) == 42,
        "polygon": lambda a: a.startswith("0x") and len(a) == 42,
        "avalanche": lambda a: a.startswith("0x") and len(a) == 42,
        "binance": lambda a: a.startswith("0x") and len(a) == 42,
        "xrpl": lambda a: a.startswith("r") and 25 <= len(a) <= 34,
    }
    validator = supported_chains.get(chain.lower())
    if not validator:
        raise AxelarBridgeError(f"Unsupported chain: {chain}")
    if not validator(address):
        raise AxelarBridgeError(f"Invalid address for {chain}: {address}")
    return True
```

---

## Practical Workflow: Full Cross-Chain XRP Transfer

```python
import asyncio
import httpx
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.transaction import submit_and_wait

async def full_bridge_workflow(
    xrpl_seed: str,
    destination_chain: str,
    destination_address: str,
    amount_xrp: float
) -> dict:
    """
    Complete workflow to bridge XRP from XRPL to an EVM chain via Axelar.
    Returns XRPL tx hash and tracks until Axelar confirms completion.
    """
    wallet = Wallet.from_seed(xrpl_seed)

    # 1. Validate destination
    validate_axelar_destination(destination_chain, destination_address)
    print(f"Bridging {amount_xrp} XRP to {destination_chain}:{destination_address}")

    # 2. Send Payment to Axelar gateway
    result = bridge_xrp_to_evm(wallet, destination_chain, destination_address, amount_xrp)
    xrpl_hash = result["xrpl_tx_hash"]
    print(f"XRPL tx submitted: {xrpl_hash}")

    if result["status"] != "tesSUCCESS":
        raise AxelarBridgeError(f"XRPL tx failed: {result['status']}")

    # 3. Wait for Axelar indexing (typically 1-2 minutes for XRPL finality)
    print("Waiting for Axelar to index XRPL transaction...")
    await asyncio.sleep(90)

    # 4. Poll until complete
    print("Polling Axelar for cross-chain transfer completion...")
    final_status = await poll_transfer_until_complete(xrpl_hash, timeout_minutes=30)

    return {
        "xrpl_tx_hash": xrpl_hash,
        "axelar_status": final_status["status"],
        "axelarscan": f"https://axelarscan.io/transfer/{xrpl_hash}"
    }
```

---

## GMP Example: Call EVM Contract from XRPL

General Message Passing allows XRPL transactions to trigger arbitrary EVM smart contract calls.

```python
import json

def encode_gmp_memo(
    destination_chain: str,
    destination_contract: str,
    payload: dict
) -> list:
    """
    Encode an Axelar GMP call as XRPL memos.
    The payload is ABI-encoded or JSON, depending on the destination contract.
    """
    payload_hex = json.dumps(payload).encode().hex().upper()
    return [
        {
            "Memo": {
                "MemoType": "64657374436861696E",  # "destChain"
                "MemoData": destination_chain.encode().hex().upper()
            }
        },
        {
            "Memo": {
                "MemoType": "64657374436F6E7472616374",  # "destContract"
                "MemoData": destination_contract.replace("0x", "").upper()
            }
        },
        {
            "Memo": {
                "MemoType": "7061796C6F6164",  # "payload"
                "MemoData": payload_hex
            }
        }
    ]
```

```json
{
  "TransactionType": "Payment",
  "Account": "rGMPSender",
  "Destination": "rAxelarGateway",
  "Amount": "1000000",
  "Memos": [
    {
      "Memo": {
        "MemoType": "64657374436861696E",
        "MemoData": "657468657265756D"
      }
    },
    {
      "Memo": {
        "MemoType": "64657374436F6E7472616374",
        "MemoData": "ABCDEF1234567890ABCDEF1234567890ABCDEF12"
      }
    },
    {
      "Memo": {
        "MemoType": "7061796C6F6164",
        "MemoData": "7B22616374696F6E223A22737761705F616E645F6272696467655F6261636B227D"
      }
    }
  ]
}
```

---

## Bridge Security Model

| Property | Value |
|----------|-------|
| Validator count | 75+ validators (open set, AXL-staked) |
| Consensus threshold | 2/3+ validator set |
| Slashing | AXL slashed for misbehavior |
| Finality wait | 2-4 XRPL ledger closes before relay |
| Rate limits | Destination chain contracts enforce limits |
| Emergency pause | Gateway admin multisig can pause |
| Audits | Multiple third-party security audits |

Unlike federator-based bridges (where a small fixed set controls funds), Axelar uses an open, slashable validator set — reducing trust assumptions.

---

## Monitoring and Observability

```python
async def get_bridge_metrics() -> dict:
    """Get current Axelar bridge health metrics."""
    async with httpx.AsyncClient() as client:
        stats = await client.get("https://api.axelarscan.io/stats")
        tvl = await client.get("https://api.axelarscan.io/tvl")

        return {
            "stats": stats.json(),
            "tvl": tvl.json(),
            "dashboard": "https://axelarscan.io"
        }

async def get_xrpl_gateway_balance() -> dict:
    """Check the Axelar XRPL gateway account balance."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://s1.ripple.com:51234",
            json={
                "method": "account_info",
                "params": [{"account": AXELAR_GATEWAY_XRPL, "ledger_index": "validated"}]
            }
        )
        data = response.json()
        balance_drops = int(data["result"]["account_data"]["Balance"])
        return {
            "xrp_balance": balance_drops / 1_000_000,
            "drops": balance_drops
        }
```

---

## Resources

- Axelar documentation: https://docs.axelar.dev
- Supported chains list: https://docs.axelar.dev/resources/mainnet
- Axelarscan explorer: https://axelarscan.io
- XRPL integration guide: https://docs.axelar.dev/dev/axelarjs-sdk/token-transfer-dep-addr
- GMP documentation: https://docs.axelar.dev/dev/general-message-passing/overview

---

## Related Files

- `50-xrpl-evm-sidechain.md` — XRPL's native EVM sidechain (different from Axelar bridges)
- `55-xrpl-sidechain-interop.md` — Full sidechain interoperability patterns
- `49-xrpl-flare-ftso.md` — Flare's alternative cross-chain approach with F-Assets
- `52-xrpl-l1-reference.md` — XRPL L1 Payment transaction reference
- `53-xrpl-wallets-auth.md` — Wallet setup for sending bridge transactions
