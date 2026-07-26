# XRPL EVM Sidechain — Quick Boundary

## Network identity

| Network | Configured chain ID | RPC |
|---|---:|---|
| Mainnet | `1440000` | `https://rpc.xrplevm.org` |
| Testnet | `1449000` | `https://rpc.testnet.xrplevm.org` |

Always compare configured and observed chain IDs.

## Capability status

- Balance/network reads: **experimental read-only**.
- Contract intent: **experimental build-only**.
- Compile, constructor encoding, simulation and gas estimation: **external dependency/not implemented**.
- Signing/submission: **external wallet only**.
- Deployment verification: **not implemented**.
- XRPL L1 ↔ EVM transfer: **quarantined**.

```bash
python3 scripts/xrpl_tools.py evm-balance 0x1111111111111111111111111111111111111111 mainnet
python3 scripts/xrpl_tools.py evm-bridge mainnet
```

`evm-bridge` verifies RPC identity and latest block only and must report `BridgeCertified: false`.

Never provide a private key to Hermes. Require decoded wallet preview and finalized receipt/runtime-code verification for any externally executed deployment.

Official source: https://docs.xrplevm.org/

Reviewed: **2026-07-26**.
