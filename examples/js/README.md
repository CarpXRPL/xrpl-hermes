# JavaScript / TypeScript examples (`xrpl.js`)

Runnable `xrpl.js` twins of the Python examples, for the web / Node / TypeScript
side of XRPL-Hermes. They are **builder-layer only**: each one constructs a
typed, unsigned, signer-ready transaction object and prints it as JSON.

They do **not** sign, do **not** submit, and never touch a seed — exactly like
the Python `build-*` CLI commands. Signing stays in your wallet/signing layer
(Xaman, Crossmark, or your own `xrpl.js` signer) which runs
`autofill → preview → sign → submitAndWait`. See
[`../../references/agentic-payments.md`](../../references/agentic-payments.md).

> The XRPL-Hermes CLI and MCP server stay Python (`xrpl-py`). These examples are
> for the code **you** write in a JS/TS project — the SDKs are interchangeable;
> pick the one that matches your stack.

## Run

```bash
cd examples/js
npm install            # pulls xrpl.js (xrpl@^5)
node build-xrp-payment.js
node build-rlusd-payment.js
node agent-receipt-nft.js
```

| File | Builds |
|---|---|
| `build-xrp-payment.js` | Unsigned XRP `Payment` with `SourceTag`, `DestinationTag`, and a hex-encoded `Memo` |
| `build-rlusd-payment.js` | Unsigned RLUSD issued-currency `Payment` using the 160-bit currency code (the literal `"RLUSD"` is invalid on-ledger) |
| `agent-receipt-nft.js` | Unsigned `NFTokenMint` that records an agent run / skill evolution as an on-chain receipt — compact base64 `data:` URI, enforces the 256-byte URI limit *after* encoding. Safe twin of "agent mints its own NFT": no seed, no signing, no submit. See [`../../skills/agent-receipt-flow.md`](../../skills/agent-receipt-flow.md) |

## Equivalent calls across stacks

| Concept | xrpl-py (Python) | xrpl.js (JS/TS) |
|---|---|---|
| XRP amount | `xrp_to_drops(10)` | `xrpl.xrpToDrops("10")` |
| Hex-encode a memo | `text.encode("utf-8").hex()` | `xrpl.convertStringToHex(text)` |
| Fill Fee/Sequence/LLS | `autofill(tx, client)` | `await client.autofill(tx)` |
| Sign + submit + wait | `submit_and_wait(tx, client, wallet)` | `await client.submitAndWait(signed.tx_blob)` |

Deeper xrpl.js reference: [`../../knowledge/31-xrpl-xrpljs.md`](../../knowledge/31-xrpl-xrpljs.md).
The Python twins live one directory up (`../example-build-payment.py`,
`../example-cross-currency.py`).

## Safety

These examples follow the canonical **Safety rules** block in
[`../../SKILL.md`](../../SKILL.md): testnet-first, no hardcoded seeds, builders
never sign, and amounts always go through `xrpToDrops` / 160-bit currency hex.
