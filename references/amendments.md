# Amendments — Quick Reference

Condensed from `knowledge/37-xrpl-amendments.md`. **Never trust a static list — check live state first:**

```bash
python3 -m scripts.xrpl_tools amendments            # full live inventory
python3 -m scripts.xrpl_tools amendment MPTokensV1  # one amendment's status
```

## How activation works
- Validators signal via `EnableAmendment` pseudo-transactions; **80%+ of trusted validators for two consecutive weeks** activates an amendment, permanently.
- The two-week window resets if support drops below 80%.
- `feature`/`FeatureAll` RPC reports `enabled` / `supported` / `vetoed` per amendment.

## Build-time rule
A transaction type that depends on a non-enabled amendment fails on mainnet even though current servers *support* it. The MPT, Credential, Oracle, and Batch builders in this repo already check live status and warn; for anything else, run `amendment NAME` before building.

## Status snapshot (verify live — this ages)
Checked live 2026-06-10 via `amendment NAME` against mainnet: **enabled** — `MPTokensV1`, `AMMClawback`, `Credentials`, `PriceOracle`, `Clawback`, `TokenEscrow`, `PermissionedDEX`. **Supported but not enabled** (build-only on mainnet) — `Batch`, `PermissionDelegation`, `XChainBridge`, `DynamicMPT`, `LendingProtocol`, `SingleAssetVault`.

## Deeper material in `knowledge/37-xrpl-amendments.md`
- Chronological catalog of every enabled amendment since 2016
- Devnet/testnet activation for testing pre-enable features
- Amendment IDs for direct `Feature` lookups
- Veto mechanics for validator operators
