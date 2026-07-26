# Xahau Hooks Development — Safe Workflow

## Capability boundary

XRPL-Hermes can help specify a Hook, calculate `HookOn`, review artifacts, and verify an installed chain. It does not currently compile Hook code or construct/serialize/sign/submit `SetHook` transactions. Those actions belong to the current official Xahau Hooks toolchain and a user-controlled signer.

## Development stages

### 1. Specification

Write a short behavior contract before coding:

- target account role and target network;
- exact incoming/outgoing transaction types;
- accept/reject behavior;
- state keys and update invariants;
- emitted transaction types, if any;
- parameters and grants;
- failure behavior;
- upgrade and rollback path.

Avoid broad “account firewall” requirements until each permitted and denied flow is enumerated.

### 2. Trigger calculation

```bash
python3 scripts/xrpl_tools.py hooks-bitmask Payment Invoke
```

Review the returned transaction IDs and exact 64-character field. `HookOn` is active-low except `SetHook` bit 22, which is active-high. Testnet may support `HookOnIncoming`/`HookOnOutgoing` while Mainnet does not; confirm the target network's enabled amendments.

### 3. Implementation and compilation

Use only the current official Xahau documentation, Hook API headers, examples, and build tooling. The browser builder is documented at <https://builder.xahau.network/>; validate its current provenance before use.

A Hook module must meet current Xahau WebAssembly and Hook API constraints. Do not copy code from the superseded XRPL-Hermes articles: those snippets were quarantined because they contained incorrect imports, function signatures, undefined identifiers, and unverified limits.

Required review artifacts:

- source commit/hash;
- compiler/toolchain version;
- deterministic build command or project manifest;
- WASM SHA-256;
- static/audit findings;
- expected namespace, HookOn, parameters, grants, and chain slot.

### 4. Unsigned transaction preparation

Prepare `SetHook` only with a current Xahau-aware serializer. `xrpl-py` transaction models are not proof that Xahau-only fields or transaction types serialize correctly. The transaction must contain the correct Xahau `NetworkID`.

Before signing:

- validate all field encodings and lengths;
- ensure `CreateCode` is hex WASM bytes;
- verify install/update/delete operation classification;
- inspect chain position and override/namespace-delete flags;
- compare the resulting signing serialization with current Xahau tooling;
- run Xahau `simulate` where supported and require successful preflight.

Never place a seed, secret, or private key in source, command arguments, environment examples, logs, MCP calls, or node RPC payloads.

### 5. Testnet verification

1. Confirm endpoint/network ID `21338`.
2. Fund a dedicated disposable Testnet account through an official current faucet path.
3. Sign in a user-controlled Xahau-compatible wallet.
4. Submit through the wallet/toolchain, not XRPL-Hermes.
5. Wait for a validated transaction.
6. Inspect the installed chain:

```bash
python3 scripts/xrpl_tools.py hooks-info rACCOUNT testnet
```

7. Match slot and `HookHash` to the reviewed artifact.
8. Run positive, negative, boundary, replay, malformed-parameter, and fee/reserve tests.
9. Rehearse update and deletion; prove the validated post-state.

## Testing requirements

At minimum, test:

- every intended trigger type;
- representative non-trigger types;
- incoming and outgoing account participation;
- minimum/maximum values;
- malformed and missing parameters;
- state initialization, mutation, and namespace isolation;
- emitted-transaction limits and failure paths;
- chain interaction with Hooks before and after the target slot;
- rollback when the Hook rejects ordinary account operations.

Keep transaction hashes, validated ledger indexes, Hook hashes, and build hashes as receipts.

## Mainnet gate

Testnet success is necessary but insufficient. Mainnet requires:

- refreshed Mainnet amendment state and serializer definitions;
- compatibility with features actually enabled on Mainnet;
- independent source/WASM/security audit;
- reviewed reserve and operational costs;
- monitored rollout and tested rollback;
- explicit human approval before signing.

## Sources

Use `references/xahau-hooks.md` as the pinned protocol card and `knowledge/51-xrpl-xahau-hooks.md` for network semantics. Do not revive old inline signing/submission examples.
