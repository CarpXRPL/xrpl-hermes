# XRPL Hooks Development

## Overview

Hooks are small WebAssembly programs that execute on the Xahau network (the XRPL sidechain with Hooks enabled). They react to transactions before or after they're applied, allowing logic like: auto-routing, fee distribution, access control, and programmable escrow. Hooks are the primary "smart contract" mechanism for Xahau.

---

## 1. Architecture

```
Transaction arrives at Xahau node
    │
    ▼
Hook executes (before tx is applied)
    │
    ├── accept()    → TX proceeds
    ├── rollback()  → TX rejected with error
    │
    ▼
Transaction applied to ledger
    │
    ▼
Hook executes (after tx is applied, for emit)
```

Hooks are:
- Written in C, compiled to WebAssembly (WASM)
- Installed on an account (not a contract address)
- Triggered by incoming or outgoing transactions
- Deterministic and sandboxed

---

## 2. Toolchain Setup

```bash
# Install clang with WebAssembly target
apt install -y clang lld

# Install wabt (WebAssembly Binary Toolkit)
apt install -y wabt

# Clone Hooks C library
git clone https://github.com/XRPLF/hook-cleaner-c
git clone https://github.com/XRPLF/xrpl-hook-toolkit

# Or use the Docker development environment
docker pull xrplf/xrpld-hooks:latest

# Compile a hook
clang \
  --target=wasm32-unknown-unknown \
  -O3 \
  -o hook.wasm \
  hook.c \
  -I ./xrpl-hook-toolkit/includes \
  --no-standard-libraries \
  -Wl,--no-entry \
  -Wl,--export=hook \
  -Wl,--export=cbak
```

---

## 3. Basic Hook Structure (C)

```c
#include "hookapi.h"

// Called when a transaction arrives at the Hook account
int64_t hook(uint32_t reserved) {
    TRACESTR("MyHook: Starting");
    
    // Get the transaction type
    uint8_t txn_type[2];
    otxn_field(SBUF(txn_type), sfTransactionType);
    uint16_t txtype = (txn_type[0] << 8) + txn_type[1];
    
    // Only process Payment transactions
    if (txtype != ttPAYMENT) {
        ACCEPT("Not a payment, passing", 0);
    }
    
    // Get the amount
    uint8_t amount_buf[48];
    int64_t amount_len = otxn_field(SBUF(amount_buf), sfAmount);
    
    if (amount_len != 8) {
        // Token payment (not XRP)
        ROLLBACK("Only XRP accepted", 50);
    }
    
    int64_t drops = AMOUNT_TO_DROPS(amount_buf);
    
    if (drops < 1000000) {  // < 1 XRP
        ROLLBACK("Minimum 1 XRP required", 51);
    }
    
    ACCEPT("Payment accepted", 0);
}

// Called after transaction is applied (for emitting new transactions)
int64_t cbak(uint32_t reserved) {
    return 0;
}
```

---

## 4. Hook API Reference

### Core Functions

```c
/* Accept the transaction */
int64_t accept(uint32_t read_ptr, uint32_t read_len, int64_t error_code);
#define ACCEPT(msg, code) accept(SBUF(msg), code)

/* Reject the transaction */
int64_t rollback(uint32_t read_ptr, uint32_t read_len, int64_t error_code);
#define ROLLBACK(msg, code) rollback(SBUF(msg), code)

/* Get field from originating transaction */
int64_t otxn_field(uint32_t write_ptr, uint32_t write_len, uint32_t field_id);

/* Get field from emitted transaction (in cbak) */
int64_t etxn_field(uint32_t write_ptr, uint32_t write_len, uint32_t field_id);

/* Get ledger object */
int64_t slot_set(uint32_t read_ptr, uint32_t read_len, int32_t slot);
int64_t slot_subfield(uint32_t read_ptr, uint32_t read_len, uint32_t field_id, int32_t slot);
int64_t slot_size(int32_t slot);
int64_t slot(uint32_t write_ptr, uint32_t write_len, int32_t slot);
```

### State Management

```c
/* Read hook state */
int64_t state(
    uint32_t write_ptr, uint32_t write_len,  // output buffer
    uint32_t kread_ptr, uint32_t kread_len   // key buffer
);

/* Write hook state */
int64_t state_set(
    uint32_t read_ptr, uint32_t read_len,    // value buffer
    uint32_t kread_ptr, uint32_t kread_len   // key buffer
);

/* State in another hook account's namespace */
int64_t state_foreign(
    uint32_t write_ptr, uint32_t write_len,
    uint32_t kread_ptr, uint32_t kread_len,
    uint32_t nread_ptr, uint32_t nread_len,  // namespace
    uint32_t aread_ptr, uint32_t aread_len   // hook account
);
```

