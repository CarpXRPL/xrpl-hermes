# XRPL-Hermes examples

The supported pattern is signer-separated:

1. XRPL-Hermes produces **unsigned** transaction JSON with a validated `build-*` command.
2. The user reviews it and hands it to a compatible user-owned wallet/signing system.
3. XRPL-Hermes verifies the final result with `tx-info` and requires `validated: true`.

No example reads a seed/private key, signs, submits or uploads.

## Runnable build/read examples

| Example | Status |
|---|---|
| `example-agent-receipt.py` | Build-only unsigned `NFTokenMint` receipt; no signing/submission |
| `example-token-safety-check.py` | Read-only token ledger snapshot/risk check |
| `example-telegram-bot.py` | Read-only bot plus unsigned Payment preview |
| `example-discord-bot.py` | Read-only bot pattern; verify current dependencies before deployment |
| `js/agent-receipt-nft.js` | Build-only JavaScript receipt twin |

Most transaction examples are one CLI call:

```bash
python3 -m scripts.xrpl_tools build-payment --from rSRC --to rDST --amount 1000000
```

Use the command table in [`../SKILL.md`](../SKILL.md) for exact builder syntax. Placeholder addresses above are documentation tokens, not executable addresses.

## Retired direct-sign examples

The following filenames are retained as explicit migration stubs. Running one returns a JSON retirement notice and exit code 2; it never reads a key, signs or submits:

- `example-build-payment.py`
- `example-setup-trustline.py`
- `example-create-offer.py`
- `example-cross-currency.py`
- `example-mint-nft.py`
- `example-nft-buy.py`
- `example-amm-deposit.py`
- `example-clawback.py`
- `example-multisig.py`
- `example-evm-swap.py` (also lacks a certified route/router)

Use the named `build-*` replacement in each stub, external signing, and validated-ledger verification.
