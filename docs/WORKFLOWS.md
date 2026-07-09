# Ecosystem Workflow Index

One page mapping every ecosystem xrpl-hermes covers to its live commands, knowledge files, reference cards, and runnable examples — with an honest label for how deep the tooling goes.

**Coverage labels** (used in every section):

- **Live commands** — CLI/MCP commands that query live networks or build signer-ready JSON today, verified in [`AUDIT-tool-matrix.md`](../AUDIT-tool-matrix.md).
- **Build-only** — builders emit valid JSON, but the feature is amendment-gated or network-specific; the tool tells you when mainnet doesn't accept it yet.
- **Knowledge + references** — documented workflows and integration patterns; you execute them with the ecosystem's own tooling, not an xrpl-hermes command.

---

## XRPL L1 — accounts, payments, trust lines, DEX

**Coverage: Live commands.**

- Query: `account`/`balance`, `account_objects`, `account-tx`, `trustlines`, `ledger`, `ledger-entry`, `server-info`, `tx-info`, `decode`, `validate-address`, `subscribe`
- Build: `build-payment`, `build-trustset`, `build-offer`, `build-cross-currency-payment`, `build-account-set`, `build-account-delete`, `build-set-regular-key`, `build-deposit-preauth`
- DEX read side: `book-offers`, `path-find`
- Advanced ops: `build-signer-list-set` (multisig), `build-ticket-create`, `build-escrow-*`, `build-check-*`, `build-paychannel-*`, `build-batch` (XLS-56, warns until enabled on mainnet), `build-set-oracle` (XLS-47), `build-credential-*` (XLS-70)
- Submit path for advanced users with externally signed blobs: `submit`, `submit-multisigned`
- Knowledge: `01`–`04`, `09`–`15`, `52-xrpl-l1-reference.md`, `60-xrpl-account-set.md`, `61-xrpl-websocket-streams.md` · Card: `references/xrpl-l1.md`
- Workflow playbooks: `skills/treasury-monitor-flow.md`, `skills/multisig-safety-flow.md`, `skills/account-access-safety-flow.md`, `skills/failed-transaction-diagnosis-flow.md` · Examples: `example-build-payment.py`, `example-setup-trustline.py`, `example-create-offer.py`, `example-cross-currency.py`, `example-multisig.py`

## Issued tokens (IOUs)

**Coverage: Live commands.**

- Issuer setup: `build-account-set` (DefaultRipple, domain, transfer rate, tick size), `build-trustset`, `build-payment` (mint/distribute), `build-clawback`
- Research: `token-intel` (one-shot live report: issuer flags/domain, trustline sample, DEX book, AMM, risk flags), plus `account`, `trustlines`, `book-offers`, `account-tx` for deeper digging
- Knowledge: `21-xrpl-token-model.md`, `22-xrpl-token-issuance.md`, `07-xrpl-clawback.md`, `38-xrpl-minting-ops.md`, `58-rlusd-operations.md`, `59-rwa-tokenization.md` · Card: `references/rlusd.md`
- Workflow playbooks: `skills/issuer-first-mint-flow.md` (minimal path), `skills/token-launch-flow.md` (full launch), `skills/clawback-flow.md` · Examples: `example-clawback.py`, `example-token-safety-check.py` (read-only pass/fail verdict over `token-intel`, exit-code friendly for scripts and CI)
- **Token intelligence reports:** `token-intel CURRENCY rISSUER` implements the research workflow (≥5 live datapoints, confidence score, mandatory missing-data list, source labels) specified in `knowledge/64-token-intelligence-reports.md` with the quick card at `references/token-intelligence.md`.

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

**Coverage: Live command + knowledge.**

- `xaman-payload` pushes signer-ready JSON to the Xaman Platform API and returns the sign URL + QR (requires free `XUMM_API_KEY`/`XUMM_API_SECRET`; without keys it fails safely with instructions)
- No keys needed at all for the manual path: every builder's JSON pastes directly into Xaman's Developer console for signing
- Knowledge: `26-xrpl-xaman-deeplink.md`, `63-xrpl-xaman-platform.md`, `53-xrpl-wallets-auth.md` · Card: `references/xrpl-wallets-auth.md`

## Xahau / Hooks

**Coverage: partial — live HookOn calculator, one live query, deep references.**