### Emitting Transactions

```c
/* Prepare a new transaction to emit */
int64_t etxn_reserve(uint32_t count);
int64_t etxn_nonce(uint32_t write_ptr, uint32_t write_len);
int64_t etxn_fee_base(uint32_t read_ptr, uint32_t read_len);

/* Build and emit a transaction */
int64_t emit(
    uint32_t write_ptr, uint32_t write_len,  // emitted tx hash output
    uint32_t read_ptr, uint32_t read_len     // serialized transaction
);
```

### Utility

```c
/* Tracing (debug output) */
int64_t trace(uint32_t mread_ptr, uint32_t mread_len,
              uint32_t dread_ptr, uint32_t dread_len, uint32_t as_hex);
#define TRACESTR(msg) trace(SBUF(msg), 0, 0, 0)
#define TRACEHEX(data) trace("hex", 3, SBUF(data), 1)

/* Float math */
int64_t float_set(int32_t exponent, int64_t mantissa);
int64_t float_multiply(int64_t float1, int64_t float2);
int64_t float_divide(int64_t float1, int64_t float2);
int64_t float_compare(int64_t float1, int64_t float2, uint32_t mode);
int64_t float_one(); /* Returns 1.0 as XFL */
```

---

## 5. HookOn Bitmask

HookOn controls which transaction types trigger the hook:

```c
// Transaction type bits (each bit = one transaction type)
// Bit 0 = ttPAYMENT (type 0)
// Bit 22 = ttAMM_DEPOSIT (type 35)
// etc.

// To trigger on Payment only:
uint64_t hook_on = ~0ULL ^ (1ULL << ttPAYMENT);
// (All 1s except the payment bit, which is 0 = "trigger")

// To trigger on all transactions:
uint64_t hook_on = 0ULL;  // all zeros = trigger on everything

// To trigger on Payment AND OfferCreate:
uint64_t hook_on = ~0ULL ^ (1ULL << ttPAYMENT) ^ (1ULL << ttOFFER_CREATE);
```

Transaction type numbers:
```
ttPAYMENT = 0
ttESCROW_CREATE = 1
ttESCROW_FINISH = 2
ttACCOUNT_SET = 3
ttESCROW_CANCEL = 4
ttSET_REGULAR_KEY = 5
ttOFFER_CREATE = 7
ttOFFER_CANCEL = 8
ttTICKET_CREATE = 10
ttSIGNER_LIST_SET = 12
ttPAYCHAN_CREATE = 15
ttPAYCHAN_FUND = 16
ttPAYCHAN_CLAIM = 17
ttCHECK_CREATE = 16
ttCHECK_CASH = 17
ttCHECK_CANCEL = 18
ttDEPOSIT_PREAUTH = 19
ttTRUST_SET = 20
ttACCOUNT_DELETE = 21
ttHOOK_SET = 22
ttNFTOKEN_MINT = 25
ttNFTOKEN_BURN = 26
ttNFTOKEN_CREATE_OFFER = 27
ttNFTOKEN_CANCEL_OFFER = 28
ttNFTOKEN_ACCEPT_OFFER = 29
ttINVOKE = 99
```

---

## 6. HookSet Transaction

Install a hook on an account:

```json
{
  "TransactionType": "SetHook",
  "Account": "rMYACCOUNT...",
  "Hooks": [
    {
      "Hook": {
        "CreateCode": "0061736D010000...",
        "HookOn": "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFBFFFFFFF",
        "HookNamespace": "0000000000000000000000000000000000000000000000000000000000000000",
        "HookApiVersion": 0,
        "Flags": 1
      }
    }
  ],
  "Fee": "100000",
  "Sequence": 1
}
```

| Field | Description |
|-------|-------------|
| `CreateCode` | WASM bytecode (hex) |
| `HookOn` | 256-bit bitmask of triggering tx types |
| `HookNamespace` | 32-byte namespace for state isolation |
| `HookApiVersion` | Always 0 for now |
| `Flags` | `hsfOVERRIDE` = 1 (update existing) |

### Installing via xrpl-py

