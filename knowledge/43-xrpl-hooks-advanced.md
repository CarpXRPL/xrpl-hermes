# Advanced Hooks Development (Xahau Network)

## Hooks Overview

Hooks are WebAssembly (WASM) programs that execute on the Xahau network (XRPL fork with hooks enabled) in response to transactions. They run **on-ledger** inside rippled validators — no external servers, no gas oracle, deterministic execution.

**Network:** Xahau Mainnet (not XRPL mainnet as of 2025 — pending XLS-40 vote)  
**Language:** C (compiled to WASM with Hooks SDK)  
**Test Network:** Xahau Testnet, or local Docker: `docker pull xrpldlabs/xrpld-hooks`

Key concepts:
- **Hook** — WASM binary installed on an account via `HookSet` transaction
- **HookOn** — bitmask specifying which transaction types trigger the hook
- **State** — 256-byte key→value store per hook (persists across ledgers)
- **Emit** — hooks can emit new transactions (with restrictions)
- **Rollback / Accept** — hook either accepts or rolls back the triggering tx

---

## Project Structure

```
hooks-project/
├── CMakeLists.txt
├── include/
│   └── hookapi.h          # Hook SDK header (from XRPL-Labs/hook-api)
├── src/
│   ├── guard.c            # Whitelist/access control hook
│   ├── fee_collector.c    # Marketplace fee hook
│   └── price_oracle.c     # Price oracle hook
└── build/
    └── *.wasm             # Compiled hook binaries
```

```cmake
# CMakeLists.txt
cmake_minimum_required(VERSION 3.16)
project(hooks C)

set(WASM_TARGET "--target=wasm32-unknown-unknown")
set(CMAKE_C_FLAGS "${WASM_TARGET} -Os -nostdlib -Wl,--no-entry -Wl,--allow-undefined")

function(add_hook name source)
    add_executable(${name} ${source})
    target_include_directories(${name} PRIVATE include)
    set_target_properties(${name} PROPERTIES SUFFIX ".wasm")
endfunction()

add_hook(guard src/guard.c)
add_hook(fee_collector src/fee_collector.c)
add_hook(price_oracle src/price_oracle.c)
```

---

## HookOn Bitmask Reference

`HookOn` is a 256-bit field (32 bytes) where each bit corresponds to a transaction type. **Bit = 1 means IGNORE (inverted logic).**

```c
// hookapi.h (simplified)
// Transaction type bit positions
#define TT_PAYMENT           0
#define TT_ESCROW_CREATE     1
#define TT_ESCROW_FINISH     2
#define TT_ACCOUNT_SET       3
#define TT_ESCROW_CANCEL     4
#define TT_REGULAR_KEY_SET   5
#define TT_OFFER_CREATE      7
#define TT_OFFER_CANCEL      8
#define TT_TRUST_SET        20
#define TT_ACCOUNT_DELETE   19
#define TT_NFTOKEN_MINT     25
#define TT_NFTOKEN_BURN     26
#define TT_NFTOKEN_CREATE_OFFER 27
#define TT_NFTOKEN_CANCEL_OFFER 28
#define TT_NFTOKEN_ACCEPT_OFFER 29
#define TT_AMM_CREATE       35
#define TT_AMM_DEPOSIT      36
#define TT_AMM_WITHDRAW     37
```

```python
# Python helper to build HookOn bitmask
def build_hook_on(*trigger_types: int) -> str:
    """
    Returns hex HookOn value. Bits for IGNORED types are 1; trigger types are 0.
    trigger_types: list of transaction type integers to TRIGGER on.
    """
    # Start with all bits set (ignore everything)
    mask = (1 << 256) - 1

    for tt in trigger_types:
        # Clear the bit for this type (un-set = trigger)
        mask &= ~(1 << tt)

    return mask.to_bytes(32, 'big').hex().upper()

# Hook on: Payment (0) and NFTokenAcceptOffer (29) only
hook_on_hex = build_hook_on(0, 29)
print(hook_on_hex)
```

---

## Installing a Hook (HookSet Transaction)

