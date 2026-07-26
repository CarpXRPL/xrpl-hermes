# XRPL EVM Sidechain — Advanced Operations Boundary

## Status

**Experimental/read-only plus build-only planning.** XRPL-Hermes does not currently provide a transaction serializer, simulator, gas estimator, signer, broadcaster, deployment verifier, relayer, or certified bridge transfer for the XRPL EVM Sidechain.

The former advanced guide contained private-key loading, raw signing/broadcasting, placeholder contracts, and speculative bridge/relayer flows. Those examples were removed.

## Current narrow surface

- `evm-balance 0xADDRESS [mainnet|testnet]`
  - validates the EVM address and network;
  - reads a live balance and chain ID;
  - surfaces JSON-RPC errors.
- `evm-bridge [mainnet|testnet]`
  - verifies configured RPC identity, observed chain ID, and latest block;
  - **does not verify a bridge route**.
- `evm-contract ...`
  - emits an explicitly experimental unsigned deployment intent;
  - rejects malformed address, bytecode, gas, network, and ABI misuse;
  - is not serialization-, simulation-, gas-, or deployment-certified.

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

RPC health is not bridge health. Do not infer gateway contracts, supported assets, minimums, fees, liquidity, pause state, or recovery behavior from block height or chain registration. Transfer support remains quarantined until a first-party-schema Testnet round trip and recovery test pass.

## Official source

- https://docs.xrplevm.org/

Source review date: **2026-07-26**.
