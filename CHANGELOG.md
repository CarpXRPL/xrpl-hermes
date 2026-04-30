# Changelog

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

### 🛠 Developer Experience
- Added requirements.txt (xrpl-py, httpx, web3, eth-account)
- Added setup.sh — one-command install script with verification
- Added examples/ folder with 3 ready-to-run scripts:
  - `example-build-payment.py` — XRP payment on testnet
  - `example-mint-nft.py` — XLS-20 NFT mint on testnet
  - `example-evm-swap.py` — UniswapV2-style swap simulation on XRPL EVM

---

## v1.0 — Initial Release

- 55 knowledge files covering L1, EVM, Xahau, Flare, Axelar, Arweave, Evernode
- 34 CLI tools for transactions, NFTs, AMM, DEX, escrow, bridges
- SKILL.md master prompt for Hermes Agent activation
- MIT licensed — free for everyone
