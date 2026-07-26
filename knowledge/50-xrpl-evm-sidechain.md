# XRPL EVM Sidechain — Network and Capability Card

## Network separation

The XRPL EVM Sidechain is an EVM-compatible network adjacent to XRPL L1. It is not XRPL L1 and does not share XRPL account addresses, transaction serialization, or finality receipts.

| Network | Configured chain ID | Configured RPC |
|---|---:|---|
| Mainnet | `1440000` | `https://rpc.xrplevm.org` |
| Testnet | `1449000` | `https://rpc.testnet.xrplevm.org` |

Treat these as configuration values that must be checked against the live RPC and current official documentation before use.

## XRPL-Hermes release posture

| Capability | Status |
|---|---|
| Address/network validation | Implemented |
| Live balance + observed chain ID | Experimental read-only |
| RPC identity/latest block | Experimental read-only |
| Contract deployment intent | Experimental build-only |
| Compile/constructor encoding | External dependency |
| Gas estimation/simulation | Not implemented |
| Signing/submission | External wallet only |
| Receipt/runtime verification | Not implemented |
| XRPL L1 ↔ EVM transfer | Quarantined |

## Safe commands

```bash
python3 scripts/xrpl_tools.py evm-balance 0x1111111111111111111111111111111111111111 mainnet
python3 scripts/xrpl_tools.py evm-bridge mainnet
```

Despite its historical command name, `evm-bridge` reports only RPC/network identity. It must return `BridgeCertified: false`.

`evm-contract` produces an explicitly labeled unsigned planning envelope. A valid-looking envelope is not evidence that bytecode compiles, constructor arguments are correct, gas is sufficient, or deployment will succeed.

## Non-custodial boundary

- Never request or load an EVM private key.
- Never include raw signing/broadcast examples in this knowledge base.
- Use an external wallet with decoded chain/value/calldata preview.
- Start on Testnet.
- Verify a finalized receipt and deployed runtime code independently.

## Bridge boundary

Do not use a generic lock/mint pattern, placeholder gateway, hardcoded asset list, or inferred memo. Bridge integrations require current first-party schemas, current contracts, asset support, fees/minimums, pause state, recovery behavior, and a reproduced Testnet round trip.

## Official source

- https://docs.xrplevm.org/

Source review date: **2026-07-26**.
