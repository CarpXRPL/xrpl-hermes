# Xahau Hooks L1 — Complete Reference

## Overview
Xahau is an XRPL sidechain powered by Hooks — smart contract-like functionality executing on-ledger at the transaction level. Hooks are WebAssembly (WASM) programs that run before and after every transaction, enabling custom logic, fees, and automation.

**Status:** Mainnet live. Hooks v3+ in production on Xahau.

## Architecture
Transaction → Hook (pre-flight) → Core Logic → Hook (post-flight) → Result

### Hook Execution Lifecycle
1. Hook fired when matching HookOn condition is met
2. Hook parameters passed: etxn_reserves, hook_state, otxn, ledger info
3. Hook executes — can read/write state, accept/reject/modify transaction
4. Hook result — accept (tx proceeds) or rollback (rejected with message)

### Hook API Functions (C SDK)
- `accept(uint256 amount, callback)` — Accept and pay hook fee
- `rollback(message, length, amount)` — Reject tx with message
- `otxn_field(field_id, buffer, len)` — Read transaction field
- `otxn_type()` — Get transaction type
- `state(key, buffer, len)` — Read hook state from ledger
- `state_set(key, data, len)` — Write hook state to ledger
- `ledger_seq()` — Current ledger sequence
- `ledger_last_hash()` — Last ledger hash
- `float_multiply(a, b)` — Multiply floats (no floating point in WASM)
- `float_divide(a, b)` — Divide floats
- `util_sha512half(data, len, output)` — Hash
- `util_verify(data, len, sig, sig_len)` — Verify signature
- `emit()` — Emit a new transaction from the hook

### Hook Development (C to WASM)
```c
#include "hookapi.h"

int64_t cbak(uint32_t mread, uint32_t momread, uint32_t mwrite, uint32_t mowrite) {
    // Read transaction type
    uint8_t tt[1];
    otxn_type(SBUF(tt));

    // Only fire on Payments
    if (tt[0] != ttPAYMENT)
        rollback(SBUF("Only payments allowed"), 0);

    // Read sender account
    uint8_t account[20];
    otxn_field(SBUF(account), sfAccount);

    // Store state
    state_set(SBUF(account), SBUF(amount));

    // Emit a new transaction
    // emit(...)

    accept(0, __LINE__);
    return 0;
}
```

### HookSet Transaction
```json
{
  "TransactionType": "HookSet",
  "Account": "rHookOwner",
  "Hooks": [{
    "Hook": {
      "CreateCode": "base64_wasm...",
      "HookOn": "0000000000000000",
      "HookNamespace": "namespace_id",
      "HookApiVersion": 0,
      "HookParameters": []
    }
  }]
}
```

### HookOn Bitmask
Bitmask for which transaction types fire the hook. All zeros = fire on all.

## Use Cases
- Custom transfer fees (tax/burn/redistribute on buy/sell)
- Automated market logic
- Access control / whitelist
- Royalty enforcement on NFT sales
- Wallet recovery mechanisms
- Payment splitting

## Resources
- GitHub: github.com/XRPL-Labs/xrpld-hooks
- Xahau explorer: xahauexplorer.com
