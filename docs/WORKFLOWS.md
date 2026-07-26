# Capability map

This page maps shipped capabilities to commands. If a command is not listed by the CLI or `xrpl_list_commands`, it is not a product feature.

## XRPL L1

| Capability | Commands |
|---|---|
| Accounts and ledger | `account`, `balance`, `account_objects`, `account-tx`, `ledger`, `ledger-entry`, `server-info`, `tx-info`, `decode`, `subscribe` |
| Payments and DEX | `build-payment`, `build-cross-currency-payment`, `path-find`, `build-trustset`, `trustlines`, `build-offer`, `book-offers` |
| Account control | `build-account-set`, `build-account-delete`, `build-set-regular-key`, `build-deposit-preauth`, `build-signer-list-set`, `build-ticket-create` |
| Escrow/checks/channels | `build-escrow-*`, `build-check-*`, `build-paychannel-*` |
| NFTs | `nft-info`, `nft-offers`, `build-nft-*` |
| AMM | `amm-info`, `build-amm-*` |
| Tokens and compliance | `build-clawback`, `build-mpt-*`, `build-credential-*`, `build-set-oracle`, `token-intel` |
| Network capability | `amendments`, `amendment`, `amendment-status` |
| Address validation | `validate-address` |

All builders return unsigned JSON. Signing and broadcasting are performed by the user’s external wallet or signing system.

## External and adjacent networks

| Capability | Commands | Boundary |
|---|---|---|
| Xaman Payment handoff | `xaman-payload` | Local CLI only; requires `XUMM_API_KEY` and `XUMM_API_SECRET`; creates a real request |
| Xahau inspection | `hooks-bitmask`, `hooks-info` | Calculates HookOn and reads installed Hooks; no compile/build/deploy |
| XRPL EVM Sidechain | `evm-balance`, `evm-bridge`, `evm-contract` | Available reads/unsigned intent; transfer is not shipped and deployment requires external setup |
| Flare | `flare-ftso`, `flare-price` | Read-only FTSOv2 and separately labeled market context |
| Axelar | `bridge-status`, `bridge-tx` | Registration/GMP index reads only; no route or transfer certification |
| Arweave | `arweave-cost` | Cost estimate only; no upload |

## Not shipped

- key generation or import;
- signing or broadcasting;
- Batch/XLS-56 construction;
- bridge transfer execution;
- Xahau Hook compilation or deployment;
- Arweave upload;
- x402 facilitator;
- node deployment or hosting.

## Network amendments

A public XRPL Mainnet server may know an amendment that Mainnet has not activated. This does not mean XRPL-Hermes contains a disabled implementation. Use `amendment NAME` for live network status and command discovery for product capability.

## Guides

- Operation flows: [`skills/`](../skills/)
- Knowledge: [`knowledge/`](../knowledge/)
- Reference cards: [`references/`](../references/)
- MCP setup: [`MCP-CLIENTS.md`](MCP-CLIENTS.md)
