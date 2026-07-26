# Xahau Hooks — Certified Operational Card

## Capability boundary

**Available surface:**

- Calculate legacy `HookOn` values from Xahau transaction-type IDs.
- Read installed hook chains from validated Xahau Mainnet or Testnet ledgers.
- Report network ID, endpoint, server version, ledger index/hash, chain slot, and RPC errors.
- Explain the signer-separated Testnet-first workflow.

**Not implemented by XRPL-Hermes:** Hook source generation, compilation, WASM validation, `SetHook` construction/serialization, signing, submission, or deployment. Use the official Xahau toolchain and a user-controlled signer. Do not claim Hermes deployed a Hook.

## Networks

| Network | NetworkID | HTTP JSON-RPC | WebSocket |
|---|---:|---|---|
| Mainnet | `21337` | `https://xahau.network` | `wss://xahau.network` |
| Testnet | `21338` | `https://xahau-test.net` | `wss://xahau-test.net` |

A Xahau transaction must carry the network's `NetworkID`. Never reuse an XRPL endpoint or assume that supported amendments are enabled.

## Safe commands

```bash
# Exactly 64 hex characters; no 0x prefix
python3 scripts/xrpl_tools.py hooks-bitmask Payment Invoke

# Validated-ledger read with explicit network
python3 scripts/xrpl_tools.py hooks-info rACCOUNT testnet
python3 scripts/xrpl_tools.py hooks-info rACCOUNT mainnet
```

`hooks-info` accepts classic `r...` addresses only. An unfunded/missing account or malformed request is an error, not proof of zero installed Hooks.

## HookOn

`HookOn` is a 256-bit `Hash256` field:

- For every transaction type except `SetHook` (`tt=22`), a **zero** bit enables firing and a **one** bit suppresses firing.
- Bit 22 is special and active-high: **one** enables firing on `SetHook`.
- Bit positions are transaction-type numeric IDs, not an arbitrary display order.
- JSON encoding is exactly 64 hexadecimal characters without `0x`.

Examples:

| Intended trigger set | HookOn |
|---|---|
| none | `FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFBFFFFF` |
| `Payment` | `FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFBFFFFE` |
| `SetHook` | `FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF` |
| `Payment`, `Invoke` | `FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF7FFFFFFFFFFFFFFFFFFBFFFFE` |

Always calculate; do not hand-edit a mask.

## SetHook facts

- Transaction name: `SetHook`, never `HookSet`.
- `Hooks` is required and contains 1–10 positional `{ "Hook": {...} }` objects.
- Position in the array maps to position in the account's Hook chain.
- `CreateCode` is hex-encoded WASM bytes, not base64.
- `HookHash`, `HookNamespace`, `HookOn`, and `HookCanEmit` are 64-hex-character fields.
- Creation requires `HookApiVersion: 0` under the currently deployed protocol.
- Hook-level flags: `hsfOVERRIDE=1`, `hsfNSDELETE=2`, `hsfCOLLECT=4`.
- Install/update/delete/namespace-delete are distinct field/flag combinations. Never infer deletion from an empty `{ "Hook": {} }`; that positional object is a no-op.
- Parameters are nested `HookParameter` entries; grants are nested `HookGrant` entries. Validate all current limits against the target network definitions and simulate before signing.

XRPL-Hermes intentionally does not emit a `SetHook` template because it cannot yet serialize and protocol-validate one using the released Python runtime.

## Amendment-sensitive fields

Live definitions checked 2026-07-25:

| Feature | Mainnet | Testnet |
|---|---|---|
| Hooks | enabled | enabled |
| HookCanEmit | enabled | enabled |
| HookOnV2 (`HookOnIncoming` / `HookOnOutgoing`) | disabled/vetoed | enabled |
| NamedHooks (`HookName`) | disabled/vetoed | enabled |
| Remit | enabled | enabled |
| URIToken | enabled | enabled |

This is a dated observation, not a permanent guarantee. Query `server_definitions.json` or `feature` on the chosen network before using amendment-gated fields. A Testnet transaction using `HookOnV2` is not Mainnet-portable while Mainnet has that feature disabled.

## Testnet acceptance gate

Before any Mainnet proposal:

1. Compile using the current official Xahau Hooks toolchain.
2. Review the WASM and source; never accept an opaque binary.
3. Verify `NetworkID=21338`, Hook chain slot, flags, namespace, parameters, grants, and `HookOn`.
4. Use Xahau `simulate` where supported; reject any malformed/preflight result.
5. Sign with a user-controlled Testnet wallet outside Hermes.
6. Confirm the validated `SetHook` transaction and installed hash/slot.
7. Exercise one triggering and one non-triggering transaction.
8. Rehearse rollback/deletion and verify the validated post-state.
9. Audit independently before considering Mainnet.

## Pinned sources


- Xahaud protocol: `Xahau/xahaud@bb244ef7729503a0317bcff0f8fdaa93ca5cb7d2`
  - `include/xrpl/protocol/detail/transactions.macro`
  - `include/xrpl/hook/Enum.h`
  - `src/xrpld/app/tx/detail/SetHook.cpp`
  - `src/xrpld/app/hook/applyHook.cpp`
- Xahau docs: `Xahau/Xahau-Docs@d7efa48a277cd35e4c33e33d223124e02e766eb1`
- Hooks toolkit: `Xahau/hooks-toolkit-ts@8e9025a15924bc7e34d3804448698160f36bf14a`
- Official docs: <https://xahau.network/docs/hooks/concepts/hookon-field>
- Live definitions: <https://xahau.network/server_definitions.json> and <https://xahau-test.net/server_definitions.json>
