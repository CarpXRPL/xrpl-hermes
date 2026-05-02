# Xahau Hooks — On-Ledger Smart Contracts for XRPL

## Overview

Xahau is an XRPL-protocol sidechain that implements **Hooks** — a smart contract-like system that executes WebAssembly (WASM) programs at the transaction level. Unlike the XRPL EVM Sidechain (which runs Solidity), Hooks run natively inside the ledger consensus process, executing before and after every matching transaction.

**Key difference from EVM:** Hooks are not general-purpose Turing-complete contracts. They are purpose-built reactive programs: they fire on transactions, can accept/reject/modify them, read/write small amounts of state, and emit new transactions. This makes them ideal for automating ledger behavior without a separate execution environment.

**Status:** Hooks v3+ live on Xahau mainnet. Hooks amendment proposed for XRPL mainnet (pending community vote as of 2026).

**Xahau native token:** XAH

---

## Architecture

### Transaction Lifecycle with Hooks

```
Incoming Transaction
        ↓
Hook (pre-flight / "otxn" hooks)
  ├── Read tx fields
  ├── Read/write hook state
  ├── Validate conditions
  └── accept() or rollback()
        ↓ (if accepted)
Core Ledger Logic
  (balance changes, offer matching, etc.)
        ↓
Hook (post-flight / "callback" hooks)
  ├── React to outcome
  ├── Emit new transactions
  └── accept() to finalize
        ↓
Validated Transaction
```

### Hook Execution Model

1. Hook is installed on an account via `HookSet` transaction
2. `HookOn` bitmask specifies which transaction types trigger the hook
3. When a matching transaction involves the account, the hook fires
4. Hook receives context: the originating transaction (`otxn`), ledger state, hook parameters
5. Hook calls `accept()` to let the transaction proceed, or `rollback()` to reject it
6. Hook can emit new transactions from within the hook (up to 16 per hook execution)

### Hook State

Hooks have a persistent key-value store on the ledger:
- Key: 32 bytes
- Value: up to 128 bytes
- Stored in `HookState` ledger entries
- Subject to reserve requirements (0.2 XAH per state entry)
- Cleared when hook is removed, unless namespace sharing is used

---

## Hook Development

### C SDK (Recommended)

Hooks are written in C, compiled to WASM using the Hooks C SDK:

```bash
# Install hooks-builder
npm install -g @xrplf/hooks-builder

# Or build manually with emcc
emcc hook.c -o hook.wasm \
  -I /path/to/hookapi \
  -O3 \
  --no-entry \
  -e "cbak,hook" \
  -s WASM=1 \
  -s EXPORTED_FUNCTIONS='["_hook","_cbak"]'
```

### Hook API Functions Reference

```c
#include "hookapi.h"

// Transaction I/O
int64_t otxn_field(uint32_t write_ptr, uint32_t write_len, uint32_t field_id);
int64_t otxn_type(void);          // Returns transaction type (ttPAYMENT=0, etc.)
int64_t otxn_id(uint32_t write_ptr, uint32_t write_len, uint32_t flags);

// Account info
int64_t hook_account(uint32_t write_ptr, uint32_t write_len);
int64_t account_balance(uint32_t accid_ptr, uint32_t accid_len);
int64_t account_seq(uint32_t accid_ptr, uint32_t accid_len, uint32_t flags);

// State
int64_t state(uint32_t write_ptr, uint32_t write_len,
              uint32_t kread_ptr, uint32_t kread_len);
int64_t state_set(uint32_t read_ptr, uint32_t read_len,
                  uint32_t kread_ptr, uint32_t kread_len);
int64_t state_foreign(uint32_t write_ptr, uint32_t write_len,
                      uint32_t kread_ptr, uint32_t kread_len,
                      uint32_t aread_ptr, uint32_t aread_len,
                      uint32_t nread_ptr, uint32_t nread_len);

// Float math (no floating point in WASM)
int64_t float_set(int32_t exponent, int64_t mantissa);
int64_t float_multiply(int64_t float1, int64_t float2);
int64_t float_divide(int64_t float1, int64_t float2);
int64_t float_sum(int64_t float1, int64_t float2);
int64_t float_compare(int64_t float1, int64_t float2, uint32_t mode);
int64_t float_int(int64_t float1, uint32_t decimal_places, uint32_t absolute);

// Emit new transactions
int64_t etxn_reserve(uint32_t count);
int64_t etxn_details(uint32_t write_ptr, uint32_t write_len);
int64_t emit(uint32_t write_ptr, uint32_t write_len,
             uint32_t read_ptr, uint32_t read_len);

// Utilities
int64_t util_sha512half(uint32_t write_ptr, uint32_t write_len,
                        uint32_t read_ptr, uint32_t read_len);
int64_t util_verify(uint32_t vread_ptr, uint32_t vread_len,
                    uint32_t dread_ptr, uint32_t dread_len,
                    uint32_t kread_ptr, uint32_t kread_len);

// Ledger
int64_t ledger_seq(void);
int64_t ledger_last_time(void);
int64_t ledger_last_hash(uint32_t write_ptr, uint32_t write_len);
int64_t ledger_nonce(uint32_t write_ptr, uint32_t write_len);

// Control
int64_t accept(uint32_t read_ptr, uint32_t read_len, int64_t error_code);
int64_t rollback(uint32_t read_ptr, uint32_t read_len, int64_t error_code);
```

