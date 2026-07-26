# MetaMask and XRPL EVM — External Wallet Boundary

## Status

MetaMask is an external EVM wallet. XRPL-Hermes does not access its private key, seed phrase or local storage and does not certify contract deployment or bridge transfers.

## Network checks

| Network | Configured chain ID | RPC |
|---|---:|---|
| Mainnet | `1440000` | `https://rpc.xrplevm.org` |
| Testnet | `1449000` | `https://rpc.testnet.xrplevm.org` |

Before requesting a wallet action:

1. query live `eth_chainId`;
2. compare it with the intended network;
3. show sender, destination/creation intent, native value, calldata and estimated fee;
4. request explicit user approval in MetaMask;
5. verify the finalized receipt and resulting state independently.

## Current Hermes posture

- `evm-balance`: experimental read-only evidence.
- `evm-bridge`: RPC identity/latest block only; no bridge certification.
- `evm-contract`: experimental unsigned intent only; no compile/simulation/gas/deployment proof.

The former `.env` private-key, Hardhat account-array, Foundry `--private-key`, and `ethers.Wallet` examples were removed. Use an injected wallet/provider or user-owned hardware/software signer; never route key material through Hermes.

## Bridge exclusion

Do not ask MetaMask to execute a bridge based on generic patterns. Require current first-party route/contracts/assets/fees/recovery evidence and Testnet proof.

Official source: https://docs.xrplevm.org/

Reviewed: **2026-07-26**.
