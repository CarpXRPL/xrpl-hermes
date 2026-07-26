# Xahau Hooks — Network and Protocol Guide

## Scope and status

Xahau is a separate XRPL-protocol network with native currency **XAH**, network IDs `21337` (Mainnet) and `21338` (Testnet), and its own amendment state. Hooks are deterministic WebAssembly modules attached to Xahau accounts. They execute as part of ledger transaction processing when account participation and `HookOn` rules match.

Do not describe Xahau as XRPL Mainnet and do not imply that installing a Hook on Xahau changes XRPL Mainnet behavior.

XRPL-Hermes currently provides only:

- a deterministic legacy `HookOn` calculator; and
- validated-ledger installed-Hook inspection for Mainnet/Testnet.

It does **not** compile, audit, serialize, sign, submit, or deploy Hooks.

## Live endpoints

| Network | NetworkID | JSON-RPC | WebSocket |
|---|---:|---|---|
| Mainnet | `21337` | `https://xahau.network` | `wss://xahau.network` |
| Testnet | `21338` | `https://xahau-test.net` | `wss://xahau-test.net` |

Check the `server_info.info.network_id` response before trusting an endpoint label. Use validated ledgers for state proof.

## Execution model

An account can have an ordered chain of up to 10 Hooks. The `Hooks` array in a `SetHook` transaction is positional. A Hook may:

- inspect the originating transaction and relevant ledger state;
- accept or reject execution;
- read/write namespace-scoped Hook state within protocol limits;
- emit permitted transactions when the required amendment and permissions apply.

Hook behavior can affect funds and account availability. Treat source, binary, parameters, grants, namespace, chain position, trigger mask, emission permissions, and rollback as security-critical.

## HookOn semantics

`HookOn` uses current Xahau transaction-type numeric IDs as bit positions in a 256-bit value.

- Most bits are active-low: `0` means the Hook may fire for that type.
- `ttHOOK_SET=22` is active-high: `1` means the Hook may fire for `SetHook`.
- The field is a 64-character hexadecimal `Hash256` without an `0x` prefix.

Use:

```bash
python3 scripts/xrpl_tools.py hooks-bitmask Payment Invoke
```

The calculator is protocol-ID based and includes source/review metadata. Numeric IDs in range 0–255 are accepted for current types not yet named by the local alias map; verify those IDs against the target network's live `server_definitions.json`.

## SetHook structure and operations

The canonical transaction type is `SetHook`. Its required `Hooks` field contains 1–10 positional Hook wrappers. Depending on the operation, a Hook object can include:

- `CreateCode`: hex-encoded WASM bytes;
- `HookHash`: existing definition hash;
- `HookOn` or amendment-gated incoming/outgoing masks;
- `HookNamespace`;
- `HookApiVersion` (creation currently uses `0`);
- `Flags` (`hsfOVERRIDE=1`, `hsfNSDELETE=2`, `hsfCOLLECT=4`);
- `HookParameters`;
- `HookGrants`;
- amendment-gated fields such as `HookCanEmit` or `HookName`.

Operation classification is determined by exact field presence and flags. In particular:

- create/replace uses non-empty `CreateCode`; replacing an occupied slot needs override authorization;
- installing a previously defined Hook uses `HookHash` rather than `CreateCode`;
- deleting a Hook uses empty `CreateCode` plus the override flag;
- namespace deletion uses the namespace-delete flag and its allowed field combination;
- an empty positional Hook object is a no-op, not deletion.

Do not build these combinations from memory. Use current official tooling, current target-network definitions, and `simulate` before signing.

## Reading installed Hooks

```bash
python3 scripts/xrpl_tools.py hooks-info rACCOUNT testnet
python3 scripts/xrpl_tools.py hooks-info rACCOUNT mainnet
```

The command reads `account_objects` with `type=hook`, flattens the installed Hook chain, and returns:

- chain `Slot` and `HookHash`;
- exposed parameters/flags;
- `LedgerIndex`, `LedgerHash`, and `Validated`;
- `Network`, `NetworkID`, endpoint, and server version.

Hooks are not embedded in `account_info`. A missing account is an RPC error and must never be presented as an empty Hook chain.

## Invoke, Remit, and URITokens

These are real Xahau protocol surfaces on the reviewed Mainnet and Testnet definitions:

- `Invoke` (`tt=99`) explicitly targets Hook execution and may carry Hook parameters.
- `Remit` (`tt=95`) supports exact multi-asset transfer semantics and can include Xahau-specific URIToken operations; it has distinct reserve/fee consequences.
- URIToken transaction types use IDs `45–49`: mint, burn, buy, create sell offer, cancel sell offer.

XRPL-Hermes does not currently provide builders for these Xahau transaction types. Do not pass secrets to public nodes or adapt XRPL builders by merely changing `TransactionType`.

## Amendment drift

At the 2026-07-25 review:

- Mainnet and Testnet enabled Hooks, HookCanEmit, Remit, and URIToken.
- Testnet enabled `HookOnV2` and NamedHooks.
- Mainnet reported `HookOnV2` and NamedHooks disabled and vetoed.

Supported is not the same as enabled. Re-query live definitions before every deployment decision. Mainnet compatibility must be proven independently from Testnet compatibility.

## Burn-to-mint clarification

Historic Xahau distribution references to burn-to-mint are not a general, ongoing bridge API and must not be presented as a current XRP↔XAH interoperability workflow. XRPL-Hermes ships no Xahau bridge/burn-to-mint builder. Any asset-transfer or bridge claim requires a separately audited, current protocol and operational source.

## Safe delivery sequence

1. Define one narrow behavior and non-goals.
2. Select Testnet and verify network ID `21338`.
3. Calculate and review the trigger mask.
4. Build with the current official Hooks toolchain.
5. Independently review source and resulting WASM.
6. Simulate the exact unsigned transaction.
7. Sign outside Hermes with a user-controlled Testnet wallet.
8. Verify the validated transaction, installed slot/hash, positive behavior, negative behavior, and rollback.
9. Audit before preparing a Mainnet proposal.
10. Require explicit human approval before any Mainnet signature or submission.

## Authoritative sources

See `references/xahau-hooks.md` for pinned commits, exact runtime commands, live feature snapshot, and acceptance vectors. Source pins were reviewed 2026-07-25; live amendment state must always be refreshed.