```python
import xrpl, os
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.transaction import submit_and_wait

client = JsonRpcClient("https://xahau.network")  # Xahau mainnet
account = Wallet.from_secret(os.environ["XAHAU_SECRET"])

# Read compiled WASM
with open("build/guard.wasm", "rb") as f:
    wasm_bytes = f.read()
wasm_hex = wasm_bytes.hex().upper()

# HookOn: trigger on Payment only
HOOK_ON_PAYMENT = build_hook_on(0)

# HookSet transaction (raw dict — use xrpl-py's generic Transaction)
hook_set = {
    "TransactionType": "HookSet",
    "Account": account.classic_address,
    "Hooks": [
        {
            "Hook": {
                "CreateCode": wasm_hex,
                "HookOn": HOOK_ON_PAYMENT,
                "HookNamespace": "0" * 64,  # 32-byte namespace (hex)
                "HookApiVersion": 0,
                "Flags": 1,  # hsfOVERRIDE
                # Optional parameters
                "HookParameters": [
                    {
                        "HookParameter": {
                            "HookParameterName": "4D494E",   # hex("MIN")
                            "HookParameterValue": "0000000000000064",  # 100 in uint64 LE
                        }
                    }
                ],
            }
        }
    ],
    "Fee": "100000",   # Hooks cost more fee (proportional to WASM size)
    "Sequence": account_sequence,
}

# Sign and submit as raw JSON (xrpl-py may not have native HookSet model)
import json, hashlib
signed = xrpl.transaction.safe_sign_transaction(
    xrpl.models.transactions.Transaction.from_dict(hook_set), account
)
resp = client.request(xrpl.models.requests.Submit(tx_blob=signed.to_blob()))
print(resp.result.get("engine_result"))
```

---

## Hook: Payment Whitelist (Guard Hook)

```c
// src/guard.c
#include "hookapi.h"

#define GUARD_LIMIT 100  // Max iterations in each loop

// State key for whitelist entries
uint8_t WHITELIST_KEY[32] = {0};

int64_t hook(uint32_t reserved) {
    GUARD(GUARD_LIMIT);

    // Only act on outgoing payments
    int64_t hook_type = hook_type();
    if (hook_type != HOOK_OUTGOING)
        accept(0, 0, __LINE__);

    // Get destination from transaction
    uint8_t dest[20];
    int64_t dest_len = otxn_field(SBUF(dest), sfDestination);
    if (dest_len < 0)
        rollback(SBUF("Could not read Destination"), __LINE__);

    // Check state: is this destination whitelisted?
    uint8_t allowed = 0;
    int64_t state_len = state(SBUF(WHITELIST_KEY), dest, 20, &allowed, 1);

    // state_len > 0 means key exists in state
    if (state_len <= 0 || allowed != 1)
        rollback(SBUF("Destination not whitelisted"), 1);

    accept(SBUF("Payment to whitelisted destination"), 0);
    return 0;
}
```

---

## Hook: Fee Collector (Marketplace 2.5% Fee)

```c
// src/fee_collector.c
#include "hookapi.h"
#include "sfcodes.h"

#define FEE_NUMERATOR   25     // 2.5%
#define FEE_DENOMINATOR 1000
#define GUARD_LIMIT     200

uint8_t FEE_WALLET[20] = {
    // Raw account ID bytes of fee recipient (convert from classic address)
    0x12, 0x34, ...
};

int64_t hook(uint32_t reserved) {
    GUARD(GUARD_LIMIT);

    // Only trigger on NFTokenAcceptOffer transactions
    int64_t txn_type = otxn_type();
    if (txn_type != ttNFTOKEN_ACCEPT_OFFER)
        accept(0, 0, __LINE__);

    // Get the sale amount (sfAmount)
    uint8_t amount_buf[48];
    int64_t amount_len = otxn_field(SBUF(amount_buf), sfAmount);

    // XRP amounts are 8 bytes (uint64 drops, big-endian)
    // IOU amounts are different — check first byte
    if (amount_len != 8) {
        // Not an XRP sale — skip
        accept(SBUF("Non-XRP sale, skipping fee"), 0);
    }

    int64_t sale_drops = 0;
    for (int i = 0; i < 8; i++)
        sale_drops = (sale_drops << 8) | amount_buf[i];
    sale_drops &= 0x3FFFFFFFFFFFFFFF;  // Clear type bits

    int64_t fee_drops = (sale_drops * FEE_NUMERATOR) / FEE_DENOMINATOR;
    if (fee_drops <= 0)
        accept(SBUF("Fee too small"), 0);

    // Emit a fee payment to the platform wallet
    uint8_t emit_buf[PREPARE_PAYMENT_SIMPLE_SIZE];
    PREPARE_PAYMENT_SIMPLE(
        emit_buf,
        fee_drops,
        FEE_WALLET,
        otxn_burden() + 1,  // Execution burden
        0                   // No destination tag
    );

    uint8_t emit_hash[32];
    int64_t emit_result = emit(SBUF(emit_hash), SBUF(emit_buf));
    if (emit_result < 0)
        rollback(SBUF("Emit failed"), emit_result);

    accept(SBUF("Fee collected"), 0);
    return 0;
}
```