### Transaction Type Constants

```c
#define ttPAYMENT           0
#define ttESCROW_CREATE     1
#define ttESCROW_FINISH     2
#define ttACCOUNT_SET       3
#define ttESCROW_CANCEL     4
#define ttREGULAR_KEY_SET   5
#define ttOFFER_CREATE      7
#define ttOFFER_CANCEL      8
#define ttTRUST_SET         20
#define ttSIGNER_LIST_SET   12
#define ttHOOK_SET          22
#define ttNFTOKEN_MINT      25
#define ttNFTOKEN_BURN      26
#define ttNFTOKEN_CREATE_OFFER  27
#define ttNFTOKEN_ACCEPT_OFFER  29
#define ttINVOKE            99
```

---

## Hook Examples

### Example 1: Transfer Fee Hook (Tax on Payments)

```c
#include "hookapi.h"

#define TAX_RATE_BPS 100  // 1% tax (100 basis points)

int64_t hook(uint32_t reserved) {
    // Only fire on payment transactions
    if (otxn_type() != ttPAYMENT)
        accept(SBUF("Non-payment, skip"), 0);

    // Get the amount being transferred
    uint8_t amount_buf[49];
    int64_t amount_len = otxn_field(SBUF(amount_buf), sfAmount);
    if (amount_len < 0)
        rollback(SBUF("Could not read Amount"), 1);

    // Only process XRP payments (amount is a string of drops)
    // IOU amounts are encoded differently
    if (amount_buf[0] & 0x80) {  // High bit set = IOU
        accept(SBUF("IOU payment, skip"), 0);
    }

    // Extract XRP amount (drops)
    int64_t drops = 0;
    for (int i = 0; i < amount_len; i++) {
        drops = drops * 10 + (amount_buf[i] - '0');
    }

    // Calculate tax
    int64_t tax_drops = (drops * TAX_RATE_BPS) / 10000;

    // Get the hook account (where fee should go)
    uint8_t hook_accid[20];
    hook_account(SBUF(hook_accid));

    // Emit a fee payment to the hook account
    uint8_t emitted_txn[300];
    int64_t etxn_len = etxn_details(SBUF(emitted_txn));

    // Set destination to hook account
    // (actual emission requires encoding the full transaction)

    accept(SBUF("Payment accepted"), 0);
    return 0;
}

int64_t cbak(uint32_t reserved) {
    accept(SBUF("Callback accepted"), 0);
    return 0;
}
```

### Example 2: Whitelist Hook (Access Control)

```c
#include "hookapi.h"

int64_t hook(uint32_t reserved) {
    if (otxn_type() != ttPAYMENT)
        accept(SBUF("Not a payment"), 0);

    // Get the sender account
    uint8_t sender[20];
    if (otxn_field(SBUF(sender), sfAccount) < 0)
        rollback(SBUF("Cannot read sender"), 1);

    // Check if sender is in the whitelist (stored in hook state)
    uint8_t state_val[1];
    int64_t state_len = state(SBUF(state_val), SBUF(sender));

    if (state_len <= 0) {
        // Sender not in whitelist
        rollback(SBUF("Sender not whitelisted"), 2);
    }

    accept(SBUF("Sender is whitelisted"), 0);
    return 0;
}
```

### Example 3: Counter Hook (State Tracking)

```c
#include "hookapi.h"

#define STATE_KEY "counter\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0"

int64_t hook(uint32_t reserved) {
    // Read current counter
    uint8_t counter_buf[8] = {0};
    uint8_t key[32] = STATE_KEY;

    state(SBUF(counter_buf), SBUF(key));

    // Increment counter
    uint64_t counter = 0;
    for (int i = 0; i < 8; i++) {
        counter = (counter << 8) | counter_buf[i];
    }
    counter++;

    // Write back
    for (int i = 7; i >= 0; i--) {
        counter_buf[i] = counter & 0xFF;
        counter >>= 8;
    }
    state_set(SBUF(counter_buf), SBUF(key));

    accept(SBUF("Counter incremented"), 0);
    return 0;
}
```

