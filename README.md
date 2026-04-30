# 🦞 xrpl-hermes

**The open-source, all-in-one XRPL ecosystem toolkit for Hermes agents.**

**55 knowledge files + 35 working tools** covering **XRPL L1, EVM Sidechain, Xahau Hooks, Flare FTSO, Axelar Bridge, and Arweave**

## Quick Start

```bash
# Install dependency
pip install xrpl-py

# Clone the skill
git clone https://github.com/CarpXRPL/xrpl-hermes.git

# Run a query
cd xrpl-hermes
python3 scripts/xrpl_tools.py ledger

# Check an account
python3 scripts/xrpl_tools.py account rNZzab1XjmdQ2atiBzVDTxZnXqJQdZNeQG

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

## 35 Tools — All Ecosystems

### XRPL L1 (29 tools)
| Tool | Description |
|------|-------------|
| `account` | Account info, balance, flags, sequence |
| `trustlines` | All trust lines for an address |
| `account_objects` | All objects (checks, offers, escrows, NFTs) |
| `build-payment` | Payment transaction JSON |
| `build-trustset` | Trust line setup JSON |
| `build-offer` | DEX order JSON |
| `build-nft-mint` | NFT mint JSON |
| `build-amm-create` | AMM pool creation |
| `build-escrow-create/finish/cancel` | Escrow management |
| `build-check-create/cash/cancel` | Check management |
| `build-paychannel-create/fund/claim` | Payment channels |
| `build-set-regular-key` | Key management |
| `build-account-delete` | Account deletion |
| `build-deposit-preauth` | Deposit preauthorization |
| `decode` | Decode signed transaction blobs |
| `tx-info` | Transaction lookup |
| `ledger` | Ledger state |
| `server-info` | Node information |
| `book-offers` | DEX orderbook depth |
| `nft-info` | NFT metadata |
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

## 55 Knowledge Files

|| Layer | Files | Topics |
||-------|-------|--------|
|| XRPL L1 Core (01-15) | 15 files | Accounts, Payments, Trustlines, DEX, AMM, NFTs, Clawback, MPTs, Escrow, Checks, Payment Channels, Multisig, Tickets, Consensus, Transaction Format |
|| Infrastructure (16-20) | 5 files | Clio, Private Nodes, Rate Limits, Tx Costs, Data APIs |
|| Token Operations (21-25) | 5 files | Token Model, Issuance, NFT Minting, Deployment, Security |
|| Wallets (26-30) | 5 files | Xaman, Joey, Privy, MetaMask, xrpl-py |
|| Side Ecosystems (31-35) | 5 files | xrpl.js, Hooks Dev, EVM Dev, AMM Bots, Interop |
|| Advanced (36-45) | 10 files | XLS Standards, Amendments, Minting Ops, NFT Ops, Monitoring, Bot Patterns, Treasury, Hooks Advanced, EVM Advanced, Ecosystem Map |
|| Cross-Chain (46-55) | 10 files | L1 Reference, Wallets/Auth, Evernode, Sidechain Interop, Axelar Bridge, Arweave, TX Ecosystem, Flare FTSO, EVM Sidechain, Xahau Hooks |
|| References (8 files) | 8 files | XRPL L1, EVM, Hooks, Flare, Axelar, Arweave, TX, Wallets |

## License

MIT — free for everyone. Use it, fork it, build with it.

## GitHub

https://github.com/CarpXRPL/xrpl-hermes
