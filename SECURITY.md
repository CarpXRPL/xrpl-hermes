# Security policy

## Custody boundary

XRPL-Hermes reads public state and builds unsigned transaction JSON. It does not implement wallet generation, seed import, signing, or transaction broadcasting.

- Never put a seed, private key, mnemonic, recovery phrase, or signing secret in a prompt, tool call, CLI argument, log, or repository file.
- Review every unsigned transaction before sending it to a user-controlled wallet or signing system.
- Verify the network, complete addresses, asset, amount, tags, memos, fee policy, and consequences before authorization.
- Treat wallet approval or a provider callback as provisional. Verify the transaction hash, `validated: true`, and final XRPL result independently.
- New value-moving flows are Testnet-first. Mainnet activity requires deliberate authorization outside the builder layer.

## Tool surfaces

| Surface | Count | Contents |
|---|---:|---|
| Local CLI | 68 | 67 reads/unsigned builders plus local Xaman Payment handoff |
| MCP | 67 | Reads and unsigned builders only |
| Local-only | 1 | `xaman-payload`, because it creates a real external wallet request |

The MCP server uses a positive allowlist. New commands are unavailable over MCP until explicitly classified.

`xaman-payload` accepts unsigned XRPL L1 Payment intent only. It rejects key-material fields, signed payloads, Xahau payloads, and non-Payment transaction types. A returned payload URL or wallet approval is not ledger finality.

## Secrets and API credentials

- `XRPL_PRIVATE_RPC` is sent only to the configured RPC endpoint.
- `XUMM_API_KEY` and `XUMM_API_SECRET` are read only by the local Xaman helper.
- Keep credentials out of source control, chat, browser code, screenshots, and MCP configuration.
- Rotate credentials immediately if exposed.

## Reporting vulnerabilities

Report vulnerabilities privately through [GitHub Security Advisories](https://github.com/CarpXRPL/xrpl-hermes/security/advisories/new). Do not open a public issue for an undisclosed vulnerability.
