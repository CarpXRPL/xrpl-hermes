# XRPL Ecosystem — Evidence Map

## Purpose

This is a routing index for the distinct networks and external services covered by XRPL-Hermes.

## Separated surfaces

### XRPL L1

Native XRP Ledger functionality: accounts, XRP and issued currencies, trust lines, order-book DEX, AMM, escrows, checks, payment channels, NFTs, MPTs, credentials, DIDs, and amendment-gated features. Use XRPL network-specific tools and current amendment state.

### XRPL EVM Sidechain

A distinct EVM network for Solidity/Ethereum tooling. Balance/network reads and unsigned contract intent are **available**. Compilation and deployment require **external setup**; bridge transfer is **not shipped**.

### Xahau

A separate XRPL-protocol network with native XAH, Mainnet network ID `21337`, Testnet network ID `21338`, and Hooks. XRPL-Hermes provides **available** `HookOn` calculation and validated installed-chain reads. Compilation and deployment require **external setup**. See `references/xahau-hooks.md`.

### Flare and Songbird

Separate EVM-family networks. FTSO and cross-chain systems have their own contracts, feed IDs, finality, and governance. Use only current on-chain/read evidence; do not infer a direct XRPL route.

### Axelar

An external cross-chain system. Hermes exposes public status lookups only. It does not certify or build an asset route.

### Arweave

An external storage network. Hermes estimates public gateway pricing only. It does not upload, fund, or sign storage transactions.

### Evernode

No Evernode command is shipped. See `knowledge/54-xrpl-evernode-hosting.md` for the integration boundary.

## Capability labels

- **Available:** shipped and reachable on its documented surface.
- **External setup:** requires a user wallet, credentials, toolchain, or third-party service.
- **Not shipped:** no supported runnable workflow.

## Current command routing

```bash
# XRPL L1
python3 scripts/xrpl_tools.py server-info
python3 scripts/xrpl_tools.py account rADDRESS
python3 scripts/xrpl_tools.py amendments

# Xahau read-only/calculate
python3 scripts/xrpl_tools.py hooks-bitmask Payment Invoke
python3 scripts/xrpl_tools.py hooks-info rACCOUNT mainnet
python3 scripts/xrpl_tools.py hooks-info rACCOUNT testnet

# Other surfaces — treat output according to its status/source fields
python3 scripts/xrpl_tools.py evm-balance 0xADDRESS mainnet
python3 scripts/xrpl_tools.py evm-bridge mainnet
python3 scripts/xrpl_tools.py bridge-status
python3 scripts/xrpl_tools.py bridge-tx TX_HASH
python3 scripts/xrpl_tools.py flare-ftso XRP/USD
python3 scripts/xrpl_tools.py arweave-cost 1MB
```

The existence of a command does not certify a transfer, wallet, asset, contract, issuer, or production workflow.

## Wallet policy

Do not maintain a generic wallet compatibility matrix. Wallet network and transaction support changes. For each flow:

1. load current first-party wallet documentation;
2. verify package/app origin and version;
3. verify exact target network and transaction type;
4. show the fully decoded unsigned payload;
5. let the wallet keep and use the key;
6. verify the validated/finalized result independently.

Xaman Payment handoff is available only through the local CLI after configuring application credentials. It is not exposed over MCP because creating a request is an external side effect.

## Volatile data policy

Never hardcode or repeat without fresh verification:

- endpoints and faucets;
- chain/network IDs;
- bridge/gateway/door accounts;
- contract addresses and ABIs;
- token contracts, XRPL issuers, and currency codes;
- minimum transfer amounts, fees, reserves, and completion times;
- wallet compatibility;
- program/grant amounts and application status;
- decentralization, security, and trust-model claims.

Every production recommendation needs a current source, the intended network, a live probe, and clear uncertainty.

## Related files

- `SKILL.md`
- `LIMITATIONS.md`
- `knowledge/35-xrpl-full-interop.md`
- `knowledge/50-xrpl-evm-sidechain.md`
- `knowledge/51-xrpl-xahau-hooks.md`
- `knowledge/54-xrpl-evernode-hosting.md`
- `knowledge/55-xrpl-sidechain-interop.md`
- `references/`