---

## HookSet Transaction

```json
{
  "TransactionType": "HookSet",
  "Account": "rHookOwnerAddress",
  "Hooks": [
    {
      "Hook": {
        "CreateCode": "AGFzbQEAAAABBgFgAX8BfwMCAQAFBAEBcAEGCAEBfwEBgAIDCQEABxABBGhvb2sAAAoNAQsBfyAAEAEPCwAKBgEAQQALAA==",
        "HookOn": "0000000000000000000000000000000000000000000000000000000000000000",
        "HookNamespace": "CAFECAFE0000000000000000000000000000000000000000000000000000",
        "HookApiVersion": 0,
        "HookParameters": [
          {
            "HookParameter": {
              "HookParameterName": "54415852415445",
              "HookParameterValue": "64"
            }
          }
        ]
      }
    }
  ],
  "Fee": "1000000",
  "Sequence": 123456
}
```

### HookOn Bitmask

The `HookOn` field is a 64-bit bitmask where bit N = 1 means the hook fires on transaction type N.

```python
def compute_hookon(tx_types: list) -> str:
    """
    Compute the HookOn bitmask for a list of transaction types.
    tx_types: list of ttXXX integer constants
    """
    bitmask = 0
    for tt in tx_types:
        bitmask |= (1 << tt)
    # Convert to 64-character hex string (32 bytes)
    return format(bitmask, '064x').upper()

# Examples
FIRE_ON_ALL = "0000000000000000000000000000000000000000000000000000000000000000"
FIRE_ON_PAYMENT = compute_hookon([0])  # ttPAYMENT = 0
FIRE_ON_OFFER = compute_hookon([7, 8])  # ttOFFER_CREATE + ttOFFER_CANCEL
```

---

## Python: Deploy and Manage Hooks via xrpl-py

```python
import httpx
import base64
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.transaction import submit_and_wait

XAHAU_RPC = "https://xahau.network"  # Xahau mainnet

def load_wasm_as_base64(wasm_path: str) -> str:
    """Load compiled WASM hook binary and encode as base64."""
    with open(wasm_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def install_hook(
    wallet: Wallet,
    wasm_base64: str,
    hook_on: str = "0000000000000000000000000000000000000000000000000000000000000000",
    namespace: str = "CAFECAFE000000000000000000000000",
    parameters: dict = None
) -> dict:
    """Install a Hook on an account."""
    client = JsonRpcClient(XAHAU_RPC)

    hook_entry = {
        "CreateCode": wasm_base64,
        "HookOn": hook_on,
        "HookNamespace": namespace,
        "HookApiVersion": 0,
    }

    if parameters:
        hook_entry["HookParameters"] = [
            {
                "HookParameter": {
                    "HookParameterName": k.encode().hex().upper(),
                    "HookParameterValue": str(v).encode().hex().upper()
                }
            }
            for k, v in parameters.items()
        ]

    tx_data = {
        "TransactionType": "HookSet",
        "Account": wallet.classic_address,
        "Hooks": [{"Hook": hook_entry}]
    }

    # Submit via raw JSON-RPC (xrpl-py HookSet support may require custom tx)
    import xrpl.models.transactions
    # Build a GenericTransaction for HookSet
    from xrpl.models.transactions import Transaction

    result = client.request({
        "method": "submit",
        "params": [{
            "tx_json": tx_data,
            "secret": wallet.seed
        }]
    })

    return result.result

def remove_hook(wallet: Wallet, hook_index: int = 0) -> dict:
    """Remove a hook from an account."""
    client = JsonRpcClient(XAHAU_RPC)

    tx_data = {
        "TransactionType": "HookSet",
        "Account": wallet.classic_address,
        "Hooks": [{"Hook": {}}]  # Empty hook = delete
    }

    result = client.request({
        "method": "submit",
        "params": [{"tx_json": tx_data, "secret": wallet.secret}]
    })
    return result.result

async def get_account_hooks(account: str) -> list:
    """Get all hooks installed on an account."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            XAHAU_RPC,
            json={
                "method": "account_info",
                "params": [{
                    "account": account,
                    "ledger_index": "validated"
                }]
            }
        )
        data = response.json()
        hooks = data["result"].get("account_data", {}).get("Hooks", [])

    return [
        {
            "hook_hash": h["Hook"].get("HookHash"),
            "hook_on": h["Hook"].get("HookOn"),
            "namespace": h["Hook"].get("HookNamespace"),
            "flags": h["Hook"].get("Flags", 0)
        }
        for h in hooks
    ]

async def get_hook_state(account: str, namespace_id: str, key_hex: str) -> str:
    """Read a value from hook state storage."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            XAHAU_RPC,
            json={
                "method": "ledger_entry",
                "params": [{
                    "hook_state": {
                        "account": account,
                        "key": key_hex,
                        "namespace_id": namespace_id
                    }
                }]
            }
        )
        result = response.json()["result"]
        return result.get("node", {}).get("HookStateData")
```

