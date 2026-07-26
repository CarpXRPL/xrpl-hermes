# Axelar — Narrow Read-Only Card

## Status

- `bridge-status`: Axelarscan chain-registration lookup only.
- `bridge-tx`: Axelar GMP-index search only.
- ITS/token transfer building, signing, submission and recovery: **not implemented**.

Registration does not certify a route, asset, amount, fee, liquidity, pause state or transfer result. GMP search is not a general token-transfer receipt checker.

## Commands

```bash
python3 scripts/xrpl_tools.py bridge-status xrpl xrpl-evm
python3 scripts/xrpl_tools.py bridge-tx SOURCE_TX_HASH
```

Expected evidence includes provider URL, fetch time, returned registration fields or GMP records, and an explicit capability label.

## Hard rules

- Never infer current gateway/contract addresses or memo schemas.
- Never place a seed/private key in an Axelar flow.
- Never send funds based only on registration output.
- Require current official ITS/GMP schema, external-wallet decoded preview, Testnet proof and destination-side finalized verification before supporting transfers.

Official sources:

- https://docs.axelar.dev/
- https://docs.axelar.dev/dev/send-tokens/interchain-tokens/xrpl/
- https://axelarscan.io/
