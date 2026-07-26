# XRPL EVM Sidechain — Quick Boundary

## Network identity

| Network | Configured chain ID | RPC |
|---|---:|---|
| Mainnet | `1440000` | `https://rpc.xrplevm.org` |
| Testnet | `1449000` | `https://rpc.testnet.xrplevm.org` |

Always compare configured and observed chain IDs.

## Capability status

- Balance/network reads: **Available**.
- Unsigned contract intent: **Available**.
- Compile, constructor encoding, simulation and gas estimation: **External setup**.
- Signing/submission: **External setup**.
- Deployment verification: **Not shipped**.
- XRPL L1 ↔ EVM transfer: **Not shipped**.

```bash
python3 scripts/xrpl_tools.py evm-balance 0x1111111111111111111111111111111111111111 mainnet
python3 scripts/xrpl_tools.py evm-bridge mainnet
```

`evm-bridge` verifies RPC identity and latest block only and must report `BridgeCertified: false`.

Never provide a private key to Hermes. Require decoded wallet preview and finalized receipt/runtime-code verification for any externally executed deployment.

Official source: https://docs.xrplevm.org/
