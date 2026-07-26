# Ecosystem Workflow Index

One page mapping every ecosystem xrpl-hermes covers to its live commands, knowledge files, reference cards, and runnable examples — with an honest label for how deep the tooling goes.

**Coverage labels** (used in every section):

- **Live commands** — CLI/MCP commands that query live networks or build signer-ready JSON today, verified in [`AUDIT-tool-matrix.md`](../AUDIT-tool-matrix.md).
- **Build-only** — builders emit valid JSON, but the feature is amendment-gated or network-specific; the tool tells you when mainnet doesn't accept it yet.
- **Knowledge + references** — documented workflows and integration patterns; you execute them with the ecosystem's own tooling, not an xrpl-hermes command.

---

## Product Builder Mode — idea → architecture → MVP

**Coverage: Knowledge + references + live verification.** Product Builder Mode is the product-altitude layer: use it when the user wants an app, platform, dashboard, API, service, marketplace, launchpad, or agent workflow that other people/agents will use. It does not add CLI commands or custody; it routes builders through intake, architecture, primitive mapping, operation flows, and live verification.

- Canonical umbrella: `skills/build-xrpl-product-flow.md`
- Human hub: `docs/PRODUCT-BUILDER.md`
- Product altitude test: if the deliverable is signed by the user's wallet today, use an operation flow; if it is software other people or agents will use, use Product Builder Mode first.
- Product playbooks include wallet-signing UX, payments, agentic payments/x402, token intelligence, token launch, treasury, NFTs, AMM/DEX, RWA, and self-hosted agents. Xahau Hook apps are partial/planning until external compilation and deployment are independently certified.
- Live checks used during planning as needed: `server-info`, `account`, `tx-info`, `token-intel`, `amm-info`, `book-offers`, `path-find`, `amendment`.

---

## XRPL L1 — accounts, payments, trust lines, DEX

**Coverage: Live commands.**

- Query: `account`/`balance`, `account_objects`, `account-tx`, `trustlines`, `ledger`, `ledger-entry`, `server-info`, `tx-info`, `decode`, `validate-address`, `subscribe`
- Build: `build-payment`, `build-trustset`, `build-offer`, `build-cross-currency-payment`, `build-account-set`, `build-account-delete`, `build-set-regular-key`, `build-deposit-preauth`
- DEX read side: `book-offers`, `path-find`
- Advanced ops: `build-signer-list-set` (multisig), `build-ticket-create`, `build-escrow-*`, `build-check-*`, `build-paychannel-*`, `build-set-oracle` (XLS-47), `build-credential-*` (XLS-70). `build-batch` is retired and unregistered.
- Broadcast is outside supported agent workflows; legacy local `submit*` commands remain MCP-denied quarantine surfaces.
- Knowledge: `01`–`04`, `09`–`15`, `52-xrpl-l1-reference.md`, `60-xrpl-account-set.md`, `61-xrpl-websocket-streams.md` · Card: `references/xrpl-l1.md`
- Workflow playbooks: `skills/treasury-monitor-flow.md`, `skills/multisig-safety-flow.md`, `skills/account-access-safety-flow.md`, `skills/failed-transaction-diagnosis-flow.md` · Examples: `example-build-payment.py`, `example-setup-trustline.py`, `example-create-offer.py`, `example-cross-currency.py`, `example-multisig.py`

## Issued tokens (IOUs)

**Coverage: Live commands.**

- Issuer setup: `build-account-set` (DefaultRipple, domain, transfer rate, tick size), `build-trustset`, `build-payment` (mint/distribute), `build-clawback`
- Research: `token-intel` (one-shot live report: issuer flags/domain, trustline sample, DEX book, AMM, risk flags), plus `account`, `trustlines`, `book-offers`, `account-tx` for deeper digging
- Knowledge: `21-xrpl-token-model.md`, `22-xrpl-token-issuance.md`, `07-xrpl-clawback.md`, `38-xrpl-minting-ops.md`, `58-rlusd-operations.md`, `59-rwa-tokenization.md` · Card: `references/rlusd.md`
- Workflow playbooks: `skills/issuer-first-mint-flow.md` (minimal path), `skills/token-launch-flow.md` (full launch), `skills/clawback-flow.md` · Examples: `example-clawback.py`, `example-token-safety-check.py` (read-only pass/fail verdict over `token-intel`, exit-code friendly for scripts and CI)
- **Token intelligence reports:** `token-intel CURRENCY rISSUER` is a five-query ledger snapshot with confidence capped at Medium, explicit scope/source labels, a mandatory missing-data list and no recommendation. See `knowledge/64-token-intelligence-reports.md` and `references/token-intelligence.md`.