---

## Python: Monitor Hook Executions

```python
import asyncio
import websockets
import json

async def monitor_hook_executions(account: str):
    """Monitor an account for hook-triggered transactions via WebSocket."""
    async with websockets.connect("wss://xahau.network") as ws:
        # Subscribe to account transactions
        await ws.send(json.dumps({
            "command": "subscribe",
            "accounts": [account]
        }))

        while True:
            message = await ws.recv()
            data = json.loads(message)

            if data.get("type") == "transaction":
                tx = data["transaction"]
                meta = data.get("meta", {})

                # Check for hook execution results
                hooks_exec = meta.get("HookExecutions", [])
                if hooks_exec:
                    for he in hooks_exec:
                        exec_data = he.get("HookExecution", {})
                        print(f"Hook executed on tx: {tx.get('hash')}")
                        print(f"  Hook hash: {exec_data.get('HookHash')}")
                        print(f"  Return code: {exec_data.get('HookReturnCode')}")
                        print(f"  Return string: {exec_data.get('HookReturnString')}")
                        print(f"  Emitted txn count: {exec_data.get('HookEmittedTxnCount', 0)}")
```

---

## JSON: Hook Transaction Examples

### Invoke Transaction (Explicit Hook Trigger)

```json
{
  "TransactionType": "Invoke",
  "Account": "rCaller",
  "Destination": "rHookAccount",
  "Blob": "48656C6C6F20576F726C64",
  "Fee": "100",
  "Sequence": 999,
  "HookParameters": [
    {
      "HookParameter": {
        "HookParameterName": "414354494F4E",
        "HookParameterValue": "535741505F544F4B454E"
      }
    }
  ]
}
```

### HookSet with Parameters

```json
{
  "TransactionType": "HookSet",
  "Account": "rMyAccount",
  "Hooks": [
    {
      "Hook": {
        "CreateCode": "AGFzbQEAAAA...",
        "HookOn": "0000000000000000",
        "HookNamespace": "CAFECAFE000000000000000000000000",
        "HookApiVersion": 0,
        "HookParameters": [
          {
            "HookParameter": {
              "HookParameterName": "4D494E5F414D4F554E54",
              "HookParameterValue": "000F4240"
            }
          }
        ],
        "Flags": 0
      }
    }
  ],
  "Fee": "2000000"
}
```

---

## Xahau vs XRPL Main Network

| Feature | XRPL Mainnet | Xahau |
|---------|-------------|-------|
| Hooks | Proposed (not yet) | Live (v3+) |
| Consensus | XRPL Consensus Protocol | Proof of Burn + UNL |
| Native token | XRP | XAH |
| AMM | Yes (XLS-30) | Yes |
| NFTs | Yes (XLS-20) | Yes |
| Smart contracts | Via EVM Sidechain only | Via Hooks (native) |
| Finality | 3-5 seconds | 3-5 seconds |
| TPS | 1500+ | 1500+ |

---

## Use Cases for Hooks

| Use Case | Hook Logic |
|----------|-----------|
| Transfer tax/fee | On payment, emit 1% to treasury |
| Token burn | On payment, emit burn of % |
| Whitelist | On payment, reject if sender not in state |
| Royalty enforcement | On NFT offer accept, emit royalty payment |
| Payment splitting | On payment, emit splits to multiple recipients |
| Rate limiting | On payment, reject if too many in timeframe |
| Automated escrow | On condition met, emit release payment |
| KYC gate | On any tx, reject if account not flagged as KYC'd |
| Multi-sig lite | Accumulate signatures in state, release on threshold |

---

## Error Handling Patterns