---

## Hook: Cross-Hook State Sharing

```c
// Hook A (writer): stores a price in shared state
uint8_t PRICE_KEY[32] = {'P','R','I','C','E',0};

int64_t hook_a(uint32_t reserved) {
    int64_t price_drops = 1234567;  // Computed from tx or oracle

    uint8_t price_bytes[8];
    for (int i = 7; i >= 0; i--) {
        price_bytes[i] = price_drops & 0xFF;
        price_drops >>= 8;
    }

    // Write to state — persists across ledgers
    state_set(SBUF(price_bytes), SBUF(PRICE_KEY));
    accept(0, 0, __LINE__);
    return 0;
}

// Hook B (reader): reads price from same account's state
int64_t hook_b(uint32_t reserved) {
    uint8_t price_bytes[8] = {0};
    int64_t state_len = state(SBUF(price_bytes), SBUF(PRICE_KEY));

    if (state_len < 0) {
        // No price set yet
        rollback(SBUF("Price not initialized"), 1);
    }

    int64_t price = 0;
    for (int i = 0; i < 8; i++)
        price = (price << 8) | price_bytes[i];

    // Use price in validation logic...
    accept(0, 0, __LINE__);
    return 0;
}
```

---

## Hook: Reading Parameters at Runtime

```c
// Parameters are set during HookSet and can be updated without reinstalling
// Key = "MIN" (hex: 4D494E), Value = uint64 little-endian minimum

uint8_t PARAM_KEY[3] = {0x4D, 0x49, 0x4E};  // "MIN"

int64_t hook(uint32_t reserved) {
    uint8_t min_buf[8] = {0};
    int64_t param_len = hook_param(SBUF(min_buf), SBUF(PARAM_KEY));

    if (param_len != 8)
        rollback(SBUF("MIN param not set"), 1);

    // Little-endian decode
    int64_t minimum = 0;
    for (int i = 0; i < 8; i++)
        minimum |= ((int64_t)min_buf[i] << (i * 8));

    // Get incoming payment amount
    uint8_t amount_buf[8];
    otxn_field(SBUF(amount_buf), sfAmount);
    int64_t amount = /* decode drops */ 0;

    if (amount < minimum)
        rollback(SBUF("Amount below minimum"), 1);

    accept(0, 0, __LINE__);
    return 0;
}
```

### Updating Parameters Without Reinstalling

```python
# Update hook parameter without changing code
update_params = {
    "TransactionType": "HookSet",
    "Account": account.classic_address,
    "Hooks": [{
        "Hook": {
            "HookHash": existing_hook_hash,  # Reference existing installed hook
            "HookParameters": [{
                "HookParameter": {
                    "HookParameterName": "4D494E",      # "MIN"
                    "HookParameterValue": "E803000000000000",  # 1000 LE uint64
                }
            }],
        }
    }],
    "Fee": "12",
}
```

---

## Hook: Emitting Transactions

```c
// Hooks can emit at most HOOK_BURDEN transactions per execution
// Emitted txs count toward the account's sequence (no sequence field needed)

// Emit a simple payment
#include "hookapi.h"

int64_t emit_payment(
    uint8_t* dest,        // 20-byte destination account ID
    int64_t drops,        // Amount in drops
    uint32_t dest_tag     // Destination tag (0 for none)
) {
    uint8_t txn[PREPARE_PAYMENT_SIMPLE_SIZE];
    PREPARE_PAYMENT_SIMPLE(txn, drops, dest, 1, dest_tag);

    uint8_t emit_hash[32];
    int64_t result = emit(SBUF(emit_hash), SBUF(txn));
    return result;  // >= 0 is success
}

// Emit constraints:
// - Cannot emit txs that would cause themselves to trigger hooks again (infinite loop prevention)
// - emitted txs have sfEmitDetails field set
// - max emit depth: 5 levels
// - fee for emitted txs: auto-calculated, deducted from hook account
```

