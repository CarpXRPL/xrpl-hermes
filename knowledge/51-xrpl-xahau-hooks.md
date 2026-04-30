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

## Cross-References

- `50-xrpl-evm-sidechain.md` — Alternative smart contract platform for XRPL
- `52-xrpl-l1-reference.md` — XRPL L1 transaction types that hooks can intercept
- `53-xrpl-wallets-auth.md` — Joey wallet for Hooks development
- `47-xrpl-arweave-storage.md` — Store hook audit logs permanently on Arweave
