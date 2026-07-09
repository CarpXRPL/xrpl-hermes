# Payment App Product Flow

Use this product playbook when the user wants to build checkout, invoices, payment links, tipping, P2P payments, remittance, receipts, or a merchant settlement app on XRPL.

## Product promise

A non-custodial payment product:

```text
payment request → unsigned Payment JSON → wallet handoff → ledger confirmation → receipt
```

The product never holds payer funds or keys.

## Triggers

- "build a payments app"
- "make checkout on XRPL"
- "invoice/payment links"
- "tips/donations"
- "RLUSD payment app"
- "detect when a payment arrives"

## Target user

Merchants, creators, community tools, bots, and builders who need fast XRPL settlement with clear receipts.

## XRPL primitives

- Payment: XRP, RLUSD, issued currencies
- DestinationTag / SourceTag
- Memos for invoice/order/agent attribution
- Cross-currency Payment with `SendMax`/deliver amount
- Checks for pull-style payments
- Escrow and Payment Channels only when the product specifically needs them

## Read first

- `skills/build-xrpl-product-flow.md`
- `skills/wallet-signing-ux-product-flow.md`
- `skills/agentic-payment-flow.md`
- `knowledge/02-xrpl-payments.md`
- `knowledge/58-rlusd-operations.md` for RLUSD
- `knowledge/61-xrpl-websocket-streams.md`
- `references/agentic-payments.md` when tags/memos/agent attribution matter

## Commands/tools

- `server-info`
- `account rDEST`
- `path-find rSENDER rDEST AMOUNT CUR:ISSUER`
- `build-payment --from rSRC --to rDST --amount DROPS [--source-tag N] [--dest-tag N] [--memo TEXT]`
- `build-cross-currency-payment --from rSRC --to rDST --deliver CUR:rISS:VALUE --send-max ...`
- `tx-info HASH`
- `subscribe streams=ledger,transactions`

## MVP deliverable

1. Payment request page with amount, asset, destination, memo/order id, and optional destination tag.
2. Unsigned JSON builder endpoint or local builder call.
3. Wallet handoff using the wallet signing UX flow.
4. Settlement detector that watches for `validated: true`.
5. Receipt page with tx hash, delivered amount, asset, destination, tags, and memo.

## Primitive map template

| Product feature | XRPL primitive/query | Command/tool | Safety owner |
|---|---|---|---|
| Create XRP payment request | Payment | `build-payment` | `agentic-payment-flow.md` + confirm-before-build on mainnet |
| Create issued/RLUSD payment request | Payment IOU | `build-payment` or `build-cross-currency-payment` | `agentic-payment-flow.md` |
| Quote cross-currency payment | Path finding | `path-find` | live quote required |
| Mark invoice paid | transaction lookup / stream | `subscribe`, `tx-info` | finality check |
| Diagnose failure | tx result classes | `tx-info`, `decode` | `failed-transaction-diagnosis-flow.md` |

## Testnet demo checklist

- One XRP payment request signs externally and validates.
- One issued-currency or RLUSD-style test payment path is checked; if unavailable, label unavailable and name the failed command.
- The app marks paid only after `tx-info` returns `validated: true`.
- A fake/missing tx hash remains unpaid.

## Mainnet-safe checklist

- Use `delivered_amount`, not only `Amount`, when reading completed payments.
- Every quote has a timestamp/ledger context and expires.
- Destination tags are required where the receiving account requires them.
- Idempotency is tx-hash based; replayed tx hashes do not pay twice.
- Initial amount caps and alerting exist before launch.

## Common failure modes

- Treating a submitted tx as final before validation.
- Missing partial-payment semantics in receipt logic.
- Float math for XRP instead of drops.
- Quoting cross-currency payments without live `path-find`.
- Polling too slowly or without backoff when `subscribe` is the right product layer.
