# Changelog

## v1.6.2 — Agent / skill receipts: safe, signer-separated on-chain provenance — Opus 4.8 Max Audited (2026-06-16)

Adds a focused, safe way to record **what an agent did, or how a skill improved (v1 → v2), as an
on-chain receipt** — an unsigned `NFTokenMint` the user's wallet signs. It is the signer-separated
shape of the popular "an agent mints its own NFT to prove it learned" demo: the provenance (timestamp,
author, tamper-evidence, public verifiability) is kept; the unsafe part — a seed inside the agent that
signs and submits on its own — is removed. No new command and no architecture change: it composes the
existing `build-nft-mint` primitive.

### Added
- `skills/agent-receipt-flow.md` — the signer-separated receipt playbook: summarize a run / skill
  evolution as a compact ≤256-byte URI (or a pointer to an off-ledger record) → build an **unsigned**
  `NFTokenMint` (CLI or JS) → human preview + approval → wallet signs → `nft-info` reads it back.
  Explicit: no autonomous minting; keys stay with the user.
- `examples/js/agent-receipt-nft.js` — runnable, build-only `xrpl.js` receipt builder. Encodes a
  compact receipt as a base64 `data:` URI, enforces the 256-byte URI limit **after** base64+hex
  encoding (where the limit actually bites), and prints the unsigned `NFTokenMint`. Never reads a
  seed, signs, submits, or connects to a node — the safe twin of a seed-signing minter.
- `tests/test_agent_receipt.py` — node-free coverage of the receipt primitive: `build-nft-mint`
  hex-encodes a text URI, passes through already-hex, round-trips a compact `data:` receipt through
  on-ledger hex, emits the unsigned `SigningPubKey:""` marker, and refuses an over-256-byte URI.

### Changed
- Discoverability wiring only: an **"Agent / skill receipts"** row in the README "build anything"
  map (label: CLI + pattern), a row in `examples/js/README.md`, a "Key Knowledge Files" row, and a
  one-line note in SKILL.md Core Mission 5. No command behavior changed; the dispatcher still exposes
  73 commands and the CLI/MCP server stay Python (`xrpl-py`).

### Verified
- Pytest 51 passed (46 + 5 new receipt tests); `dev_test_matrix.py` 73/73 PASS (no command change);
  `audit_project_quality.py` all PASS (no-seeds incl. the new `.js`, neutral-language, command-count,
  version-sync 1.6.2, currency-literals).
- JS: `node --check examples/js/agent-receipt-nft.js` passes; `node agent-receipt-nft.js` prints an
  unsigned `NFTokenMint` (URI 370/512 hex). Its URI hex is byte-identical to the Python
  `build-nft-mint --uri <data:…>` output and round-trips back to the original receipt JSON.
- MCP stdio smoke: initialize reports 1.6.2.

## v1.6.1 — Dual-stack (Python + xrpl.js) developer experience, "build anything" map, rippled 3.2.0 freshness — Opus 4.8 Ultra Audited (2026-06-16)

Makes XRPL-Hermes read as a "build anything on XRPL with AI agents" kit for both Python and
TypeScript/JavaScript developers, adds a reusable self-update playbook, and refreshes currentness for
the rippled 3.2.0 release. No command behavior changes — the CLI and MCP server stay Python (`xrpl-py`).

### Added
- `examples/js/` — runnable, build-only `xrpl.js` twins of the Python payment examples:
  `build-xrp-payment.js` (unsigned XRP `Payment` with `SourceTag`/`DestinationTag`/hex `Memo`) and
  `build-rlusd-payment.js` (unsigned RLUSD issued-currency `Payment` using the 160-bit currency code).
  Neither signs, submits, nor touches a seed; both leave Fee/Sequence/LLS for the wallet layer's
  autofill. Includes `package.json` (pins `xrpl@^5`) and a README mapping xrpl-py ↔ xrpl.js calls.
- `skills/freshness-update-flow.md` — the reusable "update XRPL-Hermes" playbook (audit report first →
  edit → verify → version-bump → ship), wired into SKILL.md and `knowledge/65`. It enumerates the
  sources to check: rippled releases, live amendments, `npm view xrpl version`, xrpl-py on PyPI, x402/t54.
