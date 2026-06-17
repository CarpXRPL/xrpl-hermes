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

## rippled 3.2.0 (released 2026-06-15)
Latest release ([notes](https://github.com/XRPLF/rippled/releases/tag/3.2.0)): a cleanup release that **retires** many legacy `fix*` amendments and renames the binary to `xrpld` (per **XLS-0095**; read the notes before upgrading). Ripple **rotated the GPG signing key** — existing installs should download and trust the new key. Live-checked 2026-06-16: public mainnet still reported `BuildVersion 3.1.3`, and 3.2.0-line amendments (e.g. `fixCleanup3_2_0`) are not yet on the mainnet `feature` table (`amendment fixCleanup3_2_0` → `UnknownAmendment`) — they activate via the normal validator-upgrade + 2-week majority process. Deeper note: `knowledge/37-xrpl-amendments.md`.

## Deeper material in `knowledge/37-xrpl-amendments.md`
- Chronological catalog of every enabled amendment since 2016
- Devnet/testnet activation for testing pre-enable features
- Amendment IDs for direct `Feature` lookups
- Veto mechanics for validator operators
