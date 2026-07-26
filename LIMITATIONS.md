# Limitations

XRPL-Hermes is a knowledge, read, and unsigned-build layer. It is not a wallet, signer, broadcaster, node, hosted API, or custody service.

## Available surfaces

- **67 CLI + MCP commands:** live reads and unsigned transaction builders.
- **1 local-only command:** `xaman-payload`, which creates a Payment request after local validation and requires Xaman application credentials.
- **Packaged guidance:** XRPL knowledge, references, and workflow files.

## Not implemented

- wallet generation, seed import, private-key handling, signing, or transaction broadcast;
- XRPL Batch/XLS-56 construction;
- Xahau Hook compilation, transaction construction, signing, or deployment;
- XRPL EVM/Axelar bridge transfer construction or execution;
- Arweave uploads;
- x402 facilitation or settlement;
- rippled/Clio deployment or managed hosting.

## Narrow integrations

- `evm-balance` and `evm-bridge` provide **available** read-only XRPL EVM checks. `evm-contract` provides an **available** unsigned intent; compilation, simulation, gas estimation, signing, and deployment require **external setup** or are **not shipped**.
- `bridge-status` reads Axelar registration metadata. `bridge-tx` searches the GMP index. Neither proves a supported transfer route.
- `flare-ftso` performs read-only FTSOv2 calls. `flare-price` is separately labeled market context.
- `arweave-cost` returns a point-in-time public-gateway estimate. It does not upload or guarantee retrieval.
- `hooks-bitmask` calculates HookOn. `hooks-info` reads validated Xahau Hook chains. Neither deploys Hooks.
- `token-intel` is an XRPL ledger snapshot with explicit missing-data fields, not identity verification or financial advice.

## Amendment status is not product support

Public XRPL Mainnet servers can know an amendment that Mainnet has not activated. That protocol state does not create an XRPL-Hermes feature. Shipped capabilities are the commands returned by the CLI and `xrpl_list_commands`.

Current fees, reserves, amendment state, balances, liquidity, provider schemas, and network endpoints must be checked live before use.
