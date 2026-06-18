# XRPL-Hermes examples (Python)

Runnable Python examples. They fall into **three layers — know which one you're
running.** The signer-separated model is the whole point: builders produce
*unsigned* JSON; your wallet/signing layer signs; **keys stay with you.**
JavaScript/TypeScript (`xrpl.js`) build-only twins live in [`js/`](js/).

## 1. Builder layer — unsigned, no seed, no signing

Construct signer-ready transaction JSON and print it. They never read a seed,
never sign, and never submit — exactly like the `build-*` CLI commands and the
[`js/`](js/) twins.

| Example | Builds |
|---|---|
| `example-agent-receipt.py` | Unsigned `NFTokenMint` recording an agent run / skill evolution as an on-chain receipt (compact base64 `data:` URI, 256-byte limit enforced after encoding). Twin of [`js/agent-receipt-nft.js`](js/agent-receipt-nft.js); flow in [`../skills/agent-receipt-flow.md`](../skills/agent-receipt-flow.md). |

Most builders are one CLI call — `python3 scripts/xrpl_tools.py build-payment …`
emits the same unsigned JSON. Full command list: the tool table in [`../SKILL.md`](../SKILL.md).

## 2. Wallet layer — signs + submits with YOUR testnet seed

These demonstrate the **other half** of the signer-separated model working end to
end: the *user's* wallet/signing stack autofills, signs, and submits on
**testnet**. They are intentionally **not** build-only — they show that the part
the agent never touches (the keys) lives here, in your stack. This is the North
Star in practice: *the agent builds; your wallet signs.*

Each reads `XRPL_SEED` from the environment (never hardcoded, never committed) and
targets testnet. Move to mainnet deliberately, behind explicit approval.

```bash
export XRPL_SEED=sEd...            # a funded testnet wallet; faucet: https://faucet.altnet.rippletest.net
python3 examples/example-build-payment.py
```

| Example | Signs + submits (testnet) |
|---|---|
| `example-build-payment.py` | sends XRP (`Payment`) |
| `example-setup-trustline.py` | opens a trust line (`TrustSet`) |
| `example-create-offer.py` | places a DEX offer (`OfferCreate`) |
| `example-cross-currency.py` | cross-currency payment |
| `example-mint-nft.py` | mints an NFT (`NFTokenMint`) |
| `example-nft-buy.py` | buys an NFT |
| `example-amm-deposit.py` | adds AMM liquidity |
| `example-clawback.py` | issuer clawback |
| `example-multisig.py` | multisigned submission |

## 3. Read-only — live queries, no wallet

| Example | Reads |
|---|---|
| `example-token-safety-check.py` | live token risk report (exit code 0/1/2 for scripts) |
| `example-telegram-bot.py` · `example-discord-bot.py` | bot patterns: query the ledger, alert |
| `example-evm-swap.py` | XRPL EVM Sidechain swap pattern |

---

**Safety (all examples):** no seeds or private keys are committed; builder
examples never sign; wallet-layer examples sign only with *your* env-supplied
testnet seed. See [`../SECURITY.md`](../SECURITY.md) and the Safety rules in
[`../SKILL.md`](../SKILL.md).