- `hooks-info` — live query of installed hooks on a Xahau account
- `hooks-bitmask Payment OfferCreate …` — calculates the 256-bit Xahau `HookOn` transaction-type bitmap with active-low semantics (except SetHook). It outputs the hex value and the transaction types it will trigger on.
- Knowledge: `32-xrpl-hooks-dev.md`, `43-xrpl-hooks-advanced.md`, `51-xrpl-xahau-hooks.md` (Hooks v3, URITokens, B2M), `54-xrpl-evernode-hosting.md` · Card: `references/xahau-hooks.md`
- Workflow playbook: `skills/xahau-hook-setup-flow.md` (what the toolkit can/cannot do, HookOn calculation, manual SetHook template)

## Flare — price context

**Coverage: Live commands, clearly labeled sources.**

- `flare-ftso XRP/USD BTC/USD …` — live read-only FTSOv2 `eth_call` reads from the Flare C-chain, resolving the contract through the FlareContractRegistry.
- `flare-price XRP FLR …` — current prices from a public fallback API, labeled as **not direct on-chain FTSOv2 proof**.
- Knowledge: `49-xrpl-flare-ftso.md` · Card: `references/flare-ftso.md`

## Axelar — bridging XRPL ↔ EVM and beyond

**Coverage: Live read-only status + knowledge + references.** Bridging executes through Axelar's own contracts/UI, while xrpl-hermes can inspect route registration and transfer status.

- `bridge-status [xrpl xrpl-evm]` — reads Axelar/XRPL chain registration and gateway context from Axelarscan; does not move funds.
- `bridge-tx TXHASH` — looks up an Axelar GMP transfer by source-chain transaction hash.
- Knowledge: `46-xrpl-axelar-bridge.md`, `55-xrpl-sidechain-interop.md`, `35-xrpl-full-interop.md` · Card: `references/axelar-bridge.md`
- Always verify current gateway/contract addresses from official Axelar/XRPL EVM docs before moving funds — addresses are deliberately not hardcoded here.

## Arweave — permanent storage for token/NFT metadata

**Coverage: Live cost estimate + knowledge + references.** The workflow (upload metadata/images, reference `ar://` URIs from NFT mints and issuer TOMLs) still runs with Arweave tooling per the docs.

- `arweave-cost 1MB` — estimates permanent storage cost from the public Arweave gateway. It never uploads data or handles wallet keys.
- Knowledge: `47-xrpl-arweave-storage.md` · Card: `references/arweave-storage.md`
- Pairs with: `build-nft-mint --uri <hex of ar://...>`

## XRPL EVM Sidechain

**Coverage: Live commands + knowledge.**

- `evm-balance 0xADDR [mainnet|testnet]` — live balance via `rpc.xrplevm.org` (chain ID 1440000) / testnet (1449000)
- `evm-contract` — raw deployment transaction JSON for external signing (e.g. MetaMask)
- `evm-bridge` — live chain status (latest block, observed chain ID)
- Knowledge: `29-xrpl-metamask-evm.md`, `33-xrpl-evm-dev.md`, `44-xrpl-evm-advanced.md`, `50-xrpl-evm-sidechain.md` · Card: `references/xrpl-evm-sidechain.md`
- Example: `example-evm-swap.py`

## Bots and monitoring (Telegram / Discord)

**Coverage: Knowledge + runnable examples.**

- Knowledge: `40-xrpl-monitoring.md`, `41-xrpl-bots-patterns.md` (secret-sourcing rules, signer-handoff over hot wallets), `56-telegram-xrpl-bots.md`, `57-discord-xrpl-bots.md`
- Examples: `example-telegram-bot.py`, `example-discord-bot.py` · Stream feed: `subscribe`

## Infrastructure — your own node

**Coverage: Deploy configs + knowledge.**

- `deploy/` — docker-compose for rippled + Clio, with configs; point the toolkit at it via `XRPL_PRIVATE_RPC`
- Knowledge: `16-xrpl-clio.md`, `17-xrpl-private-node.md`, `18-xrpl-rate-limits.md`, `24-xrpl-deploy-guide.md`

---

## Roadmap / future work

Honest gaps, in rough priority order:

1. **Bridge workflow depth** — add richer, typed Axelar route/fee guidance while staying read-only by default.
2. **Arweave workflow depth** — add optional signed upload handoff patterns without introducing hidden paid uploads or wallet-key handling.
3. **Flare FTSOv2 hardening** — expand feed coverage and official-source regression tests for feed IDs/contracts.

Shipped from earlier roadmaps: AMM pool state is now the first-class `amm-info` command, the token-intelligence research workflow is the first-class `token-intel` command (both v1.5.1), and v1.5.2 added read-only Axelar status, Arweave cost estimates, Flare FTSOv2 reads, and a real Xahau HookOn calculator.
