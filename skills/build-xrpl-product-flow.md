# Build XRPL Product Flow — Product Builder Mode

Use this flow when the user wants to build an **application, platform, dashboard, API, bot, marketplace, product, service, startup, or agent workflow** on XRPL. This is product altitude: it designs software that other people or agents will use. It is not the right flow for a one-off transaction the user's own wallet will sign today.

## Route P altitude test

Before choosing a transaction builder, ask:

- **Operation altitude:** if the deliverable is signed by the user's wallet today, route to the relevant operation flow (`issuer-first-mint-flow`, `token-launch-flow`, `agentic-payment-flow`, `multisig-safety-flow`, etc.).
- **Product altitude:** if the deliverable is software other people or agents will use, stay here first. Product flows compose knowledge reads, live checks, operation flows, and coding-agent handoffs.

Ambiguous examples:

| User says | Route |
|---|---|
| "Launch my token on testnet" | Operation: `issuer-first-mint-flow.md` or `token-launch-flow.md` |
| "Build a token launch platform" | Product: this flow → `token-launch-product-flow.md` when written |
| "Send 10 XRP" | Operation: payment flow/builders |
| "Build a checkout app" | Product: this flow → `payment-app-product-flow.md` when written |

If the phrase is ambiguous, ask one altitude question before doing anything else: **"Are we building a one-time XRPL operation for your wallet to sign, or software other users/agents will use?"**

## Intake: ask at most five questions

Only ask questions whose answers change the archetype, architecture, or primitive map.

1. **Who uses it?** You, your community, merchants, token creators, treasury signers, other builders, autonomous agents?
2. **Custody model?** Users sign with their own wallets (default), you operate your own policy-gated signer for your own funds, or you want to hold users' funds?
3. **Value moved?** XRP, RLUSD, your IOU, NFTs, MPTs, none/read-only?
4. **Stack/runtime?** TypeScript web app, Python service, bot platform, MCP client, local/self-hosted server, VPS/Evernode?
5. **Network + horizon?** Testnet demo this week, mainnet later, production now, solo/team?

If the user has already supplied the answer, do not ask again. State assumptions and move.

## Custody decision tree

- **Users sign with their own wallets** → preferred. Design wallet handoff: decoded unsigned JSON preview → Xaman/Joey/Privy/manual signing → `tx-info` confirmation.
- **User's own policy-gated signer for their own funds** → allowed outside the skill. Require scoped transaction types, amount caps, allowlists, dry-run/preview, logs, monitoring, and circuit breaker. The skill still emits unsigned JSON only.
- **Hold users' funds, seeds, or private keys** → stop and warn. Do not design custody workarounds. Redesign as wallet-handoff or tell the user this is regulated/legal/security territory outside XRPL-Hermes.

Never ask for, store, print, or route around private keys. Product Builder Mode plans software; it does not host, sign, custody, or submit on behalf of users.

## Standard 5-box XRPL product architecture

Every Product Builder answer instantiates these boxes with concrete components:

1. **UI/client** — web app, bot, dashboard, CLI, or agent surface. Shows decoded transaction previews before wallet handoff.
2. **App backend** — product state, user/session records, receipts, rate limits, queues, and API routes. Does not hold user keys.
3. **XRPL read layer** — public Clio for light usage, private Clio/rippled for production/heavy reads, WebSocket subscriptions for settlement/alerts.
4. **Signing layer** — wallet handoff by default; optional user-owned policy-gated signer only for the user's own funds. Builders output unsigned signer-ready JSON.
5. **Monitor/attribution layer** — `SourceTag`, `DestinationTag`, hex JSON `Memos`, `subscribe`, `tx-info`, receipts, alerting, and incident response.

A good plan names which box owns every feature. If a feature cannot be placed cleanly, the product design is not ready.

## Artifact the agent should produce

After intake, produce:

1. **Product one-pager** — user, problem, wedge, custody model, value moved, explicit non-goals.
2. **5-box architecture** — concrete components, data flow, and wallet/signing boundary.
3. **XRPL primitive map** — feature → XRPL primitive/query → exact `xrpl_run`/CLI command → operation flow that owns safety checkpoints.
4. **MVP plan** — read-only first, build-only second, wallet handoff third, mainnet last.
5. **Testnet demo checklist** — how the user proves the MVP works without risking funds.
6. **Mainnet-safe launch checklist** — what must be live before value flows.
7. **Coding-agent handoff** — a concise implementation brief for Claude Code/Cursor/Codex plus verification commands XRPL-Hermes will run afterward.

## Base testnet demo checklist

