# XRPL L1 ↔ EVM Sidechain Interop — Certification Boundary

## Status

**Experimental / not transfer-certified.** This file no longer contains bridge payment builders, private-key examples, placeholder ABIs, raw broadcasts, invented door accounts, or speculative token representations.

XRPL-Hermes can inspect selected public XRPL EVM and Axelar status surfaces. It does not currently construct, sign, submit, or guarantee an XRPL L1 ↔ EVM bridge transfer.

## Why the former examples were removed

A real bridge transaction depends on current:

- source and destination chain IDs;
- gateway/door accounts and EVM contracts;
- route and asset support;
- XRPL memo/tag and EVM calldata formats;
- token addresses/issuers and decimals;
- minimums, fees, gas, rate limits, and pause state;
- validator/federator/signing model;
- finality and refund/recovery procedures.

The removed examples used environment-provided secrets, direct signing/broadcast, placeholder accounts/contracts/calldata, and generic mint/burn logic without proving those fields against a live bridge. They were unsafe to copy.

## Read-only commands

```bash
python3 scripts/xrpl_tools.py evm-balance 0xADDRESS [mainnet|testnet]
python3 scripts/xrpl_tools.py evm-bridge [mainnet|testnet]
python3 scripts/xrpl_tools.py bridge-status
python3 scripts/xrpl_tools.py bridge-tx TX_HASH
```

Interpretation:

- `evm-balance` is a JSON-RPC balance read on the selected EVM network.
- `evm-bridge` reports only EVM RPC identity/latest-block status and explicitly sets `BridgeCertified: false`.
- `bridge-status` and `bridge-tx` depend on public Axelar APIs and may be stale, unavailable, or incomplete.
- None of these commands proves that an asset route is open or safe.

## Required evidence for a transfer builder

Before adding or using any bridge builder, obtain and preserve:

1. Current first-party bridge documentation and source/release pins.
2. Live chain IDs and endpoint identity.
3. Exact gateway/door and contract addresses with provenance.
4. Exact asset representation, address/issuer, decimals, and supply/custody model.
5. Canonical deposit/withdraw encoding and destination-address rules.
6. Live minimum, fees, gas, limits, pause state, and expected finality.
7. Trust model, validator/federator set, upgrade authority, emergency controls, audits, and incident history.
8. Local structural and signing serialization validation for both network transactions.
9. End-to-end Testnet evidence with source receipt, bridge message, destination receipt, and net-amount reconciliation.
10. Explicit approval before any monitored production canary.

## Non-custodial flow

A future accepted flow must:

- build unsigned network-specific payloads only;
- reject placeholder or unverified addresses/contracts;
- display decoded source, destination, amount, asset, route, fees, and network;
- hand each signature to the user's network-appropriate wallet;
- never receive seeds/private keys;
- verify source validation, message status, destination finality, and net amount;
- stop safely on timeout, pause, route drift, fee/minimum drift, or receipt mismatch.

## Xahau exclusion

Xahau is not part of an XRPL L1 ↔ EVM bridge path by default. Do not use the Xahau endpoint as a “Hook-style sidecar” for XRPL or EVM transactions. Any system that explicitly includes Xahau requires its own independently certified route and signer model.

## Acceptance status

| Capability | Status |
|---|---|
| EVM JSON-RPC balance read | implemented experimental read with configured/observed chain-ID enforcement |
| EVM network identity read | implemented; explicitly not bridge metadata or transfer certification |
| Axelar registration/GMP-index lookup | external dependency; no route or transfer certification |
| XRPL → EVM unsigned bridge builder | not implemented/certified |
| EVM → XRPL unsigned bridge builder | not implemented/certified |
| Bridge signing/submission | intentionally unavailable |
| Production transfer recommendation | blocked pending full proof |

See `references/xrpl-evm-sidechain.md`, `references/axelar-bridge.md`, `LIMITATIONS.md`, and current first-party bridge documentation.