---

## Testing Hooks with Docker

```bash
# Start local hooks testnet
docker pull xrpldlabs/xrpld-hooks:latest
docker run -d \
  --name hooks-testnet \
  -p 51235:51235 \
  -p 5005:5005 \
  xrpldlabs/xrpld-hooks

# Fund a test account
curl -s -X POST http://localhost:5005 \
  -H "Content-Type: application/json" \
  -d '{"method":"wallet_propose","params":[{"seed":"REDACTED_TEST_SEED"}]}'

# Check hook installation
curl -s -X POST http://localhost:5005 \
  -H "Content-Type: application/json" \
  -d '{"method":"account_info","params":[{"account":"rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh"}]}' | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d['result']['account_data'].get('Hooks',[]), indent=2))"
```

```python
# Python test harness for hooks
from xrpl.clients import JsonRpcClient
from xrpl.wallet import generate_faucet_wallet

test_client = JsonRpcClient("http://localhost:5005")
tester = generate_faucet_wallet(test_client)

# Install hook
# ... (HookSet tx) ...

# Send test payment
from xrpl.models.transactions import Payment
from xrpl.transaction import submit_and_wait

test_payment = Payment(
    account=tester.classic_address,
    destination="rDestination...",
    amount=xrpl.utils.xrp_to_drops("1"),
)
resp = submit_and_wait(test_payment, test_client, tester)
print("Hook triggered, result:", resp.result['meta']['TransactionResult'])
# Check for hook return codes in meta
hook_meta = resp.result['meta'].get('HookExecutions', [])
for h in hook_meta:
    print("  Hook:", h['HookExecution'].get('HookReturnString'))
```

---

## Gas (Fee) Optimization

```c
// Every C function call costs "gas" (counted as GUARD credits)
// Avoid:
// - Loops without GUARD macros (will be rejected at install time)
// - Large state reads/writes (each costs proportional fee)
// - Deep call chains

// Rule: Every loop must have a GUARD with worst-case iteration count
for (int i = 0; i < MAX_ITEMS; i++) {
    GUARD(MAX_ITEMS);
    // ... loop body ...
}

// GUARD count affects the minimum fee for the triggering tx
// Fee formula: base_fee * (1 + max_hook_instructions / HOOK_INSTR_PER_FEE_UNIT)
// Typical fees: 100-500 drops for simple hooks, 10000+ for complex ones
```

---

## Hook Debugging

```python
# Read HookExecution metadata from a validated tx
from xrpl.models.requests import Tx

resp = client.request(Tx(transaction="TXHASH..."))
meta = resp.result.get("meta", {})

hook_executions = meta.get("HookExecutions", [])
for exec_entry in hook_executions:
    h = exec_entry.get("HookExecution", {})
    print(f"Hook account: {h.get('HookAccount')}")
    print(f"Return code:  {h.get('HookReturnCode')}")
    print(f"Return msg:   {bytes.fromhex(h.get('HookReturnString', '')).decode('ascii', errors='replace')}")
    print(f"State changes: {h.get('HookStateChangeCount', 0)}")
    print(f"Emit count:    {h.get('HookEmitCount', 0)}")
```

---

## Removing a Hook

```python
# Uninstall a hook by setting CreateCode to empty
remove_hook = {
    "TransactionType": "HookSet",
    "Account": account.classic_address,
    "Hooks": [{
        "Hook": {
            "CreateCode": "",     # Empty = remove
            "Flags": 1,           # hsfOVERRIDE
        }
    }],
}
```

---

## Related Files
- `references/xahau-hooks.md` — Xahau hooks fundamentals and network info
- `knowledge/32-xrpl-hooks-dev.md` — basic hook development walkthrough
- `knowledge/36-xrpl-xls-standards.md` — XLS-40 hooks standard proposal
