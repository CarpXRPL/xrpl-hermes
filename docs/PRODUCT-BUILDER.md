# XRPL-Hermes Product Builder Mode

XRPL-Hermes is moving beyond one-off transaction help into a repeatable product-building layer for XRPL builders.

Product Builder Mode helps a user go from:

```text
idea → intake → archetype → architecture → XRPL primitive map → MVP → testnet demo → mainnet-safe launch gates
```

It stays open-source and self-hosted: your runtime, your infrastructure, your keys. XRPL-Hermes designs, maps, builds unsigned JSON, and verifies with live tools. It does **not** custody funds, host a SaaS runtime, sign for users, or provide legal advice.

Canonical flow: [`skills/build-xrpl-product-flow.md`](../skills/build-xrpl-product-flow.md).

## When to use Product Builder Mode

Use it when the user wants software other people or agents will use:

- app
- dashboard
- API
- marketplace
- launchpad
- product/service
- wallet UX
- treasury tool
- token intelligence bot
- agentic payment service

If the deliverable is a single transaction signed by the user's wallet today, use an operation flow instead.

## Standard 5-box architecture

```text
┌───────────┐   ┌─────────────┐   ┌────────────────┐   ┌────────────────┐   ┌────────────────────┐
│ UI/client │ → │ app backend │ → │ XRPL read layer│ → │ signing layer  │ → │ monitor/attribution│
└───────────┘   └─────────────┘   └────────────────┘   └────────────────┘   └────────────────────┘
```

| Box | What it owns |
|---|---|
| UI/client | user interface, decoded transaction preview, wallet links/QRs |
| app backend | product state, API routes, receipts, queues, rate limits |
| XRPL read layer | Clio/rippled reads, WebSocket subscriptions, `tx-info` verification |
| signing layer | wallet handoff by default; optional user-owned policy signer for the user's own funds |
| monitor/attribution | `SourceTag`, `DestinationTag`, `Memos`, alerts, receipts, incident response |

## Archetype catalog

| Product archetype | Canonical planning file | Wedge deliverable |
|---|---|---|
| Umbrella product intake | `skills/build-xrpl-product-flow.md` | one-pager, 5-box architecture, primitive map, MVP/testnet/mainnet checklists |
| Wallet signing UX | `skills/wallet-signing-ux-product-flow.md` | external wallet login + decoded unsigned JSON handoff |
| Payment app | `skills/payment-app-product-flow.md` | payment request → external wallet handoff → ledger receipt |
| Agentic payments / x402 | `skills/agentic-payments-product-flow.md` | design template; x402 middleware is not shipped |
| Token intelligence dashboard/API/bot | `skills/token-intelligence-product-flow.md` | live token report with confidence and missing-data list |
| Token launch platform | `skills/token-launch-product-flow.md` | non-custodial creator wizard driven by live ledger state |
| Treasury/multisig tool | `skills/treasury-tool-product-flow.md` | read-only treasury cockpit + unsigned proposal workflow |
| NFT/community product | `skills/nft-community-product-flow.md` | mint/offer/holder-verification loop |
| AMM/DEX product | `skills/amm-dex-product-flow.md` | pool/orderbook explorer + timestamped quote view |
| Xahau Hook app | `skills/xahau-hook-app-product-flow.md` | HookOn calculation and installed-Hook inspection; compile/deploy requires external setup |
| RWA/compliance rails | `skills/rwa-compliance-product-flow.md` | technical planning; legal/compliance services and RequireAuth trust-line authorization are not shipped |
| Self-hosted XRPL agent stack | `skills/xrpl-agent-stack-product-flow.md` | MCP-powered read-only agent job + external wallet signing loop |

## How to use from Hermes

1. Load XRPL-Hermes.
2. Ask for a product, not just a transaction: "Build a payments app", "Build a token safety dashboard", "Build a launchpad".
3. The agent should route to `skills/build-xrpl-product-flow.md`, ask only missing intake questions, and produce the product artifacts.
4. When code is needed, hand the implementation brief to a coding agent and verify the result with live XRPL tools.

## How to use from MCP clients

MCP clients can discover and read the product flow:

1. `xrpl_knowledge_index`
2. `xrpl_knowledge` with `skills/build-xrpl-product-flow.md`
3. `xrpl_run` for grounded live checks such as `server-info`, `account`, `tx-info`, `token-intel`, `amm-info`, `path-find`, and builders when the chosen operation flow requires them.

## What this is not

- not custody
- not a hosted runtime
- not a wallet replacement
- not legal/securities/compliance advice
- not market predictions
- not automatic mainnet execution
- not a guarantee of liquidity, holders, or token safety

The promise is narrower and stronger: XRPL-Hermes helps builders design, map, verify, and safely hand off XRPL products while keys stay with the user.
