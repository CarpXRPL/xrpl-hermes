# ☤ xrpl-hermes — The Open-Source XRPL Developer Toolkit

Build real XRPL applications with 63 knowledge files, 64 CLI commands, and signer-ready transaction JSON for XRPL L1, NFTs, AMMs, issued tokens, MPTs, Xaman, Xahau Hooks, Flare, Axelar, Arweave, and the XRPL EVM Sidechain.

[![GitHub stars](https://img.shields.io/github/stars/CarpXRPL/xrpl-hermes?style=social)](https://github.com/CarpXRPL/xrpl-hermes)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
[![CI](https://github.com/CarpXRPL/xrpl-hermes/actions/workflows/ci.yml/badge.svg)](https://github.com/CarpXRPL/xrpl-hermes/actions/workflows/ci.yml)

## What You Can Build

| Build | Example |
|---|---|
| Token Launch | Configure issuer flags, domain, transfer rate, trust lines, and mintable supply. |
| NFT Marketplace | Mint NFTs, create sell offers, discover offers, accept offers, cancel stale offers, and burn inventory. |
| Trading Bot | Monitor books, path-find payments, place DEX offers, and react to AMM liquidity changes. |
| Telegram Monitor | Watch accounts, stream ledger events, and send Xaman signing requests to users. |
| Multisig Treasury | Build signer lists, tickets, batch transactions, and submit multisigned blobs. |
| Cross-Chain dApp | Combine XRPL L1 with EVM Sidechain, Axelar Bridge, Flare FTSO, and Arweave metadata. |

## Quick Start

```bash
pip install -r requirements.txt && python3 -m scripts.xrpl_tools ledger
```

Useful first commands:

```bash
python3 -m scripts.xrpl_tools server-info
python3 -m scripts.xrpl_tools account rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe
python3 -m scripts.xrpl_tools build-payment --from rSRC --to rDST --amount 10000000
```

## Tool Table

64 commands are split across about 20 Python modules in `scripts/tools/`.

| Ecosystem | Count | Commands |
|---|---:|---|
| XRPL L1 core and ops | 42 | `account`, `balance`, `account_objects`, `account-tx`, `trustlines`, `build-payment`, `build-trustset`, `build-offer`, `book-offers`, `path-find`, `ledger`, `ledger-entry`, `server-info`, `tx-info`, `decode`, `submit`, `submit-multisigned`, `build-account-set`, `build-account-delete`, `build-set-regular-key`, `build-deposit-preauth`, `build-signer-list-set`, `build-ticket-create`, `build-escrow-create`, `build-escrow-finish`, `build-escrow-cancel`, `build-check-create`, `build-check-cash`, `build-check-cancel`, `build-paychannel-create`, `build-paychannel-fund`, `build-paychannel-claim`, `build-clawback`, `build-cross-currency-payment`, `build-batch`, `build-set-oracle`, `build-credential-create`, `build-credential-accept`, `build-credential-delete`, `build-mpt-issuance-create`, `build-mpt-authorize`, `subscribe` |
| NFT marketplace | 7 | `nft-info`, `nft-offers`, `build-nft-mint`, `build-nft-create-offer`, `build-nft-accept-offer`, `build-nft-cancel-offer`, `build-nft-burn` |
| AMM liquidity | 5 | `build-amm-create`, `build-amm-deposit`, `build-amm-withdraw`, `build-amm-vote`, `build-amm-bid` |
| EVM Sidechain | 3 | `evm-balance`, `evm-contract`, `evm-bridge` |
| Xahau Hooks | 2 | `hooks-bitmask`, `hooks-info` |
| Flare | 1 | `flare-price` |
| Wallet utils | 3 | `wallet-generate`, `wallet-from-seed`, `validate-address` |
| Xaman Platform | 1 | `xaman-payload` |

## Knowledge Map

| Range | Topics |
|---|---|
| `01`-`15` | XRPL accounts, payments, trust lines, DEX, AMM, NFTs, clawback, MPTs, escrow, checks, channels, multisig, tickets, consensus, transaction format |
| `16`-`25` | Clio, private nodes, rate limits, costs, Data API, token model, issuance, NFT minting, deployment, security |
| `26`-`35` | Xaman, wallets, Privy, MetaMask, xrpl-py, xrpl.js, Hooks, EVM, AMM bots, interop |
| `36`-`45` | XLS standards, amendments, minting ops, NFT ops, monitoring, bot patterns, treasury, advanced hooks/EVM, ecosystem map |
| `46`-`55` | Axelar, Arweave, TX ecosystem, Flare, EVM Sidechain, Xahau, L1 reference, wallet auth, Evernode, sidechain interop |
| `56`-`63` | Telegram bots, Discord bots, RLUSD, RWA tokenization, AccountSet flags, WebSocket streams, NFT marketplaces, Xaman Platform |

## Hermes Agent Installation

```bash
git clone https://github.com/CarpXRPL/xrpl-hermes.git
cd xrpl-hermes
pip install -r requirements.txt

# Copy into a Hermes/Codex skills directory if your agent runtime uses local skills.
cp -r . ~/.hermes/skills/xrpl/xrpl-hermes
```

Activate with:

```text
activate xrpl-hermes
```

## Contributing

Use the existing module pattern in `scripts/tools/`: each module exposes a `COMMANDS` dict and emits JSON through shared helpers. Add or update focused pytest coverage in `tests/` when changing command output.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`CHANGELOG.md`](CHANGELOG.md).

## License

MIT. Free to use, fork, and build with.