```python
import binascii

with open("hook.wasm", "rb") as f:
    wasm_bytes = f.read()
    wasm_hex = binascii.hexlify(wasm_bytes).decode().upper()

tx = {
    "TransactionType": "SetHook",
    "Account": wallet.address,
    "Hooks": [
        {
            "Hook": {
                "CreateCode": wasm_hex,
                "HookOn": "F" * 64,  # trigger on nothing (test)
                "HookNamespace": "0" * 64,
                "HookApiVersion": 0,
                "Flags": 1
            }
        }
    ],
    "Fee": "100000"
}
```

---

## 7. State Management Pattern

Counter hook that tracks payment count:

```c
#include "hookapi.h"

int64_t hook(uint32_t reserved) {
    // State key: "COUNT"
    uint8_t key[5] = {'C', 'O', 'U', 'N', 'T'};
    
    // Read current count
    uint8_t count_buf[8];
    int64_t count = 0;
    
    if (state(SBUF(count_buf), SBUF(key)) >= 0) {
        count = *(int64_t*)count_buf;
    }
    
    count++;
    
    // Write back
    *(int64_t*)count_buf = count;
    state_set(SBUF(count_buf), SBUF(key));
    
    TRACESTR("Counter incremented");
    ACCEPT("Counted", 0);
}

int64_t cbak(uint32_t reserved) { return 0; }
```

---

## 8. Emitting a Transaction from a Hook

```c
#include "hookapi.h"

#define DESTINATION_ADDR "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh"
#define FEE_DROPS 1000000  // 1 XRP fee share

int64_t hook(uint32_t reserved) {
    // Reserve space for 1 emitted transaction
    etxn_reserve(1);
    
    // Get incoming amount
    uint8_t amount_buf[48];
    otxn_field(SBUF(amount_buf), sfAmount);
    
    // Only handle XRP
    if (amount_buf[0] & 0x80) {
        ACCEPT("Token payment, skip fee share", 0);
    }
    
    // Calculate fee (10% of incoming)
    int64_t incoming = AMOUNT_TO_DROPS(amount_buf);
    int64_t fee_share = incoming / 10;
    
    if (fee_share < 1000) {
        ACCEPT("Too small for fee share", 0);
    }
    
    // Build emitted payment transaction
    uint8_t emtx[256];
    uint16_t bytes = 0;
    
    // ... (build STObject manually using hook C API)
    // This is complex — use the Hooks boilerplate from XRPLF
    
    uint8_t emithash[32];
    emit(SBUF(emithash), emtx, bytes);
    
    ACCEPT("Fee share emitted", 0);
}
```

---

## 9. Testing with xrpld-hooks

```bash
# Run local Xahau node with Hooks enabled
docker pull xrplf/xrpld-hooks:latest

docker run -d \
  --name xrpld-hooks \
  -p 6006:6006 \
  -p 5005:5005 \
  xrplf/xrpld-hooks:latest

# Fund test accounts from genesis
curl -X POST http://localhost:5005 \
  -d '{"method":"ledger_accept","params":[{}]}'

# Install hook
python3 install_hook.py --network http://localhost:5005
```

---

## 10. Hook Parameters

Hooks can receive runtime parameters (set by installer or invoker):

```c
// In the hook C code:
uint8_t param_buf[32];
int64_t param_len = hook_param(SBUF(param_buf), "MINAMT", 6);
if (param_len > 0) {
    int64_t min_amount = *(int64_t*)param_buf;
}
```

Setting parameters in HookSet:
```json
{
  "Hook": {
    "HookHash": "EXISTING_HOOK_HASH...",
    "HookParameters": [
      {
        "HookParameter": {
          "HookParameterName": "4D494E414D54",
          "HookParameterValue": "00000000000F4240"
        }
      }
    ]
  }
}
```

---

## 11. Hook Execution Model

```
Hook execution budget: 
  - Maximum instructions: 1,048,576 (1M)
  - Maximum state size: 128 bytes per key
  - Maximum state keys: 256
  - Maximum emit count: 5 per hook
  - Maximum state namespace: 32 bytes

Fee for hook execution:
  - base hook fee + per-instruction cost
  - Higher fee = more budget allowed
```

---

## 12. Resources

- Hooks documentation: `https://xahau.network/hooks`
- Hook toolkit (C): `https://github.com/XRPLF/xrpl-hook-toolkit`
- Hook examples: `https://github.com/XRPLF/xrpl-hooks-examples`
- Xahau testnet explorer: `https://explorer.testnet.xahau.network`
- Xahau mainnet: `wss://xahau.network`
- Testnet: `wss://hooks-testnet-v3.xrpl-labs.com`
