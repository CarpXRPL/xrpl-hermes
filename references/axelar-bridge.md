# Axelar Bridge — Complete Reference

## Overview
Axelar is a decentralized cross-chain communication network connecting XRPL to 50+ blockchains (Ethereum, BSC, Polygon, Avalanche, etc.). Enables token transfers and general message passing (GMP).

## Architecture
Chain A sends message to Axelar Gateway. Validators (AXL-staked, permissionless) reach consensus and relay. Chain B's Gateway verifies and executes.

## XRPL Integration
XRPL connects via Axelar's native gateway. Supports XRP and token transfers between XRPL and EVM chains. XRPL sends via Payment tx with memo. Receives via signed validator attestation.

## General Message Passing
callContract() on source chain encodes arbitrary payload. Validators relay and verify. execute() on destination chain processes payload. Enables cross-chain DeFi, NFT bridging, contract composability.

## Token Flows
Lock/burn on source chain -> mint/release on destination. Supported: wXRP, RLUSD, USDC, USDT, AXL. Fees in AXL or native gas.

## Resources
- Docs: docs.axelar.dev
- Supported chains: docs.axelar.dev/resources/mainnet
- Axelarscan: axelarscan.io