## NFTs (XLS-20)

**Coverage: Live commands.**

- Query: `nft-info`, `nft-offers`
- Build: `build-nft-mint`, `build-nft-create-offer`, `build-nft-accept-offer`, `build-nft-cancel-offer`, `build-nft-burn`
- Knowledge: `06-xrpl-nfts.md`, `23-xrpl-nft-minting.md`, `39-xrpl-nft-ops.md`, `62-xrpl-nft-marketplace.md`
- Workflow playbook: `skills/nft-operations-flow.md` · Examples: `example-mint-nft.py`, `example-nft-buy.py`

## AMMs

**Coverage: Live commands.**

- Build: `build-amm-create`, `build-amm-deposit`, `build-amm-withdraw`, `build-amm-vote`, `build-amm-bid`
- Pool/market reads: `amm-info` (live pool state: reserves, trading fee, auction slot), `book-offers`, `path-find` (AMM liquidity participates in pathfinding)
- Knowledge: `05-xrpl-amm.md`, `34-xrpl-amm-bots.md`
- Workflow playbook: `skills/amm-bot-flow.md` (paper-mode-first, 9-stage go-live checklist) · Example: `example-amm-deposit.py`

## MPTs (XLS-33 Multi-Purpose Tokens)

**Coverage: Live commands** (MPTokensV1 is enabled on mainnet; the builders verify live status on each run).

- Build: `build-mpt-issuance-create`, `build-mpt-authorize`
- Knowledge: `08-xrpl-mpts.md` · Amendment check: `amendment MPTokensV1`

## Amendments

**Coverage: Live commands.**

- `amendments` (full table with enabled/supported/vetoed counts), `amendment NAME`, `amendment-status NAME`
- Knowledge: `37-xrpl-amendments.md` · Card: `references/amendments.md` (date-stamped snapshot — the live command is the source of truth)

## Xaman (XUMM) workflows

**Coverage: Guarded external API side effect + boundary documentation.**

- `xaman-payload` validates an unsigned XRPL L1 Payment before creating a real Platform payload; all other transaction types are currently rejected (requires `XUMM_API_KEY`/`XUMM_API_SECRET`; denied over MCP).
- Payload creation is an external side effect, not transaction success. Verify the wallet-selected network and final validated XRPL transaction independently.
- Knowledge: `26-xrpl-xaman-deeplink.md`, `63-xrpl-xaman-platform.md`, `53-xrpl-wallets-auth.md` · Card: `references/xrpl-wallets-auth.md`

## Xahau / Hooks

**Coverage: partial/certified boundary — HookOn calculation and validated Mainnet/Testnet Hook-chain inspection. No compile/build/sign/deploy.**

- `hooks-info rADDR [mainnet|testnet]` — validated installed-chain query with endpoint/network/ledger provenance and explicit RPC errors
- `hooks-bitmask Payment OfferCreate …` — calculates the legacy 256-bit active-low bitmap (special active-high SetHook bit) as 64 hex characters without `0x`
- Knowledge: `32-xrpl-hooks-dev.md`, `43-xrpl-hooks-advanced.md`, `51-xrpl-xahau-hooks.md` · pinned card: `references/xahau-hooks.md`
- Workflow: `skills/xahau-hook-setup-flow.md` — external compiler/Xahau serializer/wallet handoff, Testnet evidence, rollback, and Mainnet approval gate

## Flare — price context

**Coverage: Live commands, clearly labeled sources.**

