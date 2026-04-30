# Changelog

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
