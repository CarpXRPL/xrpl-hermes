# AMM / DEX Product Flow

Use this playbook when the user wants a swap UI, DEX interface, AMM/LP dashboard, pool analytics product, or quote surface.

## Product promise

A live-data-first DeFi product:

```text
pool/orderbook reads → timestamped quote → decoded unsigned trade/LP JSON → wallet handoff → validated result/position view
```

## Triggers

- "build a swap UI"
- "DEX interface"
- "LP dashboard"
- "pool analytics"
- "quote XRP/token swaps"

## Target user

DeFi builders, LP communities, dashboards, and trading UX projects.

## XRPL primitives

- OfferCreate and order books
- AMMCreate / AMMDeposit / AMMWithdraw / AMMVote / AMMBid
- path-find across AMM+CLOB liquidity
- LP token accounting via live AMM state

## Read first

- `skills/build-xrpl-product-flow.md`
- `skills/wallet-signing-ux-product-flow.md`
- `skills/amm-bot-flow.md` if automation/trading behavior is involved
- `knowledge/04-xrpl-dex.md`
- `knowledge/05-xrpl-amm.md`
- `knowledge/34-xrpl-amm-bots.md`

## Commands/tools

- `amm-info ASSET1 ASSET2`
- `book-offers TAKER_GETS TAKER_PAYS`
- `path-find rSENDER rDEST AMOUNT CUR:ISSUER`
- `build-offer`
- `build-amm-create`
- `build-amm-deposit`
- `build-amm-withdraw`
- `build-amm-vote`
- `build-amm-bid`

## MVP deliverable

1. Read-only pool explorer: reserves, fee, LP token, auction slot.
2. Orderbook panel from `book-offers`.
3. Quote panel with ledger/timestamp and expiry.
4. Unsigned trade or LP transaction builder with decoded preview.
5. Post-signing position/tx confirmation using live reads.

## Testnet demo checklist

- Pool/orderbook renders from live data.
- Quote expires and refreshes.
- One unsigned OfferCreate or AMMDeposit is generated and decoded.
- Confirm a testnet trade/LP action with `tx-info` if signed externally.

## Mainnet-safe checklist

- Slippage/deviation warning exists.
- Quotes expire quickly and name source ledger/time.
- Single-asset AMM deposit/withdraw price impact is explained.
- AMM bid/vote flows require explicit confirmation.
- Product does not claim guaranteed execution from stale quotes.

## Common failure modes

- Stale quote presented as executable.
- Double-counting AMM liquidity when `path-find` already includes routes.
- Building a matching engine instead of using XRPL as the matching engine.
- Misexplaining AMM auction slot or LP token accounting.
