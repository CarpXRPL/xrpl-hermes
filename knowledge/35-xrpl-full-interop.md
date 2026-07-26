# Multi-Network Interoperability — Safety and Certification Map

## Why this replaces the former “full interop” guide

The previous article contained unverified bridge routes, wallet matrices, stale endpoints, placeholder contracts, direct signing/submission examples, and speculative asset/NFT flows. It was not production evidence and has been retired.

XRPL L1, the XRPL EVM Sidechain, Xahau, Flare/Songbird, Axelar, and Arweave are distinct systems. Shared branding or XRP relevance does not make addresses, assets, signatures, finality, trust assumptions, or wallet support interchangeable.

## Current XRPL-Hermes boundary

| Surface | Local capability | Certification posture |
|---|---|---|
| XRPL L1 | live reads and structurally validated unsigned builders | certified per command/test matrix; new flows remain Testnet-first |
| Xahau | legacy `HookOn` calculation and validated hook-chain lookup | certified partial/read-only; no compile/build/sign/deploy |
| XRPL EVM Sidechain | validated balance/network reads plus explicit experimental contract intent | experimental read/build; no compile/simulation/deployment/bridge certification |
| Flare | chain-ID/freshness-checked FTSOv2 read plus labeled CoinGecko context | narrow read; FAssets/LayerCake quarantined |
| Axelar | Axelarscan registration lookup and GMP-index search | narrow/partial external read; no transfer certification |
| Arweave | point-in-time base-network storage-price estimate | narrow external read; no upload or retrieval guarantee |
| Evernode | knowledge discovery only | quarantined |
| Wallet integrations | Xaman payload handoff only where configured; other wallet claims require separate proof | external dependency |

## Network identity

Never reuse a network's identifier or endpoint for another network.

| Network | Identity |
|---|---|
| XRPL Mainnet | XRPL classic/X-address rules; native XRP |
| Xahau Mainnet | network ID `21337`; native XAH |
| Xahau Testnet | network ID `21338`; native XAH test funds |
| XRPL EVM Sidechain Mainnet | EVM chain ID must be read live and compared with current official docs before signing |
| XRPL EVM Sidechain Testnet | EVM chain ID must be read live and compared with current official docs before signing |

Xahau is not a bridge, sidecar, or execution layer for an XRPL L1 payment. A transaction on XRPL L1 does not cause a Xahau Hook to run unless a separately certified cross-network system explicitly observes and acts on it.

## Interop acceptance workflow

Before recommending or constructing any cross-network transfer:

1. Identify source network, destination network, source asset, destination asset, and exact desired result.
2. Load current official protocol/bridge documentation and pin the source/release.
3. Verify live chain/network IDs and RPC genesis/ledger identity.
4. Verify gateway/door accounts, contracts, token addresses/issuers, decimals, memo/tag encoding, minimums, fees, finality, pause state, and supported route from first-party sources and live state.
5. Document the bridge trust model, signer/validator set, custody, rate limits, upgrade/pause authority, proof mechanism, and recovery path.
6. Build only an unsigned intent or transaction for the exact network-aware serializer.
7. Simulate or estimate before signing.
8. Show the decoded destination, asset, amount, network, route, minimum, fees, and irreversible consequences to the user.
9. Let the user's wallet sign. Hermes does not receive keys.
10. Start with the smallest supported Testnet or deliberately monitored production amount.
11. Verify both source and destination validated/finalized receipts and reconcile net received amount.

If any route field is unknown or stale, stop and report the missing evidence. Do not substitute a plausible address or fee.

## Cross-network proof record

Retain:

- official source URLs and pinned versions;
- checked-at timestamps;
- source/destination chain IDs;
- gateway/contract/issuer provenance;
- unsigned decoded transaction;
- wallet handoff identifier;
- source transaction hash and validated ledger/block;
- bridge/message identifier;
- destination transaction hash and finalized block;
- gross amount, every fee, and net amount;
- errors, retries, refunds, and incident notes.

## Prohibited shortcuts

- No hardcoded unverified bridge account or contract.
- No placeholder ABI represented as a working bridge.
- No direct private-key or seed loading in examples.
- No raw broadcast helper presented as an end-to-end route.
- No wallet compatibility checkmark without current first-party evidence and an exercised flow.
- No “trustless,” “native,” “instant,” or time/fee promise without protocol evidence and a dated measurement.
- No claim that Xahau Hooks execute on XRPL Mainnet.

## Canonical references

- `references/xrpl-l1.md`
- `references/xrpl-evm-sidechain.md`
- `references/xahau-hooks.md`
- `references/flare-ftso.md`
- `references/axelar-bridge.md`
- `references/arweave-storage.md`
- `LIMITATIONS.md`
