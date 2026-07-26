# XRPL-Hermes examples

Examples follow the same custody model as the CLI:

1. read live state or build unsigned intent;
2. review the complete transaction;
3. authorize it in a user-controlled wallet;
4. verify the returned hash with `tx-info`.

No example reads a seed, signs, broadcasts, or uploads data.

## Python

| Example | Capability |
|---|---|
| `example-agent-receipt.py` | Unsigned NFTokenMint receipt intent |
| `example-token-safety-check.py` | Read-only token ledger snapshot |
| `example-telegram-bot.py` | Read-only bot with unsigned Payment preview |
| `example-discord-bot.py` | Read-only bot pattern |

Most transaction builds are a single CLI call:

```bash
xrpl-hermes build-payment --from rSOURCE --to rDESTINATION --amount 1000000
```

## JavaScript

See [`js/`](js/) for build-only `xrpl.js` examples. They produce unsigned JSON and do not contain wallet secrets.