```python
class HookDeploymentError(Exception):
    pass

class HookStateError(Exception):
    pass

HOOK_ROLLBACK_CODES = {
    1: "Invalid transaction format",
    2: "Sender not whitelisted",
    3: "Amount below minimum",
    4: "Rate limit exceeded",
    5: "Account not authorized",
}

def handle_hook_rejection(tx_result: str, return_code: int = None) -> None:
    """Handle hook rejection results."""
    if return_code and return_code in HOOK_ROLLBACK_CODES:
        raise HookDeploymentError(
            f"Hook rejected transaction: {HOOK_ROLLBACK_CODES[return_code]}"
        )

    error_map = {
        "tecHOOK_REJECTED": "Transaction rejected by hook",
        "tecINSUFFICIENT_RESERVE": "Insufficient reserve for hook state storage",
        "temINVALID_FLAG": "Invalid HookOn flags",
        "temMALFORMED": "Malformed HookSet transaction",
    }
    if tx_result in error_map:
        raise HookDeploymentError(error_map[tx_result])

async def validate_hook_wasm(wasm_bytes: bytes) -> dict:
    """
    Validate WASM hook before deployment.
    Basic checks: magic bytes, export presence.
    """
    WASM_MAGIC = b'\x00asm'
    if wasm_bytes[:4] != WASM_MAGIC:
        raise HookDeploymentError("Invalid WASM: missing magic bytes")

    # Check for required exports (hook and cbak functions)
    wasm_text = wasm_bytes.decode("latin-1")
    has_hook = "hook" in wasm_text
    has_cbak = "cbak" in wasm_text

    return {
        "valid": has_hook and has_cbak,
        "has_hook_export": has_hook,
        "has_cbak_export": has_cbak,
        "size_bytes": len(wasm_bytes)
    }
```

---

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `https://xahau.network` | Xahau mainnet JSON-RPC |
| `wss://xahau.network` | Xahau mainnet WebSocket |
| `https://xahau-test.net` | Xahau testnet |
| `https://xahauexplorer.com` | Block explorer |
| `https://hooks-builder.xrpl.org` | Online hook builder/tester |

```python
async def get_xahau_server_info() -> dict:
    """Get Xahau server info including supported amendments."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            XAHAU_RPC,
            json={"method": "server_info", "params": [{}]}
        )
        info = response.json()["result"]["info"]
        return {
            "version": info.get("build_version"),
            "ledger": info.get("validated_ledger", {}).get("seq"),
            "hooks_amendment": "Hooks" in info.get("amendments", []),
            "load_factor": info.get("load_factor")
        }
```

---

## Resources

- Xahau GitHub: https://github.com/Xahau/xahaud
- Hooks documentation: https://xrpl-hooks.readme.io
- Hooks C SDK: https://github.com/XRPL-Labs/hook-cleaner-c
- Hooks Builder (online IDE): https://hooks-builder.xrpl.org
- Xahau Explorer: https://xahauexplorer.com
- Hooks specification (XRPL): https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0030d-hooks

---

## Related Files

- `50-xrpl-evm-sidechain.md` — Alternative smart contract platform for XRPL
- `52-xrpl-l1-reference.md` — XRPL L1 transaction types that hooks can intercept
- `53-xrpl-wallets-auth.md` — Joey wallet for Hooks development
- `47-xrpl-arweave-storage.md` — Store hook audit logs permanently on Arweave

---

## URITokens (XLS-70) — Linking Off-Chain Data to On-Chain State

### Overview

URITokens are a Xahau-native NFT-like primitive that links an on-chain token to an off-chain resource via a URI. Unlike XRPL mainnet NFTs (XLS-20), URITokens are first-class ledger objects — they are simpler, cheaper, and directly integrated with the Hooks execution model.
> **Note:** URITokens use XLS-70 on Xahau. This is a different XLS-70 than XRPL Credentials (also XLS-70). They share a number by coincidence across two ecosystems.

**Key differences vs. XLS-20 NFTs:**
- No broker-mediated transfers — direct peer-to-peer
- URI is stored directly in the ledger object (immutable or mutable depending on minting flags)
- Hooks can react to URIToken transfer events natively
- No royalty enforcement (enforced via Hooks instead)
- Lower reserve requirement per token

### URIToken Transactions

| Transaction | Purpose |
|---|---|
| `URITokenMint` | Mint a new URIToken on your account |
| `URITokenBurn` | Destroy a URIToken you own |
| `URITokenBuy` | Buy a URIToken listed for sale |
| `URITokenCreateSellOffer` | List a URIToken for sale at a price |
| `URITokenCancelSellOffer` | Cancel an active sell offer |

### Minting a URIToken