- Use testnet/devnet accounts; never real funds for the first proof.
- Run `server-info` for current fees/reserves before quoting environment facts.
- Every emitted transaction is unsigned signer-ready JSON.
- UI shows decoded full transfer/asset/account/tag/memo before signing.
- Wallet signs externally; product never sees a seed.
- Confirm every demo transaction with `tx-info` and require `validated: true`.
- Log failed results and route diagnosis through `skills/failed-transaction-diagnosis-flow.md`.
- No fake live data: missing liquidity/holders/prices/status are labeled unavailable with the failed command/source named.

## Base mainnet-safe launch checklist

- Custody model written down; no user-key handling.
- Monitoring is live before value flows: WebSocket or polling, `tx-info` confirmation, alert routing.
- Initial caps are set: amount limits, rate limits, allowlists, disabled risky features.
- DestinationTag/SourceTag/Memos are handled and displayed correctly.
- Operation-level confirm-before-build still governs every value-transfer or irreversible transaction.
- Incident path exists: pause/circuit breaker, regular-key rotation path, alert owner, rollback plan.
- Legal/compliance boundary is explicit for RWA, KYC, securities-like, money-transmission, or custodial surfaces.

## Archetype dispatch table

| Product intent sounds like | Playbook | Status | First wedge deliverable |
|---|---|---|---|
| "I want to build something on XRPL" | `skills/build-xrpl-product-flow.md` | live | Intake → one-pager → primitive map → MVP/testnet plan |
| Wallet login, signing handoff, Xaman integration | `skills/wallet-signing-ux-product-flow.md` | planned | Reusable sign-in + decoded unsigned JSON handoff component |
| Checkout, invoice, tipping, payment links, remittance | `skills/payment-app-product-flow.md` | planned | Non-custodial payment request → wallet handoff → ledger receipt |
| Paid API, x402, agent-to-agent payments, monetize MCP | `skills/agentic-payments-product-flow.md` | planned | 402 challenge + verified XRPL payment middleware |
| Token safety dashboard, holder dashboard, rug checker, analytics bot | `skills/token-intelligence-product-flow.md` | planned | Read-only token report API with confidence + missing-data list |
| Launchpad, creator token wizard, token creator tool | `skills/token-launch-product-flow.md` | planned | Non-custodial issuer wizard driven by live ledger state |
| DAO/project treasury, signer coordination, proposal flow | `skills/treasury-tool-product-flow.md` | planned | Read-only treasury cockpit + unsigned proposal workflow |
| NFT mint site, holder-gated community, small marketplace | `skills/nft-community-product-flow.md` | planned | Mint/offer/holder-verification loop with wallet proof |
| Swap UI, LP dashboard, DEX/AMM analytics | `skills/amm-dex-product-flow.md` | planned | Read-only pool/orderbook explorer + timestamped quote view |
| Xahau Hook app, on-ledger automation product | `skills/xahau-hook-app-product-flow.md` | planned | Hook use-case plan + HookOn calculation + install verification |
| RWA/compliance-gated issuance platform | `skills/rwa-compliance-product-flow.md` | planned | Technical rails plan with RequireAuth/credentials/clawback boundary |
| Self-hosted XRPL agent stack, MCP-powered agent service | `skills/xrpl-agent-stack-product-flow.md` | planned | MCP smoke + read-only agent job + human-signed builder loop |

## Coding-agent handoff template

When the user wants implementation, hand a coding agent this shape:

```md
# XRPL Product Implementation Brief

Product: <name>
User + wedge: <who / first useful job>
Custody model: <wallet handoff default | user-owned policy signer for own funds>
Network: <testnet/devnet/mainnet later>

## 5-box architecture
- UI/client:
- app backend:
- XRPL read layer:
- signing layer:
- monitor/attribution:

## Primitive map
| Feature | XRPL primitive/query | Command/tool | Operation flow |
|---|---|---|---|

## MVP tasks
1. Read-only proof first.
2. Unsigned builder output second.
3. Wallet handoff third.
4. Testnet validation and receipts.

## Must-pass checks
- no seeds/private keys in code/logs
- builders emit unsigned JSON only
- decoded preview before signing
- `tx-info` validated confirmation after signing
- no fake live data; cache timestamps visible
```

## Anti-goals

- Do not design hosted custody, seed collection, or private-key storage.
- Do not imply XRPL-Hermes runs the product, hosts it, signs for users, or provides legal compliance.
- Do not promise market outcomes, token appreciation, guaranteed holders, or guaranteed liquidity.
- Do not answer product asks with a single transaction JSON unless the user confirms they actually wanted operation altitude.
- Do not duplicate flag tables or irreversible checkpoint details from operation flows; link them.

## Verification behavior after code is built

Do not trust coding-agent self-reports. Verify artifacts by reading files, running tests, decoding generated JSON, checking live ledger status with `server-info`/`tx-info`/`account`/`token-intel` as appropriate, and confirming no secrets are present before telling the user it is done.
