# Xahau Hook Setup Flow

Use for requests to inspect, design, calculate triggers for, or plan installation of a Xahau Hook.

## Hard boundary

Xahau is a separate XRPL-protocol network with native XAH and network IDs `21337`/`21338`. Hooks installed there do not run on XRPL Mainnet.

XRPL-Hermes can:

- calculate legacy `HookOn`;
- inspect validated installed Hook chains on Xahau Mainnet/Testnet;
- review an unsigned plan and evidence.

XRPL-Hermes cannot currently:

- compile or audit source/WASM;
- construct or serialize a protocol-validated `SetHook`;
- sign, submit, deploy, update, or delete a Hook.

Never accept or request a secret. Never claim deployment from a plan or unvalidated transaction.

## Read first

- `references/xahau-hooks.md`
- `knowledge/51-xrpl-xahau-hooks.md`
- for development: `knowledge/32-xrpl-hooks-dev.md`
- for production: `knowledge/43-xrpl-hooks-advanced.md`

## Flow

### 1. Select the target

Default all new work to **Testnet**. Mainnet requires refreshed amendment checks, independent audit, complete Testnet receipts, and explicit human approval.

Record:

- network and observed `NetworkID`;
- account classic address;
- target chain slot;
- intended transaction types and account direction;
- state/parameters/grants/emission requirements;
- rollback objective.

### 2. Inspect current chain

```bash
python3 scripts/xrpl_tools.py hooks-info rACCOUNT testnet
```

For Mainnet inspection only:

```bash
python3 scripts/xrpl_tools.py hooks-info rACCOUNT mainnet
```

Stop on any top-level `Error`, network mismatch, or `Validated: false`. Preserve all chain slots/hashes before changing anything.

### 3. Calculate triggers

```bash
python3 scripts/xrpl_tools.py hooks-bitmask Payment Invoke
```

Verify:

- intended types and IDs;
- 64 hex characters with no `0x`;
- active-low semantics for normal types;
- special active-high `SetHook` bit 22.

If the design requires incoming/outgoing masks or named Hooks, check live target-network amendment state. Testnet support does not imply Mainnet support.

### 4. External compile and transaction preparation

Hand the specification to the current official Xahau Hooks toolchain. Require source, compiler version, deterministic build recipe, WASM hash, exact Hook fields, and Xahau-aware serialization proof.

Use Xahau `simulate` where available before the user signs. Do not manufacture a `SetHook` JSON template from XRPL-only libraries.

### 5. User-controlled Testnet signing

The user reviews and signs in a Xahau-compatible wallet outside Hermes. Hermes may inspect decoded unsigned data but must not handle keys or broadcast.

### 6. Validate results

Require:

- validated `SetHook` transaction hash and ledger index;
- installed slot/hash matching the reviewed WASM;
- one positive trigger test;
- one negative/non-trigger test;
- boundary and malformed-input tests;
- successful rollback/update/delete rehearsal;
- validated post-rollback chain inspection.

## Output contract

Return:

- **Target:** network, NetworkID, account, slot
- **Behavior:** exact triggers and non-triggers
- **HookOn:** value, resolved IDs, semantics
- **Artifacts required:** source/build/WASM/audit hashes
- **Current live state:** validated chain snapshot
- **External steps:** compile, Xahau-aware serialize/simulate, wallet sign/submit
- **Acceptance evidence:** transaction/ledger/hash/tests/rollback
- **Blockers:** any unsupported field, disabled amendment, or missing evidence