- `flare-ftso XRP/USD BTC/USD …` — live read-only FTSOv2 `eth_call` reads from the Flare C-chain, resolving the contract through the FlareContractRegistry.
- `flare-price XRP FLR …` — current prices from a public fallback API, labeled as **not direct on-chain FTSOv2 proof**.
- Knowledge: `49-xrpl-flare-ftso.md` · Card: `references/flare-ftso.md`

## Axelar — registration and GMP-index inspection

**Coverage: Narrow read-only registration lookup + partial GMP-index search. No transfer certification.**

- `bridge-status [xrpl xrpl-evm]` — reads Axelarscan registration metadata; it does not establish route/assets/fees/liquidity.
- `bridge-tx TXHASH` — searches the GMP index; it is not a general ITS token-transfer receipt checker.
- Knowledge: `46-xrpl-axelar-bridge.md`, `55-xrpl-sidechain-interop.md`, `35-xrpl-full-interop.md` · Card: `references/axelar-bridge.md`
- Always verify current gateway/contract addresses from official Axelar/XRPL EVM docs before moving funds — addresses are deliberately not hardcoded here.

## Arweave — base-network storage cost

**Coverage: Narrow point-in-time base fee estimate. Upload and retrieval workflows are quarantined.**

- `arweave-cost 1MB` — estimates the base-network fee from a public gateway. It never uploads, touches keys, or guarantees retrieval.
- Knowledge: `47-xrpl-arweave-storage.md` · Card: `references/arweave-storage.md`
- Pairs with: `build-nft-mint --uri 'ar://...'` for text (encoded once by the builder),
  or `--uri-hex HEX` only when the input is already encoded. Never pass pre-encoded hex to
  `--uri`; NFT URIs are immutable and that would encode the hex characters a second time.

## XRPL EVM Sidechain

**Coverage: Experimental balance/network reads + build-only deployment intent. No transfer certification.**

- `evm-balance 0xADDR [mainnet|testnet]` — live balance via `rpc.xrplevm.org` (chain ID 1440000) / testnet (1449000)
- `evm-contract` — explicitly experimental unsigned intent; no compile/simulation/gas/deployment proof
- `evm-bridge` — RPC identity/latest block only and reports `BridgeCertified: false`
- Knowledge: `29-xrpl-metamask-evm.md`, `33-xrpl-evm-dev.md`, `44-xrpl-evm-advanced.md`, `50-xrpl-evm-sidechain.md` · Card: `references/xrpl-evm-sidechain.md`
- The former swap/bridge examples are not certification evidence and must not be used as production instructions.

## Bots and monitoring (Telegram / Discord)

**Coverage: Knowledge + signer-separated examples.**

- Knowledge: `40-xrpl-monitoring.md`, `41-xrpl-bots-patterns.md`, `56-telegram-xrpl-bots.md`, `57-discord-xrpl-bots.md`
- Examples: `example-telegram-bot.py`, `example-discord-bot.py` · Stream feed: `subscribe`

## Infrastructure — your own node

**Coverage: External dependency boundary + knowledge.**

- `deploy/` contains only the retirement notice for the former unverified node stack.
- Knowledge: `16-xrpl-clio.md`, `17-xrpl-private-node.md`, `18-xrpl-rate-limits.md`, `24-xrpl-deploy-guide.md`. Current first-party rippled/Clio operations documentation is the authority; `XRPL_PRIVATE_RPC` can target infrastructure the user independently operates.

---

## Roadmap / future work

Honest gaps, in rough priority order:

1. **Bridge proof** — current first-party schema fixtures plus Testnet round-trip and recovery evidence before restoring transfer guidance.
2. **Arweave upload proof** — current SDK, user-controlled signer, fee separation, confirmed upload and multi-gateway retrieval before restoring upload guidance.
3. **Flare FTSOv2 hardening** — expand feed coverage and official-source regression tests for feed IDs/contracts.

Shipped from earlier roadmaps: AMM pool state is now the first-class `amm-info` command, the token-intelligence research workflow is the first-class `token-intel` command (both v1.5.1), and v1.5.2 added read-only Axelar status, Arweave cost estimates, Flare FTSOv2 reads, and a real Xahau HookOn calculator.
