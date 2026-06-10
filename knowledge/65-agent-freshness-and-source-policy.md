# Agent Freshness & Source Policy

This knowledge base is a starting point, not live truth. Markdown ages; the ledger does not wait for documentation. This file defines how an agent using xrpl-hermes keeps its claims current.

## The core rule

> For current XRPL facts: read the knowledge file for context, then **verify with live tools or official docs before answering**. State which you did.

"Current facts" means anything that can change without this repo changing: amendment status, fees and reserves, endpoint availability, issuer account state, token supply, liquidity, chain IDs of evolving networks, API shapes of external services.

## What is stable vs. what goes stale

| Stable (knowledge file is sufficient) | Goes stale (verify live) |
|---|---|
| Transaction field semantics, flag meanings | Amendment enabled/vetoed status |
| Currency-code encoding rules (3-char vs 160-bit hex) | Base fee, reserves (`server-info`) |
| Consensus mechanics, escrow/check/channel semantics | Issuer flags, domains, balances |
| Signing model, multisig rules | Endpoint health, rate limits |
| Address encoding | Explorer/API URLs of external services |
| | Token supply, holders, order books, AMM pools |

## Verification ladder

1. **Ledger facts** → live tools: `server-info`, `amendments` / `amendment NAME`, `account`, `trustlines`, `book-offers`, `account-tx`, `tx-info`.
2. **Protocol behavior** → xrpl.org / rippled release notes; the knowledge file should agree — if it doesn't, trust the official doc and flag the discrepancy for a repo fix.
3. **Ecosystem services** (Xaman, Xahau, XRPL EVM, Axelar, Flare, explorers) → their official docs. URLs in this repo were verified at the date stamped in CHANGELOG; re-check before telling a user to rely on one.
4. **Token claims** (supply, holders, "team", age) → live ledger + named metadata source. Marketing material is never a source for a number.

## Date-stamping and phrasing

- Any answer containing a stale-able fact states *when and how* it was verified: "enabled on mainnet (checked live via `amendment Batch`, 2026-06-10)" — not "Batch is enabled."
- Distinguish clearly in answers: **[live]** from a tool run this session, **[docs]** from official documentation, **[repo]** from this knowledge base, **[claimed]** from project marketing or third parties.
- If two sources disagree, report both and which one is authoritative for that fact (ledger > official docs > repo > anything else).

## Failure handling

- An endpoint failing is a reportable fact, not a gap to paper over: "holder count unavailable — XRPSCAN obligations endpoint returned 5xx."
- Never substitute a remembered, typical, or interpolated number for a failed lookup.
- If all public endpoints fail, say so and suggest `XRPL_PRIVATE_RPC`.

## Citing

- Cite local files by path (`knowledge/37-xrpl-amendments.md`) when knowledge informed the answer.
- Cite URLs for external docs.
- Cite the exact command for live data so the user can re-run it.

## Repo maintenance signal

When live verification contradicts a knowledge file, fixing the answer is half the job — note the file and line so the repo gets corrected. Stale markdown that survives contradiction will mislead the next session.
