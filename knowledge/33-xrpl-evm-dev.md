# XRPL EVM Development — Safe Planning Guide

## Status

**Planning and read-only inspection only.** The previous guide embedded private-key environment patterns, direct Hardhat/Foundry deployment commands, raw bridge payments and speculative contracts. Those runnable examples were removed.

## Current network configuration

| Network | Chain ID | RPC |
|---|---:|---|
| Mainnet | `1440000` | `https://rpc.xrplevm.org` |
| Testnet | `1449000` | `https://rpc.testnet.xrplevm.org` |

Confirm these against the live RPC and current official documentation before use.

## Development workflow

1. Specify the contract, invariants, upgrade/admin model and economic risks.
2. Compile with a pinned current Solidity toolchain.
3. Run unit, fuzz and static-analysis tests locally.
4. Deploy to a local chain, then XRPL EVM Testnet through a user-controlled wallet.
5. Verify chain ID, sender, value, calldata, gas estimate and fee before signing.
6. Verify the finalized receipt, runtime bytecode and initialized state.
7. Perform security review before Mainnet.

XRPL-Hermes may help produce and review source, tests and an unsigned intent. It does not take a private key, sign, broadcast or currently certify deployment.

## Tool posture

- `evm-balance`: experimental read-only balance/network evidence.
- `evm-bridge`: RPC identity/status only; not bridge readiness.
- `evm-contract`: experimental build-only intent; not compiled/simulated/deployed proof.

## Bridge exclusion

Do not use generic door accounts, destination-tag mappings, placeholder ABIs, hardcoded assets or inferred memo schemas. Any XRPL L1 ↔ EVM transfer requires current first-party Axelar/ITS evidence and a reproduced Testnet round trip.

## External wallet boundary

The user's wallet or independent signer owns the key and presents a decoded transaction. Hermes verifies network and finalized result. No private key belongs in `.env` examples, CLI arguments, prompts, logs or MCP.

## Official source

- https://docs.xrplevm.org/

Reviewed: **2026-07-26**.
