# Arweave Storage — Complete Reference

## Overview
Arweave is a decentralized, permanent data storage network. Data stored once is stored forever. Uses a blockweave structure (unlike blockchain) with endowment-based storage fees. Perpetual storage funded by a single upfront fee invested in an endowment.

## Architecture
Blockweave type: Proof of Access consensus. Miners store random previous blocks AND new blocks. Storage endowment fund is invested, returns pay for ongoing storage. Data is replicated across nodes redundantly.

## Key Concepts
- **Transaction**: Stores data permanently. Single fee covers storage forever.
- **Wallet**: Arweave wallet (JWK file) or ArConnect browser extension.
- **AR Token**: Native token. Used for storage fees, staking, mining rewards.
- **Permaweb**: Decentralized web hosted on Arweave. Sites live forever.
- **Gateway**: Access Arweave data via HTTP gateways (arweave.net, arweave.dev).

## SmartWeave Contracts
Smart contracts on Arweave. Lazy-evaluated: each node evaluates contract state independently. Supports JavaScript (WASM). Used for: tokens (Verto, everPay), NFTs (Koii), social (Mirror.xyz).

## Bundlr Network
Scaling solution for Arweave. Bundles many small uploads into single Arweave tx. Supports multiple tokens for payment (ETH, SOL, MATIC, AR). Faster confirmations, lower fees.

## XRPL Integration
- Evernode: Decentralized hosting on XRPL using Arweave for persistent data.
- NFTs: XLS-20 NFT metadata stored on Arweave (immutable URIs).
- Data anchoring: XRPL tx hashes stored on Arweave for permanent record.
- Web hosting: XRPL project sites hosted on permaweb.

## Use Cases
- Permanent XRPL document storage (legal, compliance)
- NFT metadata and asset storage
- dApp frontend hosting (unchangedable, DDo S-resistant)
- Data anchoring and timestamping
- Censorship-resistant publishing

## Resources
- Arweave: arweave.org
- Gateway: arweave.net
- ViewBlock explorer: viewblock.io/arweave
- Bundlr: bundlr.network
- Evernode: evernode.io