```python
import httpx
import json

XAHAU_RPC = "https://xahau.network"


async def mint_uri_token(
    account: str,
    uri: str,                          # points to off-chain metadata (IPFS, Arweave, HTTPS)
    digest: str = "",                  # SHA-256 hash of the off-chain content (hex)
    flags: int = 0,                    # 1 = tfBurnable
    destination: str = "",             # auto-transfer to this address on mint
) -> dict:
    """
    Mint a URIToken on Xahau.
    URI should be a content-addressed link (IPFS CID preferred).
    digest provides integrity verification for the off-chain data.
    """
    tx = {
        "TransactionType": "URITokenMint",
        "Account": account,
        "URI": uri.encode().hex().upper(),
        "Flags": flags,
        "Fee": "12",
        "Sequence": 0,  # fill from account_info
    }
    if digest:
        tx["Digest"] = digest.upper()
    if destination:
        tx["Destination"] = destination

    # In production: sign with xrpl-py or Xaman, then submit
    return {"unsigned_tx": tx, "note": "Sign with Xaman or xrpl-py before submitting"}


async def get_uri_token(token_id: str) -> dict:
    """Fetch a URIToken ledger object by ID."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            XAHAU_RPC,
            json={
                "method": "ledger_entry",
                "params": [{
                    "uri_token": token_id,
                    "ledger_index": "validated",
                }]
            }
        )
        node = resp.json()["result"].get("node", {})
        uri_hex = node.get("URI", "")
        return {
            "token_id": token_id,
            "owner": node.get("Owner"),
            "uri": bytes.fromhex(uri_hex).decode("utf-8", errors="replace"),
            "digest": node.get("Digest"),
            "flags": node.get("Flags"),
            "amount": node.get("Amount"),  # price if listed for sale
        }


async def list_uri_token_for_sale(
    account: str,
    token_id: str,
    price_xah_drops: str,           # price in drops of XAH
    destination: str = "",           # restrict to specific buyer
) -> dict:
    """List a URIToken for sale at a fixed XAH price."""
    tx = {
        "TransactionType": "URITokenCreateSellOffer",
        "Account": account,
        "URITokenID": token_id,
        "Amount": price_xah_drops,
        "Fee": "12",
        "Sequence": 0,
    }
    if destination:
        tx["Destination"] = destination
    return {"unsigned_tx": tx}


async def buy_uri_token(
    buyer_account: str,
    token_id: str,
    price_xah_drops: str,
) -> dict:
    """Buy a URIToken that is listed for sale."""
    tx = {
        "TransactionType": "URITokenBuy",
        "Account": buyer_account,
        "URITokenID": token_id,
        "Amount": price_xah_drops,
        "Fee": "12",
        "Sequence": 0,
    }
    return {"unsigned_tx": tx}
```

### Hook Integration: React to URIToken Transfers

A Hook can fire when a URIToken changes hands, enabling:
- Royalty enforcement (emit a payment to the creator)
- Transfer gating (reject transfers to non-whitelisted addresses)
- Metadata update (write new hook state when token moves)

```c
// Pseudocode: Hook that enforces 5% royalty on URIToken sales
#include "hookapi.h"

int64_t hook(uint32_t reserved) {
    // Only fire on URITokenBuy transactions
    int64_t tt = otxn_type();
    if (tt != ttURI_TOKEN_BUY) ACCEPT("not a URITokenBuy", 0);

    // Get sale amount
    unsigned char amount_buf[8];
    otxn_field(amount_buf, 8, sfAmount);
    int64_t sale_amount = *((int64_t*)amount_buf);

    // Calculate 5% royalty
    int64_t royalty = sale_amount / 20;

    // Emit royalty payment to creator (hardcoded in hook params)
    unsigned char creator[20];
    hook_param(creator, 20, "CREATOR", 7);

    // Build and emit payment
    uint8_t emitted_txn[PREPARE_PAYMENT_SIMPLE_SIZE];
    PREPARE_PAYMENT_SIMPLE(emitted_txn, royalty, creator, 1, 1);
    uint8_t emithash[32];
    emit(emithash, emitted_txn, PREPARE_PAYMENT_SIMPLE_SIZE);

    ACCEPT("royalty emitted", 0);
}
```

### URIToken Use Cases on Xahau

| Use Case | URI Content | Hook Role |
|---|---|---|
| **NFT Art** | IPFS CID of image/metadata | Royalty enforcement |
| **RWA Certificate** | Arweave TX of legal doc + audit | Transfer gating (KYC check) |
| **Credential / Badge** | DID document URL | Soulbound (burn-only, no transfer) |
| **Game Item** | Game server asset ID | In-game logic via Hook state |
| **Domain Alias** | xrp-ledger.toml URL | Name resolution |
| **Event Ticket** | IPFS ticket metadata | Single-use scan (burn on entry) |

---

## Hooks v3 — New Features and Improvements

### What's New in Hooks v3

Hooks v3 is the production version running on Xahau mainnet as of 2025. Key improvements over earlier versions:

| Feature | Hooks v2 | Hooks v3 |
|---|---|---|
| Max emitted transactions | 8 per execution | 16 per execution |
| Hook parameters | 16 max | 32 max |
| Hook state slots | 128 | 256 |
| Namespace sharing | Single namespace | Named namespaces per hook |
| Strong hooks | Not available | Available (can block rollback) |
| cbak (callback) hooks | Basic | Full access to emitted tx result |
| XAH native amount | Drops only | Drops + sfAmount for IOU |
| `hook_account` | Account only | Full hook context |
| Ledger entry access | Limited | Full `ledger_entry` access |

