# XRP Ledger L1 — Operational Reference

## Identity

XRPL L1 is the XRP Ledger network. It is distinct from the XRPL EVM Sidechain and Xahau. Do not reuse their endpoints, chain/network IDs, assets, addresses or transaction serializers as XRPL L1 evidence.

## Source of truth

Use live validated XRPL methods for current state:

- `server-info` — endpoint/server/validated-ledger evidence;
- `ledger validated` — validated ledger identity;
- `amendments` / `amendment NAME` — enabled/supported amendment status;
- `account`, `account_objects`, `trustlines`, `account-tx` — account/object evidence;
- `book-offers`, `amm-info`, `path-find` — live liquidity evidence;
- `tx-info HASH` — final transaction result; require `validated: true`.

Official protocol documentation: <https://xrpl.org/docs.html>. Public node endpoints and operational characteristics can change; verify them live before relying on them.

## Current rules

- Native XRP amounts are integer drops; one XRP is 1,000,000 drops.
- Only exact uppercase `XRP` denotes the native asset. Other currency identifiers are issued currencies.
- Raw transaction AccountID fields use classic r-addresses. Decode X-addresses explicitly so embedded destination tag/network semantics are not discarded.
- Accounts can be deleted only through `AccountDelete` when protocol conditions are met; deletion is not generally available on demand.
- Fees, reserves, amendment state, throughput and close timing are live operational facts, not constants. Query rather than hardcode.

## Transaction workflow

1. Select explicit network and verify live identity.
2. Read validated prerequisite state.
3. Use the relevant `build-*` command to create unsigned JSON.
4. Review account, destination, tags, asset/issuer, amount, flags, fees/limits and irreversible effects.
5. Hand off to a compatible user-owned external signer. Hermes never receives the seed/private key.
6. Verify the final hash with `tx-info`; accept completion only when validated and the final result code matches intent.

New flows are Testnet-first. Mainnet use requires explicit authorization, controlled sizing and monitoring.

## Third-party APIs

No third-party explorer/token endpoint is certified by this card. Before use, require current provider documentation, TLS/auth/schema/pagination/rate-limit/error semantics, a successful live fixture and a timestamp. Metadata is not ledger truth.

Reviewed: **2026-07-26**.
