# ☤ xrpl-hermes

**The open-source, all-in-one XRPL ecosystem toolkit for Hermes agents.**

**59 knowledge files + 48 working tools** covering **XRPL L1, EVM Sidechain, Xahau Hooks, Flare FTSO, Axelar Bridge, and Arweave**

## Quick Start

```bash
# One-command setup
bash setup.sh

# Or manually
pip install -r requirements.txt

# Run a query
python3 scripts/xrpl_tools.py ledger

# Check an account
python3 scripts/xrpl_tools.py account rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe

# Build a transaction
python3 scripts/xrpl_tools.py build-payment --from rADDR --to rADDR --amount 10000000
```

## Hermes Agent Installation

```bash
# Copy to your Hermes skills directory
cp -r xrpl-hermes ~/.hermes/skills/xrpl/xrpl-hermes

# Load the skill in chat:
# > activate xrpl-hermes
```

## 48 Tools — All Ecosystems

### XRPL L1 (32 tools)

| Tool | Description |
|------|-------------|
| `account` | Account info, balance, flags, sequence |
| `balance` | Account balance (alias) |
| `trustlines` | All trust lines for an address |
| `account_objects` | All objects (checks, offers, escrows, NFTs) |
| `build-payment` | Payment transaction JSON |
| `build-trustset` | Trust line setup JSON |
| `build-offer` | DEX order JSON |
| `build-nft-mint` | NFT mint JSON |
| `build-amm-create` | AMM pool creation |
| `build-clawback` | Issuer clawback transaction |
| `build-cross-currency-payment` | Path-finding cross-currency payment |
| `build-escrow-create/finish/cancel` | Escrow management |
| `build-check-create/cash/cancel` | Check management |
| `build-paychannel-create/fund/claim` | Payment channels |
| `build-amm-deposit/withdraw/vote/bid` | AMM LP operations |
| `build-set-regular-key` | Key management |
| `build-account-delete` | Account deletion |
| `build-deposit-preauth` | Deposit preauthorization |
| `build-signer-list-set` | Multisig signer list |
| `build-mpt-issuance-create` | MPT issuance (XLS-33) |
| `build-mpt-authorize` | MPT holder authorization |
| `build-set-oracle` | Price oracle (XLS-47) |
| `build-credential-create/accept/delete` | DID credentials (XLS-70) |
| `build-batch` | Batch transactions (XLS-56) |
| `decode` | Decode signed transaction blobs |
| `tx-info` | Transaction lookup |
| `ledger` | Ledger state |
| `server-info` | Node information |
| `nft-info` | NFT metadata |
| `book-offers` | DEX orderbook depth |
| `path-find` | Payment path discovery |

### EVM Sidechain (3 tools)

| Tool | Description |
|------|-------------|
| `evm-balance` | Query XRP balance on EVM sidechain |
| `evm-contract` | Build contract deployment JSON |
| `evm-bridge` | Check bridge status |

### Xahau Hooks (2 tools)

| Tool | Description |
|------|-------------|
| `hooks-bitmask` | Calculate HookOn trigger bitmask |
| `hooks-info` | Query installed hooks on Xahau |

### Flare / Price Feeds (1 tool)

| Tool | Description |
|------|-------------|
| `flare-price` | Live XRP, BTC, ETH price feeds |

## 59 Knowledge Files

| Layer | Files | Topics |
|-------|-------|--------|
| XRPL L1 Core (01-15) | 15 files | Accounts, Payments, Trustlines, DEX, AMM, NFTs, Clawback, MPTs, Escrow, Checks, Payment Channels, Multisig, Tickets, Consensus, Transaction Format |
| Infrastructure (16-20) | 5 files | Clio, Private Nodes, Rate Limits, Tx Costs, Data APIs |
| Token Operations (21-25) | 5 files | Token Model, Issuance, NFT Minting, Deployment, Security |
| Wallets (26-30) | 5 files | Xaman, Joey, Privy, MetaMask, xrpl-py |
| Side Ecosystems (31-35) | 5 files | xrpl.js, Hooks Dev, EVM Dev, AMM Bots, Interop |
| Advanced (36-45) | 10 files | XLS Standards, Amendments, Minting Ops, NFT Ops, Monitoring, Bot Patterns, Treasury, Hooks Advanced, EVM Advanced, Ecosystem Map |
| Cross-Chain (46-55) | 10 files | L1 Reference, Wallets/Auth, Evernode, Sidechain Interop, Axelar Bridge, Arweave, TX Ecosystem, Flare FTSO, EVM Sidechain, Xahau Hooks |
| References (8 files) | 8 files | XRPL L1, EVM, Hooks, Flare, Axelar, Arweave, TX, Wallets |

## Examples

Ready-to-run scripts in `examples/`:

- [`example-build-payment.py`](examples/example-build-payment.py) — Send XRP on testnet
- [`example-mint-nft.py`](examples/example-mint-nft.py) — Mint an XLS-20 NFT on testnet
- [`example-evm-swap.py`](examples/example-evm-swap.py) — Simulate a swap on XRPL EVM sidechain

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for how to add knowledge, improve tools, or fix docs.

## Changelog

See [`CHANGELOG.md`](CHANGELOG.md) for release history.

## License

MIT — free for everyone. Use it, fork it, build with it.

## GitHub

https://github.com/CarpXRPL/xrpl-hermes
