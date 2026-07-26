# XRPL EVM Sidechain — Advanced Operations Boundary

## Status

Balance/network reads and unsigned contract intent are **available**. Compilation, simulation, gas estimation, signing, and deployment require **external setup**. Bridge transfers are **not shipped**.

XRPL-Hermes does not handle EVM private keys, raw signing, broadcasting, deployment, bridge transfers, or relayer execution.

## Current narrow surface

- `evm-balance 0xADDRESS [mainnet|testnet]`
  - validates the EVM address and network;
  - reads a live balance and chain ID;
  - surfaces JSON-RPC errors.
- `evm-bridge [mainnet|testnet]`
  - verifies configured RPC identity, observed chain ID, and latest block;
  - **does not verify a bridge route**.
- `evm-contract ...`
  - emits an available unsigned contract intent;
  - rejects malformed address, bytecode, gas, network, and ABI misuse;
  - does not provide compilation, simulation, gas estimation, or deployment proof.

Current configured identities:

| Network | Chain ID | RPC |
|---|---:|---|
| Mainnet | `1440000` | `https://rpc.xrplevm.org` |
| Testnet | `1449000` | `https://rpc.testnet.xrplevm.org` |

Always verify the observed chain ID live before wallet handoff.

## External-wallet workflow

A future deployment flow must:

1. compile and encode constructor arguments with a current audited EVM toolchain;
2. verify bytecode and source/build provenance;
3. call `eth_estimateGas` and simulate where supported;
4. preview chain ID, sender, value, calldata and fees;
5. let the user's external wallet sign;
6. wait for finalized receipt and verify runtime bytecode/contract state.

No private key should enter Hermes, examples, logs, or MCP calls.

## Bridge exclusion

RPC health is not bridge health. Do not infer gateway contracts, supported assets, minimums, fees, liquidity, pause state, or recovery behavior from block height or chain registration. Transfer support remains unavailable until a first-party-schema Testnet round trip and recovery test pass.

## Official source

- https://docs.xrplevm.org/