- README **"Choose your stack"** table (Python/`xrpl-py` vs TS-JS/`xrpl.js`, both first-class for the
  user's app code) and a labeled **"Build anything on XRPL with AI agents"** builder map with honest
  status labels (CLI / live tool / ref / pattern / roadmap) across tokens, NFTs, AMM/DEX, payments,
  RLUSD, x402, bots, wallets, MPTs, treasury, EVM, Xahau, Flare, Axelar, Arweave, and token intelligence.

### Changed
- QUICKSTART, `docs/DEVELOPERS.md`, and SKILL.md now make the Python-engine / dual-stack-app boundary
  explicit and point at `examples/js/`; SKILL.md frontmatter notes dual-stack. `.js` added to the
  project-quality audit's scanned suffixes so the new JS lane gets seed coverage.
- Freshness refresh for **rippled 3.2.0** (released 2026-06-15): dated, URL-anchored notes in
  `knowledge/37-xrpl-amendments.md`, `references/amendments.md`, `deploy/README.md`, and the QUICKSTART
  `server-info` example. Notes record the rotated GPG signing key and the binary rename to `xrpld`, and
  anchor the load-bearing point on a live check: mainnet still reported `BuildVersion 3.1.3` and
  3.2.0-line amendments (e.g. `fixCleanup3_2_0`) are not yet on the mainnet `feature` table.

### Verified
- Pytest 46 passed; `dev_test_matrix.py` 73/73 PASS (matrix regenerated); `audit_project_quality.py`
  all checks PASS (no-seeds, neutral-language, command-count, version-sync 1.6.1, currency-literals).
- JS: `node --check` passes on both files; `npm install` + `node build-xrp-payment.js` /
  `build-rlusd-payment.js` produce the expected unsigned JSON (memo hex byte-identical to the Python
  `build-payment` output; RLUSD code `524C555344…0000`).
- Live (2026-06-16): `server-info` → `BuildVersion 3.1.3`; `amendment fixCleanup3_2_0` → `UnknownAmendment`.
- MCP stdio smoke: initialize → tools/list (4 tools) → `xrpl_run validate-address` green.

## v1.6.0 — First-class agentic payments (XRP + RLUSD), x402, signer-separated docs — FABLE 5 Audited (2026-06-16)

Brings XRPL-native agentic payments up to date with the June 2026 official XRPL agent skills and audits the package for accuracy.

### Added
- `references/agentic-payments.md` — the signer-separated two-layer model (payment builder vs wallet/signing layer), dual-stack guidance (xrpl-py + xrpl.js for the *user's* code), a primitive coverage map cross-linking existing knowledge files, the strict 8-rule safety set, and a testnet-first Hermes implementation roadmap for the three official equivalents (payment-builder = mostly shipped; wallet-signing-layer = documented design only, no custody; x402 = plan).
- `references/x402-payments.md` — HTTP-402 machine-to-machine payment flow, the t54 facilitator, `x402_xrpl` (Python) / `x402Fetch` (TS), network ids (`xrpl:1`/`xrpl:0`), pricing in drops, and safety — all framed "verify live before production."
- `skills/agentic-payment-flow.md` — tested flow backing the new 5th Core Mission.
- `build-payment` / `build-cross-currency-payment`: `--source-tag` (SourceTag), `--dest-tag` (DestinationTag), and a now-functional `--memo` (UTF-8 → hex MemoData). Tags are validated as UInt32; `--tag` stays a back-compat alias for `--dest-tag`. Builders still emit unsigned JSON only.
- Canonical "Source & Destination Tags" section in `knowledge/02-xrpl-payments.md`; testnet RLUSD issuer added to `references/rlusd.md`.

### Changed
- SKILL.md: agentic payments promoted from a passive "Freshness Note" to a first-class section + a 5th Core Mission; consolidated the 8 safety rules into a single source-of-truth block (SECURITY.md and the agentic reference now defer to it).

### Fixed
- `build-payment` previously accepted `--memo` but silently dropped it and had no SourceTag support; `--tag` raised a type error. All corrected with offline regression tests.
- `references/xrpl-l1.md`: corrected a non-existent `SetAccountRoot` transaction type to `AccountSet`.
- Documentation accuracy: softened STANDALONE.md's "complete reference for all 73" claim to defer to the SKILL.md table, corrected the stale `hooks-bitmask` "BROKEN" note, and fixed stale reference-card counts and an MCP command-count assertion in the docs.

## v1.5.3 — Regression gates and executable examples — FABLE 5 Audited (2026-06-11)

- Added offline regression tests for the v1.5.2 ecosystem tooling: Axelar bridge summaries, Arweave size/cost parsing, Flare FTSOv2 feed encoding/decoding, and Xahau HookOn active-low/active-high bitmask behavior.
- Added a pytest project-quality gate that runs the audit checks for no seeds, neutral language, command-count sanity, version sync, and long-currency-literal pitfalls.
- Added `examples/example-token-safety-check.py`, a read-only token-intel based CLI example with script-friendly exit codes and no seed requirement.
- Expanded MCP client starter prompts and quickstart/workflow docs around executable read-only examples.

## v1.5.2 — Bridge/oracle/storage utility pass — FABLE 5 Audited (2026-06-11)

- Added read-only `bridge-status` and `bridge-tx` commands for Axelar/XRPL route and transfer checks.
- Added read-only `arweave-cost` for permanent-storage fee estimates; it never uploads or touches keys.
- Added `flare-ftso` for live FTSOv2 on-chain price reads, while keeping `flare-price` labeled as a public fallback.
- Replaced the Xahau `hooks-bitmask` warning stub with a real HookOn bitmask calculator.
- Added `scripts/audit_project_quality.py` to scan for decodable seeds, hostile competitor wording, command-count drift, version drift, and unsafe long currency literals.

## v1.5.1 — First-class token intelligence and AMM lookup commands — FABLE 5 Audited (2026-06-10)

Pass 2: two new read-only commands turn the token-intelligence methodology (knowledge/64) into real tooling. 67 → 69 commands; both exposed automatically through the MCP server.

### Added
- `token-intel CURRENCY rISSUER [TX_LIMIT] [TRUSTLINE_LIMIT]` (`scripts/tools/token_intel.py`) — one-shot live token report: issuer account/flags/domain/transfer-rate, recent issuer transactions, trustline/holder sample, DEX order book vs XRP, and AMM pool state. Output: `input`, `normalized_currency`, `sources`, `datapoints`, `risk_flags`, `confidence` (high only with ≥5 live datapoints), `missing_data` (failures listed, never invented), `plain_english_summary`.
- `amm-info ASSET1 ASSET2` (`scripts/tools/amm.py`) — live AMM pool lookup (reserves, trading fee, LP token, vote slots, auction slot) using the repo's `XRP` / `CUR:rISSUER` asset syntax; reports `AMMExists: false` honestly when no pool exists.
- `normalize_currency_code()` and `parse_asset_normalized()` in `scripts/tools/_shared.py` — 4-20 char ASCII symbols (e.g. `RLUSD`) normalize to their 160-bit hex form; 3-char and 40-hex codes pass through.
- `tests/test_token_intel.py` — 10 offline tests: normalization edge cases, AMM asset parsing, token-intel report shape with canned responses, honest all-failures path, command registration (69), CLI usage errors. MCP test now asserts `token-intel` and `amm-info` are exposed.
- Dev-test matrix entries for both commands; SKILL.md routing, STANDALONE/QUICKSTART/WORKFLOWS/MCP-CLIENTS docs updated.

### Verified
- Pytest 21 passed; dev-test matrix regenerated 69/69 PASS (committed); MCP stdio smoke test green.
- Live (2026-06-10): `token-intel RLUSD rMxCKbEDwqr76QuheSUMdEGf4B9xJ8m5De` → 5/5 datapoints, confidence high, RLUSD normalized to `524C555344…0000`; `amm-info XRP RLUSD:rMxCK…` and `amm-info XRP USD:rvYAf…` returned live pools.

## v1.5.0 — Professional docs release: onboarding, MCP clients, workflow index — FABLE 5 Audited (2026-06-10)

Documentation release closing the gaps between a working toolkit and a serious open-source release. No tool behavior changes except one stale-string fix.

### Added
- `docs/BEGINNERS.md` — "new to XRPL and agent CLIs" guide: the five concepts that matter (reserves, drops, trust lines, signing split, amendments), the no-seeds-in-prompts rule up front, a zero-risk read-only first session, testnet practice path, and a glossary.
- `docs/DEVELOPERS.md` — advanced guide: repo architecture (thin dispatcher + `scripts/tools/` module registry + `_shared.py` failover), safety invariants, add-a-command checklist, MCP server internals (stdio JSON-RPC, subprocess isolation, command allowlist, knowledge sandbox), two-layer testing model with the dev-test matrix pass criteria documented, and the release flow (three version-bump locations).
- `docs/MCP-CLIENTS.md` — per-client MCP setup for Claude Code, Cursor, Codex CLI, Claude Desktop, Hermes, and generic stdio clients; a no-client smoke test; prompting patterns; troubleshooting table.
- `docs/WORKFLOWS.md` — ecosystem workflow index for XRPL L1, issued tokens, NFTs, AMMs, MPTs, amendments, Xaman, Xahau/Hooks, Flare, Axelar, Arweave, XRPL EVM, bots, and self-hosted nodes — each labeled honestly as live-commands, build-only, or knowledge+references, with a roadmap of the real gaps (Axelar/Arweave commands, `hooks-bitmask` reimplementation, `amm_info`, on-chain FTSO reads).
- README "Documentation" index table linking all guides.
- `SECURITY.md` plain-English rules section: no secrets in the toolkit, no seeds in prompts/agent chats ever, signer-ready JSON only.
- `LIMITATIONS.md` honest-coverage notes (Axelar/Arweave docs-only, Flare price fallback labeling, `hooks-bitmask` disabled).

### Fixed
- `evm-bridge` output still claimed "L1-EVM federated bridge active" — stale devnet-era wording the v1.4.4 pass scrubbed from the docs; now states bridging is Axelar-based and points at docs.xrplevm.org for current gateway details.
- `CONTRIBUTING.md` described the pre-refactor architecture ("tools live in scripts/xrpl_tools.py"); now documents the `scripts/tools/` module pattern, the dev-check commands, and the correct next knowledge-file number.

### Verified
- Pytest suite and MCP stdio smoke test green; live `ledger` query through the CLI path; dev-test matrix regenerated 67/67 PASS (committed).

## v1.4.5 — Dev-test matrix correctness pass — FABLE 5 Audited (2026-06-10)

Repo coherence and currentness audit. Versions, counts (65 knowledge files, 11 references, 67 commands), CLI docs, MCP docs, and reference cards all verified in agreement; live probes re-confirmed current ledger and EVM facts.

### Fixed
- `scripts/dev_test_matrix.py` now runs the CLI with `sys.executable` instead of a bare `python3`, so the matrix works inside virtualenvs (previously every command failed with "xrpl-py missing" under a venv).
- Three matrix invocations exercised builders with invalid arguments and still counted as PASS: `build-amm-withdraw` used a nonexistent `--amount` flag (now `--amount1 XRP:500000`), `build-credential-delete` omitted the required `--subject`/`--issuer`, and `build-set-oracle` used a `--last-update-time` before the Ripple epoch. All three now produce real signer-ready JSON in the matrix.
- Matrix pass criterion tightened: any `build-*` command whose output contains an `"Error"` payload is now a FAIL, so broken builder invocations can no longer hide behind exit code 0. Read-side not-found responses (`nft-info`, `tx-info`) and credential-less `xaman-payload` remain legitimate PASSes.
- `scripts/mcp_server.py` docstring no longer hardcodes a stale "63-file" knowledge count.
- README knowledge map now includes the `64`-`65` row (token intelligence reports, agent freshness and source policy), matching the 65-file claim.

### Verified (live, 2026-06-10)
- `Batch`, `PermissionDelegation`, `XChainBridge`, `DynamicMPT`, `LendingProtocol`, `SingleAssetVault` still supported-but-not-enabled on XRPL mainnet; `TokenEscrow` and `PermissionedDEX` enabled — matches `STANDALONE.md` and `references/amendments.md`.
- `rpc.xrplevm.org` returned `eth_chainId = 0x15f900` (1440000); `explorer.xrplevm.org` and `docs.xrplevm.org` HTTP 200.
- Public node `server-info` reports rippled 3.1.3, matching QUICKSTART's expected-output wording.
- Full matrix regenerated under the stricter criteria: 67/67 PASS. Pytest: 11 passed.

## v1.4.4 — EVM sidechain coherence pass — FABLE 5 Audited (2026-06-10)

Focused repo-coherence pass started by Claude Code/Fable 5 and completed after the Claude session hit its quota limit.

### Fixed
- README first impression no longer names a hosted platform; positioning stays neutral: self-hosted, open source, keys stay yours, bring your own runtime.
- EVM sidechain knowledge files (`knowledge/29-xrpl-metamask-evm.md`, `knowledge/33-xrpl-evm-dev.md`) now use the live explorer URLs (`explorer.xrplevm.org` / testnet explorer), current RPC/WebSocket examples, native XRP gas wording, and Axelar bridge framing instead of stale devnet-era bridge-door/wXRP/federator assumptions.
- Removed hardcoded wrapped-XRP and bridge-door examples; docs now instruct users to verify current contract/gateway details from official docs/live explorer before integrating.
- `pyproject.toml` and `requirements.txt` dependency bounds updated for the installed/current xrpl-py major line while retaining compatibility headroom.

### Verified
- Live probes: `docs.xrplevm.org` and `explorer.xrplevm.org` returned HTTP 200; `rpc.xrplevm.org` returned `eth_chainId = 0x15f900` (1440000).
- Local tests and smoke checks passed after the patch.

## v1.4.3 — Knowledge freshness and depth pass — FABLE 5 Audited (2026-06-10)

Research pass against live ledger state and official public docs (xrpl.org amendment status via live `feature` lookups, docs.xrplevm.org, docs.xaman.dev, chainlist).

### Added
- `knowledge/64-token-intelligence-reports.md` — full live-data methodology for token intelligence: gathering checklist (issuer flags, domain TOML verification, trust lines, obligations, AMM/DEX liquidity depth, transfer rate, recent activity), evidence-cited risk-flag catalog, High/Medium/Low confidence scoring (no trade recommendation at Low), and a report template with a mandatory missing-data section.
- `knowledge/65-agent-freshness-and-source-policy.md` — stable-vs-stale fact taxonomy, verification ladder (ledger > official docs > repo > claims), [live]/[docs]/[repo]/[claimed] phrasing discipline, date-stamping rules, endpoint-failure handling, and citation requirements.
- `references/token-intelligence.md` quick card (references now 11 files).
- SKILL.md freshness core rule ("read the knowledge file, then verify with live tools or official docs before answering"), Agent Discipline knowledge group (64–65), routing-table rows, and counts updated to 65 files.
- README "Staying current" note.

### Fixed — stale ecosystem facts (verified 2026-06-10)
- **Dead EVM explorer URLs**: `evm-sidechain.xrpl.org` (does not resolve) replaced with `https://explorer.xrplevm.org` / `https://explorer.testnet.xrplevm.org` (both live, HTTP 200) in `knowledge/50` and `references/xrpl-evm-sidechain.md`.
- **Devnet-era EVM facts** in the same files: gas token corrected wXRP → native XRP (bridged via Axelar); consensus corrected "authority round-robin federators" → CometBFT PoS (Cosmos SDK chain, mainnet live 2025-06-30); summary table date-stamped.
- `references/amendments.md` snapshot refreshed from 13 live `amendment` lookups and date-stamped: TokenEscrow and PermissionedDEX added to the enabled list; Batch, PermissionDelegation, XChainBridge, DynamicMPT, LendingProtocol, SingleAssetVault re-confirmed not enabled.
- `scripts/mcp_server.py` tool description no longer hardcodes the knowledge-file count.

### Verified, no change needed
- `knowledge/37-xrpl-amendments.md` matches live mainnet state for all 13 amendments checked.
- RLUSD issuer, EVM chain IDs (1440000/1449000), RPC URLs, Xaman payload API endpoint (`xumm.app/api/v1/platform/payload`) and payload flow per docs.xaman.dev.

---

## v1.4.2 — Ledger-correctness audit: currency codes, issuers, bot hygiene — FABLE 5 Audited (2026-06-10)

Second professional audit pass focused on on-ledger correctness, signing hygiene, and bot-readiness.

### Fixed — currency codes (4+ chars require 160-bit hex)
- **SOLO** examples in `knowledge/30-xrpl-xrplpy.md` and `45-xrpl-ecosystem-complete.md` used the invalid 4-char literal; now use `534F4C4F00000000000000000000000000000000`.
- **USDC** issuance sample in `knowledge/38-xrpl-minting-ops.md` used the invalid 4-char literal; now routed through the file's own `currency_to_hex()` helper.
- Generic `"TOKEN"` / `"REWARD"` placeholders in tx samples (`knowledge/36`, `38`, `references/xrpl-l1.md`) replaced with valid 3-char codes (`TKN`, `RWD`) plus hex-requirement notes; corrected a wrong padding comment ("16 chars" → 5 ASCII bytes zero-padded to 20).
- Remaining `--currency RLUSD` / `--cur RLUSD` CLI lines in `knowledge/58` workflow steps now use the RLUSD hex code; trust-line grep updated to match on-ledger output.

### Fixed — issuer addresses
- Wrong SOLO issuer `rHZwvHEs56GCmHupwjA4RY7oPA3EoAJWuN` in `knowledge/30` and `20` (verified live: no domain, no issuer flags) replaced with the Sologenic issuer `rsoLo2S1kiGeCcn6hCUXVrCpGMWLrRrLZz` (verified live: domain sologenic.com, lsfDefaultRipple, lsfDisableMasterKey). Bitstamp issuer in `knowledge/45` verified live and kept.

### Fixed — references/xrpl-l1.md Clawback card
- `Amount.issuer` now correctly documents the **holder**, not the issuer.
- Removed a nonexistent "clawback within 86400 ledgers (~48h)" time-window claim.
- Corrected precondition: `asfAllowTrustLineClawback` can only be enabled while the issuer has no trust lines, and is permanent; clawback is blocked by `asfNoFreeze`.
- Corrected NFT `TransferFee` units comment (0.001% units, max 50000 = 50%).

### Improved — signing hygiene & bot readiness
- `knowledge/46-xrpl-axelar-bridge.md`: hardcoded seed placeholder replaced with the env-var pattern.
- `knowledge/41-xrpl-bots-patterns.md`: `XRPLBot` now documents secret sourcing (env/secrets manager only) and when to prefer signer-ready JSON handoff over a hot wallet.
- `skills/amm-bot-flow.md`: bot loop now defaults to `PAPER_MODE = True`; added a 9-stage go-live checklist (detection → enrichment → scoring → paper → dry-run → review → live → sell integrity → position tracking).
- `SKILL.md`: added "no fake data" core rule (live tools or explicitly *unavailable* with the failed endpoint named), Token Intelligence Rules (≥5 concrete live data points + confidence + missing-data list before any buy/snipe call), and paper-mode-first bot guidance.

---

## v1.4.1 — Neutral positioning + RLUSD accuracy fixes — FABLE 5 Audited (2026-06-09)

### Fixed
- **RLUSD currency code:** 13 code samples in `knowledge/58-rlusd-operations.md` and `59-rwa-tokenization.md` used the literal `"RLUSD"`, which xrpl-py rejects and which never matches ledger responses ("RLUSD" is 5 characters; the ledger requires the 160-bit hex code `524C555344000000000000000000000000000000`). All on-ledger usages now use the hex constant; monitoring comparisons fixed; the doc's CLI example fixed.
- **Wrong RLUSD issuer address** in `knowledge/59-rwa-tokenization.md` (`rMxCKbEDwqr76QuheSkemd63ovSYkPFBCV` — invalid). Corrected to `rMxCKbEDwqr76QuheSUMdEGf4B9xJ8m5De`, verified live on-ledger (domain ripple.com, lsfDefaultRipple + lsfDisableMasterKey).

### Changed
- README "Run your own XRPL agent": removed the feature-comparison table against hosted platforms. The project is positioned as the open-source, self-hosted option — not a pitch against anyone.

### Added
- `references/rlusd.md` and `references/amendments.md` quick-reference cards (condensed from knowledge files 58 and 37), bringing references to 10 files. `SKILL.md` now explains the card → deep-file reading pattern.

---

## v1.4.0 — MCP server + hosted-agent parity — FABLE 5 Audited (2026-06-09)

Full audit pass by Claude (Fable 5): all 9 existing tests pass, all 67 dispatcher commands verified registered, live mainnet smoke tests green (`server-info` against rippled 3.1.3, `amendment MPTokensV1` → Enabled).

### Added
- `scripts/mcp_server.py` — dependency-free stdio MCP server exposing the full toolkit to any MCP client (Claude Code, OpenClaw, Cursor). Four tools: `xrpl_list_commands`, `xrpl_run` (all 67 commands via subprocess, 90s timeout), `xrpl_knowledge_index`, `xrpl_knowledge` (path-sandboxed to `knowledge/` and `references/`).
- `tests/test_mcp_server.py` — offline end-to-end MCP session tests, including bad-command and path-traversal rejection.
- `xrpl-hermes-mcp` console entry point in `pyproject.toml`.
- `SKILL.md` "Core Missions" section: token launch, site/dApp deployment, trading/monitor bots, and skill persistence — the four jobs hosted XRPL agent platforms sell, now first-class flows here.
- `SKILL.md` "Wallet Login Flows" table mapping Xaman, Joey, Privy, and MetaMask handoffs to their knowledge files.
- README positioning section: respectful comparison with hosted XRPL agent platforms and MCP client setup instructions.

### Changed
- Version `1.3.11` → `1.4.0` across `SKILL.md` and `pyproject.toml`.
- `SKILL.md` private-RPC example now uses `clio.example.com` instead of a real-looking placeholder domain (the old one caused harmless but noisy `ERR_NAME_NOT_RESOLVED` link-prefetch errors in desktop agent UIs).
- `QUICKSTART.md`, `STANDALONE.md`, `LIMITATIONS.md` updated for the MCP server.

---

## v1.3.11 — Amendment sync + public release hardening (2026-06-08)

- Added live amendment commands: `amendments`, `amendment`, and `amendment-status`.
- Re-verified XRPL mainnet amendment state against live `feature` RPC and XRPL.org Known Amendments.
- Updated `knowledge/37-xrpl-amendments.md` with current status for AMMClawback, MPTokensV1, DID, Credentials, PriceOracle, TokenEscrow, PermissionedDEX, XRPFees, Batch, PermissionDelegation, XChainBridge, DynamicMPT, LendingProtocol, and SingleAssetVault.
- Added live amendment warnings to MPT, Credential, Oracle, and Batch builders. Batch is supported by current servers but not enabled on XRPL mainnet, so the builder now warns that payloads are build-only unless targeting another network.
- Replaced broken/null `flare-price` endpoint behavior with an honest CoinGecko fallback. Output now labels the source clearly and does not claim direct FTSO proof.
- Added `scripts/dev_test_matrix.py` and generated `AUDIT-tool-matrix.md`; all 67 registered commands passed the safe dev-test matrix.
- Humanized README and updated public positioning around open-source XRPL builder infrastructure, signer-ready JSON, and verified amendment status.

---

## v1.3.10 — Final Dev-Test Audit (2026-05-09)

### 🐛 Crash / JSON Fixes
- `scripts/tools/wallet.py`: `wallet-from-seed` no longer leaks a Python traceback on an invalid seed — now emits clean `{"Error":"InvalidSeed"}` JSON.
- `scripts/xrpl_streams.py`: `subscribe` now correctly parses both documented forms (`streams=ledger,transactions` and `--streams ledger,transactions`) and the optional `--count` alias for `--duration`. Was crashing with `TypeError: unexpected keyword argument 'streams=ledger,transactions'`.
- `scripts/tools/ledger.py`: `tx-info` now emits a clean `{"Error":"txnNotFound", ...}` JSON when the lookup fails instead of returning a row of `"?"` placeholders.

### 🐛 Accuracy Fixes
- `scripts/tools/accounts.py`: `account-tx` now resolves the transaction hash from the API v2 top-level `hash` field (xrpl-py 4.x format). Previously every entry returned `"Hash": null`.
- `scripts/tools/amm.py`: `build-amm-create` now requires only the 3 mandatory args (`--from`, `--amount1`, `--amount2`) — `--fee` keeps its default of 600. The min-pairs check was incorrectly set to 4 and rejected the documented usage.

### 🐛 Knowledge Base Fixes
- XRPL EVM **testnet** chain ID corrected from stale `1450024` to live `1449000` in `knowledge/29-xrpl-metamask-evm.md`, `33-xrpl-evm-dev.md`, `35-xrpl-full-interop.md`, `44-xrpl-evm-advanced.md`, and `references/xrpl-evm-sidechain.md`. Confirmed live via `eth_chainId` against `https://rpc.testnet.xrplevm.org` (`0x161c28` = 1,449,000). The dispatcher in `scripts/tools/evm.py` already used `1449000`; only the docs were stale.

### 🧹 Doc / Packaging
- `STANDALONE.md`: header updated from the old 48-tool wording to the then-current 64-tool dispatcher count.
- `LIMITATIONS.md`: old "48+ tools, 59+ knowledge files" wording updated to the then-current 64-tool / 63-file count.
- `QUICKSTART.md`: replaced stale flat-text sample outputs for `server-info` and `account` with the real JSON shape the CLI emits today.
- `pyproject.toml`: bumped version `1.3.8` → `1.3.9`; replaced bogus `setuptools.backends._legacy:_Backend` build-backend with the canonical `setuptools.build_meta`.

---

## v1.3.9 — Polish Pass: Clawback, Docs, CI, Deps, Debloat (2026-05-09)

### Fixed
- Removed dead `issuer` parameter from `tool_build_clawback` (was silently ignored — per XLS-39, `--from` IS the issuer)
- Fixed stale XRPL reserve formula in `42-xrpl-treasury.md` (was `2 XRP/obj + 10 XRP base`, now `0.2 + 1`)
- Fixed wrong GateHub address in `45-xrpl-ecosystem-complete.md` (was genesis account `rHb9CJA`, now `rH8G4N6`)
- De-bloated `56-telegram-xrpl-bots.md` — removed 43x copy-paste repeated sections, replaced with 5 real production patterns (webhook, auth, keyboards, conversations, rate limiting)
- De-bloated `57-discord-xrpl-bots.md` — removed 41x copy-paste repeated sections, replaced with 5 real production patterns (slash commands, views, embeds, error handling, guild config)
- Fixed AMM example issuer in `57-discord-xrpl-bots.md` (was genesis account, now Bitstamp `rvYAfWj5`)
- Fixed SECURITY.md: accurately described local seed-handling with CLI warning (replaced absolute "NEVER handles seeds" wording)
- Fixed CI workflow: now runs `pytest -q` + build-payment smoke test (was only `server-info`)
- Fixed pyproject.toml: 59→63 knowledge files, aligned deps with requirements.txt, added `[project.scripts]` entry point
- Deleted stale `scripts/xrpl_tools.py.bak`

---

## v1.3.8 — Module Split + 16 New Tools + Professional Polish (2026-05-04)

### 🏗 Breaking: Monolith → 20 Modules
- Split `scripts/xrpl_tools.py` (1,377 lines) into 20 focused modules under `scripts/tools/`
- Thin dispatcher (`xrpl_tools.py`) now just imports and merges `COMMANDS` dicts
- New import pattern: `from scripts.tools.nfts import tool_build_nft_mint`
- `scripts/xrpl_streams.py` added for async WebSocket tools (optional dep)

### 🆕 New Tools (16 added, now 64 total)
- **Account config**: `build-account-set` — all AccountSet flags (DefaultRipple, Domain, TickSize, TransferRate, Clawback enable, etc.)
- **NFT marketplace**: `build-nft-create-offer`, `build-nft-accept-offer`, `build-nft-cancel-offer`, `build-nft-burn`, `nft-offers` (sell/buy offer discovery)
- **TX submission**: `submit` (blob), `submit-multisigned` (multi-sign JSON)
- **Real-time streaming**: `subscribe` — WebSocket subscriptions (ledger, transactions, accounts, books) via `xrpl_streams.py`
- **Wallet utilities**: `wallet-generate`, `wallet-from-seed`, `validate-address`
- **Xaman integration**: `xaman-payload` — real Xaman Platform API (replaces fake URLs)
- **Bots & power users**: `account-tx` (transaction history), `build-ticket-create` (parallel tx), `ledger-entry` (generic object lookup)

### 🐛 Fixes
- **Deleted** `scripts/xrpl_tx_builder.py` (broken import path — `xrpl.binary_codec` → `xrpl.core.binarycodec`)
- **Fake Xaman URLs** replaced in `knowledge/56-telegram-xrpl-bots.md` and `examples/example-telegram-bot.py` — the old `https://xumm.app/sign/{json}` pattern would 404. Replaced with real `xaman-payload` CLI flow
- **Clawback flag** wrong constant (`536870912`) corrected to `2147483648` in `knowledge/07-xrpl-clawback.md`

### 📚 Knowledge Expansion (59 → 63 files)
- New `60-xrpl-account-set.md` — every asf flag, issuer setup checklist, CLI examples
- New `61-xrpl-websocket-streams.md` — all subscribe stream types, reconnection, NDJSON output
- New `62-xrpl-nft-marketplace.md` — full marketplace flow: mint → list → discover → accept → cancel
- New `63-xrpl-xaman-platform.md` — real Platform API, env vars, webhook callbacks, Telegram+Xaman workflow
- Expanded `56-telegram-xrpl-bots.md` (199→350+ lines): database pattern, inline keyboards, systemd/Docker deploy
- Expanded `57-discord-xrpl-bots.md` (233→517 lines): slash commands, embeds, AMM monitoring
- Expanded `08-xrpl-mpts.md` (249→499 lines): end-to-end issuance code, holder example, balance queries

### 🧪 Testing & CI
- New `tests/test_tool_outputs.py` (78 lines) — validates payment, account-set, NFT create-offer, parse_amount_arg, clawback validation, `_dispatch_build` arg mapping
- `.github/workflows/ci.yml` — runs on every push/PR to main

### 🏭 Professional Polish
- `pyproject.toml` added — modern Python packaging, `pip install` namespaced as `xrpl-hermes`
- README repositioned as "The Open-Source XRPL Developer Toolkit" — badges, build guide layout, tool/knowledge maps
- SKILL.md description updated: "63 files, 33K+ lines + 67 working tools"

---

## v1.3.6 — Continuation Dev-Test Audit (2026-05-02)

### Crash / JSON Fixes
- `scripts/xrpl_tools.py`: Query tools now emit valid JSON on stdout instead
  of human-formatted text. Covered `account`, `balance`, `trustlines`,
  `account_objects`, `decode`, `tx-info`, `ledger`, `server-info`,
  `nft-info`, `book-offers`, `path-find`, `evm-balance`, `evm-bridge`,
  `hooks-bitmask`, `hooks-info`, and `flare-price`.
- `scripts/xrpl_tools.py`: AMM asset parsing now accepts amount-shaped asset
  examples such as `--asset1 XRP:1000000` and `--asset2 USD:rISS:100` by
  stripping values when building `Asset` / `Asset2`.
- `scripts/xrpl_tools.py`: `evm-bridge` now verifies `eth_chainId` live and
  includes both configured and observed chain IDs in JSON output.

### Docs / Verification
- `STANDALONE.md`: Updated account sample output and `hooks-bitmask` wording to
  match JSON output.
- `SKILL.md`: Reordered the 48-tool table to match the dispatcher exactly.
- Verified README counts against the repo for that release.
- Verified XRPL EVM RPC requires `Content-Type: application/json`; with the
  header, `eth_chainId` reports `0x15f900` (`1440000`).

### Continuation Re-Verification (2026-05-02)
- All 16 query tools and all 32 build tools re-executed against live mainnet
  with the documented argument syntax. Every command produced valid JSON and
  no traceback (verification table appended to PR notes).
- `tx-info` confirmed against a fresh validated-ledger payment hash; `nft-info`
  confirmed against an `NFTokenMint` discovered in the same ledger.
- `evm-balance`, `evm-bridge`: live `https://rpc.xrplevm.org` returns
  `eth_blockNumber` and `eth_chainId 0x15f900` (1440000) — chain ID unchanged.
- `flare-price`: both upstream feed URLs in `tool_flare_price` are still
  reachable but currently 404 / empty; tool returns `{"Prices":{...:null},
  "FeedCount":0}` (valid JSON, graceful degradation — no code change made
  per audit rule "fix only crashes / invalid JSON").
- STANDALONE.md examples spot-checked: `build-payment` `--cur/--iss`,
  `build-amm-bid --bid-min`, `account_objects [type]`, and `ledger INDEX`
  all run as documented.

---

## v1.3.4 — Pre-Release Audit Round 2 (2026-05-02)

### 🐛 Crash Fixes
- `build-set-oracle`: Was crashing with an xrpl-py validation traceback when
  `--price-data` was omitted. Now prints a clear usage hint and exits cleanly.
- `build-paychannel-claim`: Was rejecting the documented `--balance` flag with
  `TypeError`. Now accepts `--balance DROPS` and emits it as the canonical
  `Balance` field on `PaymentChannelClaim`.

### 🐛 Accuracy Fixes (Knowledge)
- `knowledge/07-xrpl-clawback.md`: `lsfAllowTrustLineClawback` flag value was
  documented as `0x20000000 / 536870912`. Corrected to `0x80000000 / 2147483648`
  (matches xrpl.org and xrpl-py `AccountRootFlags`).
- `knowledge/58-rlusd-operations.md`: Same flag bug — Python sample used
  `CLAWBACK_FLAG = 0x00800000` while the comment claimed `0x80000000`. Fixed
  the value, and replaced the truncated `rMxCKbEDwqr76...` placeholder with
  the live mainnet issuer `rMxCKbEDwqr76QuheSUMdEGf4B9xJ8m5De`.
- `knowledge/50-xrpl-evm-sidechain.md`: Testnet chain ID was listed as
  `1450024` in the network table and the Hardhat config sample. Live RPC
  reports `1449000` (matches `scripts/xrpl_tools.py`); both occurrences
  corrected.

### 📚 Knowledge Base Hygiene
- All knowledge files in that release ended with a `## Related Files` section with
  topical cross-references (was 10/59 before this pass). Files 46–51 and 59
  had a `## Cross-References` heading; renamed for consistency.

### 🧹 Docs
- `STANDALONE.md`: Added missing CLI sections for `build-amm-deposit`,
  `build-amm-withdraw`, `build-amm-vote`, `build-amm-bid`,
  `build-signer-list-set`, `build-mpt-issuance-create`, `build-mpt-authorize`,
  `build-set-oracle`, `build-credential-create/accept/delete`,
  `build-cross-currency-payment`, and `build-batch`. Covered the full dispatcher at that release.
- `STANDALONE.md`: `hooks-bitmask` entry now carries the same ⚠️ BROKEN
  warning that `SKILL.md` and `README.md` already use.
- `STANDALONE.md` + `SKILL.md`: documented `--balance` on
  `build-paychannel-claim`.

---

## v1.3.4 — Pre-Release Audit (2026-05-02)

### 🐛 Accuracy Fixes
- `knowledge/08-xrpl-mpts.md`: Added separate `MPTokenIssuanceCreate` section (was incorrectly using `MPTokenIssuanceSet` as the creation TX throughout); fixed minting description
- `knowledge/07-xrpl-clawback.md`: Comparison table "Full balance only" → "Partial supported" (contradicted correct text in the same file)
- `knowledge/36-xrpl-xls-standards.md`: DID section header was "XLS-60" → corrected to **XLS-40**; Hooks section removed incorrect XLS-40 label
- `knowledge/37-xrpl-amendments.md`: `AMENDMENT_IDS` dict had "DID (XLS-60)" → **"DID (XLS-40)"**; fixed two table rows with empty Amendment-name cells
- `knowledge/43-xrpl-hooks-advanced.md`: Removed incorrect "pending XLS-40 vote" claim for Hooks (XLS-40 is DID)

### 🧹 Docs
- `SKILL.md` tool #22: `--max-amount` → **`--maximum-amount`** (matches actual function parameter)
- `SKILL.md` / `STANDALONE.md`: `evm-contract --from rADDR` → **`--from 0xADDR`** (EVM needs 0x address)
- `README.md`: Added ⚠️ BROKEN note to `hooks-bitmask` tool entry (was silently undocumented)
- `CHANGELOG.md`: Removed copy-pasted Developer Experience bullets from v1.2 section (identical to v1.1)

### ✅ Infrastructure
- `scripts/xrpl_tools.py`: `book-offers` now retries all failover endpoints (was hardcoded to `ENDPOINTS[0]`)
- `scripts/xrpl_tools.py`: Removed duplicate `TOOL 12–17` comment labels from escrow/check/paychannel functions

---

## v1.3.3 — Cleanup Pass (2026-04-30)

---

## v1.3.1 — Critical Bugfix Pass (2026-04-30)

### 🐛 Crash Fixes
- `build-batch`: Now wraps inner dicts in proper Transaction models + validates 2-8 inner txs
- `build-clawback --memo`: Fixed `MemoWrapper` ImportError — uses `Memo` directly
- `build-mpt-issuance-create --transfer-fee`: Auto-sets `tfMPTCanTransfer` flag
- `hooks-bitmask`: Disabled with warning (was using fictional event names, wrong spec)
- Dead Xaman URL removed from `build-payment` — replaced with honest manual-sign instructions

### 🧹 Docs & Knowledge
- `knowledge/07-xrpl-clawback.md`: `SetFlag` 14→16 (`asfAllowTrustLineClawback`), removed "no partial clawback" lie
- `knowledge/08-xrpl-mpts.md`: XLS-70→XLS-33 throughout
- `knowledge/36-xrpl-xls-standards.md`: XLS-70→XLS-33 for MPT section
- `knowledge/37-xrpl-amendments.md`: XLS-33 for MPT, XLS-70 for Credentials, Batch (not Auth Framework)
- `knowledge/38-xrpl-minting-ops.md`: XLS-70→XLS-33 for MPT table
- `references/xrpl-l1.md`: XLS-70→XLS-33 for MPT references
- `QUICKSTART.md`: Fixed git clone URL (was 404), fixed `server-info` output format
- `STANDALONE.md`: Fixed token payment example, removed dead `xaman-url` section
- `CONTRIBUTING.md`: Updated file numbering, TOOLS→dispatcher
- `.env.example`: Cleaned up — only includes vars the code actually reads

### ✅ Infrastructure
- Lazy network client — module loads instantly, build commands work offline
- `nft-info`: Fixed `PUBLIC_ENDPOINTS`→`ENDPOINTS` (undefined variable crash)
- `evm-balance` docs: rADDR→0xADDRESS
- `evm-bridge`: Per-network Chain IDs + error handling
- SKILL.md tool table regenerated from the real dispatcher count at that release

---

## v1.3 — Audit Fixes (2026-04-30)

### ✅ Accuracy
- Fixed `knowledge/01-xrpl-accounts.md`: Account deletion now correctly documented (was previously stated as impossible). Full requirements, special burn cost, and example added.
- Fixed `knowledge/37-xrpl-amendments.md`: Corrected DID and Hooks XLS numbering.

### 🧹 Prompt
- SKILL.md: "Stream thinking" → "Show concise reasoning summaries and cite relevant files"
- Self-improvement instructions marked as Hermes-specific capability

---

## v1.1 — Polish Release (2026-04-29)

### 🧹 Privacy
- Removed personal wallet addresses from README.md and SKILL.md
- Replaced example addresses with neutral testnet address

### 🚀 New Content
- Added UniswapV2-style swap contract + liquidity pool examples for XRPL EVM
- Added EVM swap/liquidity: pair contract, add/remove liquidity, swap execution, price impact calculator

### 🛠 Developer Experience
- Added requirements.txt (xrpl-py, httpx, web3, eth-account)
- Added setup.sh — one-command install script with verification
- Added examples/ folder with 3 ready-to-run scripts
- Added CONTRIBUTING.md, CHANGELOG.md

### ✅ Accuracy
- Corrected EVM RPC URLs: `rpc-evm-sidechain.xrpl.org` → `rpc.xrplevm.org`
- Corrected chain IDs: 1440001→1440000 (mainnet), 1440002→1450024 (testnet)
- Fixed owner reserve values: 2 XRP → 0.2 XRP across 12 knowledge files
- Deduplicated functions in xrpl_tools.py
- Corrected tool count: 35→34 in README, SKILL.md, CHANGELOG

---

## v1.2 — xrpl.js Hooks, Xahau Patterns, MPT/AMM/DID (2026-04-30)

### 🚀 New Content
- Added 432 lines of xrpl.js coverage: Hooks install/query/state/emit (16 sections)
- Added Xahau-specific patterns: network ID, URITokens, Import bridge, namespace conventions
- Added beta features: MPT issuance/authorize/send, AMM create/deposit/withdraw, DID operations

### 📚 Documentation
- Added CONTRIBUTING.md with clear PR and knowledge file guidelines
- Added CHANGELOG.md
- Updated README.md with links to setup.sh, examples/, and CONTRIBUTING.md

---

## v1.0 — Initial Release

- 55 knowledge files covering L1, EVM, Xahau, Flare, Axelar, Arweave, Evernode
- 34 CLI tools for transactions, NFTs, AMM, DEX, escrow, bridges
- SKILL.md master prompt for Hermes Agent activation
- MIT licensed — free for everyone
