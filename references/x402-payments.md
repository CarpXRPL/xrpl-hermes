# x402 / HTTP-402 Payments on XRPL — Reference Card

Machine-to-machine "pay-per-request" payments: an agent hits a paid HTTP endpoint, the server
answers **402 Payment Required**, the agent settles on the XRP Ledger, retries, and gets the
resource — no API keys, no human in the loop.

> **Sources (verify before production).** Package names, headers, network ids, and facilitator
> endpoints below are summarized from the official docs and the t54 facilitator and may change —
> confirm against them before shipping:
> - Agentic payments with x402 — https://xrpl.org/docs/agents/agentic-payments-x402/
> - t54 XRPL x402 facilitator — https://xrpl-x402.t54.ai (docs at `/docs`)
> - Reference impl: `x402_xrpl` on PyPI (Python); `x402Fetch` (TypeScript)
>
> This is an **integration plan**, not a shipped Hermes feature. Hermes builds/inspects the XRPL
> Payment that settles a 402 charge; **signing stays in the wallet layer** (`references/agentic-payments.md`).

## What x402 is

x402 extends HTTP's long-dormant **402 Payment Required** status into a real payment protocol:
*"an open protocol for HTTP-native machine-to-machine payments."* XRPL is a natural settlement
layer because of **deterministic finality** — the agent knows within ~3–5 seconds whether the
payment confirmed, with a clean expiry and no ambiguous pending state.

## The three parties

| Party | Role |
|---|---|
| **Agent (payer client)** | Wants a protected resource; signs + submits the XRPL Payment. |
| **Merchant (server)** | Protects an endpoint; returns 402 with price + pay-to address + facilitator; verifies the receipt and serves the resource. |
| **Facilitator** | Verifies the on-chain payment by tx hash and issues a receipt the merchant trusts. **No custody** — it never holds keys or signs. t54 runs a reference facilitator. |

## The flow (6 steps)

1. Agent calls a protected HTTP endpoint.
2. Merchant returns **`402 Payment Required`** with price, pay-to XRPL address, and facilitator URL.
3. Agent submits a (pre)signed **XRPL Payment** for the quoted amount to the merchant's address.
4. Agent obtains a **receipt** from the facilitator by submitting the transaction hash.
5. Agent retries the original request with the receipt in the **`X-PAYMENT`** header.
6. Merchant verifies the receipt and returns the resource (settlement details in a response header).

**Replay protection:** the payment is bound to an invoice id via `Memos`/MemoData, so a receipt
can't be reused. Validated-settlement mode can wait for ledger confirmation before releasing.

## Settlement assets & pricing

- **XRP** (drops; 1 XRP = 1,000,000 drops) and **RLUSD** for dollar-stable pricing. (t54 also lists USDC.)
- Prices are quoted in drops. Rough tiers from the docs: free `0`; lightweight API `100–1,000`;
  standard query `1,000–10,000`; AI inference `10,000–100,000` drops. **Quote in drops; convert with `xrp_to_drops`.**

## Network ids & facilitators (per docs — verify)

| Environment | `network` | Facilitator | Notes |
|---|---|---|---|
| **Testnet** | `xrpl:1` | `https://xrpl-facilitator-testnet.t54.ai` | Best-effort, **no SLA — not for production.** Default here. |
| **Mainnet** | `xrpl:0` | `https://xrpl-facilitator-mainnet.t54.ai` | Real XRP. Behind explicit human approval. |

Facilitator exposes spec endpoints `/supported`, `/verify`, `/settle`. Moving testnet→mainnet is a
config change (network id + facilitator url + a funded mainnet wallet), not a code rewrite.

## Code patterns (illustrative — confirm signatures against current docs)

### Merchant / server (Python, FastAPI)
```python
from x402_xrpl.server import require_payment

app.middleware("http")(
    require_payment(
        path="/hello",
        price="1000",                 # drops
        pay_to_address="rYourWalletAddress",
        facilitator_url="https://xrpl-facilitator-testnet.t54.ai",
        network="xrpl:1",             # testnet; xrpl:0 for mainnet
        asset="XRP",                  # or RLUSD
    )
)
```
Node/Express merchants use an equivalent `requirePayment()` middleware.

### Agent / client (Python, xrpl-py)
```python
from x402_xrpl.clients import x402_requests

session = x402_requests(
    buyer_wallet,                                   # signs locally; seed from env/KMS, never chat
    rpc_url="https://s.altnet.rippletest.net:51234/",
    scheme_filter="exact",
)
response = session.get(resource_url)                # auto-handles 402: pays, retries, returns result
```
`x402_requests` wraps `requests`: on a 402 it signs the required payment, includes it on retry, and
returns the final response. TypeScript clients use `x402Fetch` (Node 18+).

## Safety (same rules as any XRPL value transfer)

- **Testnet first.** Use `xrpl:1` + the testnet facilitator until the flow is proven.
- **Keys stay in the wallet/signing layer.** The buyer wallet signs locally; seeds come from env
  (dev) or KMS/HSM (prod) — never from prompts, logs, or the agent's chat surface.
- **Cap spend.** Enforce a per-request and per-session drops budget; require explicit approval to
  raise it or to use mainnet (`xrpl:0`).
- **Verify destination + amount** out of the 402 response before signing; bind to an invoice id in `Memos`.
- **Don't trust the testnet facilitator for production** (no SLA).

## Hermes integration plan (testnet-first)

1. **Build/inspect** the settling XRPL Payment with `build-payment` (`--memo` carries the invoice id; `--source-tag` attributes the agent). JSON only — no keys.
2. **Decode/verify** an incoming payment (`tx-info <hash>`, `decode <blob>`) to confirm amount/destination/memo before serving a resource.
3. **Document** the t54 facilitator handoff; signing + `submitAndWait` happen in the wallet layer.
4. Keep a per-session **drops budget** and a mainnet-approval gate.

Related: `references/agentic-payments.md`, `references/rlusd.md`, `knowledge/02-xrpl-payments.md`,
`knowledge/65-agent-freshness-and-source-policy.md`.
