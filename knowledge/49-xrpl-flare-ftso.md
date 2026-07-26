# Flare FTSO — Certified Narrow Read

## Release status

**FTSOv2 read: narrow on-chain. Market fallback: context only. FAssets/LayerCake: quarantined.**

### `flare-ftso [PAIR ...]`

XRPL-Hermes resolves `FtsoV2` through Flare's contract registry and reads requested feeds with `eth_call`. Output must identify:

- Flare RPC;
- observed chain ID (`14` for Flare Mainnet);
- resolved FTSOv2 contract;
- feed value, decimals and source timestamp;
- feed age/staleness status;
- fetch timestamp;
- missing/error feeds.

A returned value is usable as oracle evidence only when the chain ID, contract resolution, feed ID and freshness checks pass.

```bash
python3 scripts/xrpl_tools.py flare-ftso XRP/USD FLR/USD
```

### `flare-price [SYMBOL ...]`

This is CoinGecko market context, not an FTSO proof. It must include the source URL and fetch time and must surface rate-limit/API failures.

## Quarantined material

The former deep article included obsolete FTSO-v1 interfaces, fabricated FAssets HTTP APIs, an obsolete explorer action and a nonexistent LayerCake API. Those recipes were removed.

XRPL-Hermes does not currently certify:

- FAssets mint/redeem lifecycle;
- agent/vault collateral state;
- LayerCake transfers;
- Flare transaction signing or submission;
- production smart-contract integration beyond read-only FTSOv2 evidence.

Restoring any of those requires current official contracts/packages, network/release status, reproduced Testnet lifecycle evidence, collateral/liquidation analysis, external-wallet signing and finalized-result verification.

## Official sources

- https://dev.flare.network/ftso/feeds
- https://dev.flare.network/network/guides/flare-contracts-registry
- https://flare.network/

Source review date: **2026-07-26**.