### v3 Key Functions

```c
// New in v3: read any ledger entry from hook context
int64_t ledger_entry(
    uint32_t write_ptr, uint32_t write_len,
    uint32_t read_ptr, uint32_t read_len
);

// New in v3: get hook execution context
int64_t hook_account(uint32_t write_ptr, uint32_t write_len);

// New in v3: named hook state namespace
int64_t state_foreign(
    uint32_t write_ptr, uint32_t write_len,   // output buffer
    uint32_t kread_ptr, uint32_t kread_len,   // key
    uint32_t nread_ptr, uint32_t nread_len,   // namespace
    uint32_t aread_ptr, uint32_t aread_len    // hook account address
);

// v3: access to sfURITokenID in otxn_field
// Allows hooks to inspect URIToken operations natively
```

### Strong Hooks

In Hooks v3, a hook can be installed as a **strong hook** (via `HookSet` `Flags: 1`). A strong hook can block the `rollback()` of a weak hook — useful for mandatory compliance checks that must always execute.

```python
async def install_strong_hook(
    account: str,
    hook_hash: str,
    hook_params: list[dict],
) -> dict:
    """Install a v3 strong hook that cannot be bypassed by rollback."""
    tx = {
        "TransactionType": "HookSet",
        "Account": account,
        "Hooks": [{
            "Hook": {
                "HookHash": hook_hash,
                "Flags": 1,              # 1 = strong hook
                "HookParameters": hook_params,
                "HookOn": "0000000000000000",  # all transactions
            }
        }],
        "Fee": "2000000",
        "Sequence": 0,
    }
    return {"unsigned_tx": tx, "note": "Strong hook — blocks all rollback attempts"}
```

### Callback Hooks (cbak) in v3

Callback hooks fire after an emitted transaction is validated. This lets your hook react to the *result* of a transaction it previously emitted.

```c
// Callback hook: fires when emitted payment is validated
int64_t cbak(uint32_t reserved) {
    // Get the result of the emitted transaction
    unsigned char result_buf[32];
    int64_t result_len = otxn_field(result_buf, 32, sfTransactionResult);

    // tesSUCCESS = 0
    int64_t result_code = *((int64_t*)result_buf);

    if (result_code == 0) {
        // Payment succeeded — update state
        uint8_t key[32] = "last_success";
        uint8_t val[8];
        // encode ledger sequence into val...
        state_set(val, 8, key, 32);
        ACCEPT("payment confirmed", 0);
    } else {
        // Payment failed — log to state, trigger retry logic
        ROLLBACK("emitted payment failed", 25);
    }
}
```

---

## B2M — Batch-to-Mainnet (Xahau → XRPL L1 Settlement)

### Overview

**B2M (Batch-to-Mainnet)** is a bridging architecture that batches many micro-transactions processed on Xahau into periodic settlement transactions on XRPL L1. This leverages Xahau's low-cost, high-throughput Hook execution for business logic, while settling final balances on XRPL mainnet for maximum liquidity and interoperability.

```
Users / Applications
        │  (individual micro-transactions)
        ▼
    Xahau (XAH sidechain)
    ├── Hooks execute business logic
    ├── Low fee: ~0.000012 XAH per tx
    ├── Fast settlement: ~3 seconds
    ├── Accumulate net balances per user
    └── Periodic batch trigger (every N ledgers or X amount)
        │
        │  (one settlement tx per batch)
        ▼
    XRPL Mainnet (L1)
    ├── Single Payment / OfferCreate representing net of N micro-txs
    ├── Full finality and liquidity access
    └── DEX / AMM / cross-chain bridges
```

### Why B2M?

| Factor | Direct L1 | B2M (Xahau → L1) |
|---|---|---|
| Tx cost | ~0.000012 XRP × N | ~0.000012 XRP × 1 (settlement only) |
| Business logic | None (pure ledger) | Full Hooks |
| Throughput | ~1500 tps theoretical | Higher via batching |
| Finality | 3-5s each | 3-5s each on Xahau, +1 settlement |
| L1 liquidity | Direct | After settlement |

### B2M Implementation Pattern

