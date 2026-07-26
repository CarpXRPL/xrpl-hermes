# Flare FTSOv2 — Narrow Read Card

## Certified surface

`flare-ftso PAIR…` resolves the FTSOv2 contract through Flare's registry and reads feeds with `eth_call`.

Require:

- observed Flare chain ID `14`;
- registry-resolved FTSOv2 address;
- feed value and decimals;
- source timestamp and age;
- staleness flag/threshold;
- fetch timestamp and RPC URL;
- explicit missing/error feeds.

```bash
python3 scripts/xrpl_tools.py flare-ftso XRP/USD FLR/USD
```

`flare-price` is CoinGecko market context only, never oracle proof.

## Not implemented

FAssets, LayerCake, FTSO-v1 recipes, transaction signing/submission and fabricated HTTP services are not supported.

Official sources:

- https://dev.flare.network/ftso/feeds
- https://dev.flare.network/network/guides/flare-contracts-registry
