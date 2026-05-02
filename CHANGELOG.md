# Changelog

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
- Verified README counts against the repo: 59 knowledge files and 48 CLI tools.
- Verified XRPL EVM RPC requires `Content-Type: application/json`; with the
  header, `eth_chainId` reports `0x15f900` (`1440000`).

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
- All 59 knowledge files now end with a `## Related Files` section with
  topical cross-references (was 10/59 before this pass). Files 46–51 and 59
  had a `## Cross-References` heading; renamed for consistency.

### 🧹 Docs
- `STANDALONE.md`: Added missing CLI sections for `build-amm-deposit`,
  `build-amm-withdraw`, `build-amm-vote`, `build-amm-bid`,
  `build-signer-list-set`, `build-mpt-issuance-create`, `build-mpt-authorize`,
  `build-set-oracle`, `build-credential-create/accept/delete`,
  `build-cross-currency-payment`, and `build-batch`. Now covers all 48 tools.
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
- SKILL.md tool table regenerated from real dispatcher (48 tools)

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