```python
import asyncio
from dataclasses import dataclass, field
from typing import Optional
import httpx

XAHAU_RPC = "https://xahau.network"
XRPL_RPC = "https://xrplcluster.com"


@dataclass
class BatchAccumulator:
    """Accumulates micro-transactions on Xahau and settles to XRPL L1."""

    bridge_account: str             # the Xahau escrow/bridge account
    l1_settlement_account: str      # the XRPL L1 settlement wallet
    batch_threshold_xah: float = 100.0   # trigger settlement at this balance
    batch_max_ledgers: int = 256         # or at most every 256 ledgers

    pending: dict[str, float] = field(default_factory=dict)  # address → net XAH
    last_settlement_ledger: int = 0

    def record_micro_tx(self, from_addr: str, to_addr: str, amount_xah: float) -> None:
        """Record a micro-transaction (processed by Hook on Xahau)."""
        self.pending[from_addr] = self.pending.get(from_addr, 0) - amount_xah
        self.pending[to_addr] = self.pending.get(to_addr, 0) + amount_xah

    def net_positions(self) -> dict[str, float]:
        """Return only non-zero net positions for settlement."""
        return {addr: bal for addr, bal in self.pending.items() if abs(bal) > 0.000001}

    async def should_settle(self, current_ledger: int) -> bool:
        """Check if settlement threshold is reached."""
        total_volume = sum(abs(v) for v in self.pending.values()) / 2
        ledgers_since = current_ledger - self.last_settlement_ledger
        return (
            total_volume >= self.batch_threshold_xah
            or ledgers_since >= self.batch_max_ledgers
        )

    async def build_settlement_tx(
        self,
        destination: str,
        net_amount_xrp_drops: str,
        batch_ref: str,
    ) -> dict:
        """
        Build a single XRPL L1 Payment representing net settlement.
        In production: loop through net_positions and send to each creditor.
        """
        import json
        memo_data = json.dumps({
            "type": "b2m_settlement",
            "ref": batch_ref,
            "ledger": self.last_settlement_ledger,
            "net_txs": len(self.pending),
        })
        return {
            "TransactionType": "Payment",
            "Account": self.l1_settlement_account,
            "Destination": destination,
            "Amount": net_amount_xrp_drops,
            "Memos": [{
                "Memo": {
                    "MemoType": "62326d5f73657474",       # "b2m_sett"
                    "MemoData": memo_data.encode().hex(),
                }
            }],
            "Fee": "12",
        }


async def monitor_xahau_for_batch_trigger(
    bridge_account: str,
    threshold_xah: float = 100.0,
) -> None:
    """
    Subscribe to Xahau transactions on the bridge account.
    When the balance crosses threshold, trigger L1 settlement.
    """
    import json
    XAHAU_WS = "wss://xahau.network"

    async with httpx.AsyncClient() as client:
        # Get current balance
        resp = await client.post(
            XAHAU_RPC,
            json={
                "method": "account_info",
                "params": [{"account": bridge_account, "ledger_index": "validated"}]
            }
        )
        info = resp.json()["result"]["account_data"]
        balance_drops = int(info.get("Balance", 0))
        balance_xah = balance_drops / 1_000_000
        print(f"Bridge balance: {balance_xah:.6f} XAH")

        if balance_xah >= threshold_xah:
            print(f"[B2M] Threshold reached ({balance_xah:.2f} XAH) → triggering L1 settlement")
            # → build settlement tx → sign → submit to XRPL mainnet
```

### Hook-Driven B2M Settlement Trigger

The cleanest B2M pattern uses a Hook on the Xahau bridge account that automatically emits a cross-chain settlement when the accumulated balance exceeds a threshold.

```c
// Hook pseudocode: auto-trigger B2M settlement
#include "hookapi.h"

#define SETTLEMENT_THRESHOLD 100000000LL  // 100 XAH in drops

int64_t hook(uint32_t reserved) {
    // Get bridge account current balance
    unsigned char acc_buf[20];
    hook_account(acc_buf, 20);

    int64_t balance = 0;
    // ... read balance from account info via ledger_entry ...

    if (balance >= SETTLEMENT_THRESHOLD) {
        // Emit settlement payment to L1 bridge address
        unsigned char l1_bridge[20];
        hook_param(l1_bridge, 20, "L1BRIDGE", 8);

        uint8_t emitted[PREPARE_PAYMENT_SIMPLE_SIZE];
        PREPARE_PAYMENT_SIMPLE(emitted, balance - 1000000LL, l1_bridge, 1, 1);
        uint8_t emithash[32];
        emit(emithash, emitted, PREPARE_PAYMENT_SIMPLE_SIZE);

        ACCEPT("B2M settlement emitted", 22);
    }

    ACCEPT("below threshold", 0);
}
```

### B2M Use Cases

| Application | Micro-Tx Pattern | L1 Settlement |
|---|---|---|
| **Micropayments** | Per-click/per-second payments on Xahau | Daily net settlement per user |
| **Gaming economy** | In-game item trades every second | Hourly net withdrawal |
| **IoT billing** | Per-device usage metering | Weekly invoice settlement |
| **DEX aggregation** | Many small trades batched | Single net AMM deposit/withdrawal |
| **RWA income** | Daily rental accrual tracking | Monthly distribution on L1 |

---

