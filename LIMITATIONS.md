# Limitations

xrpl-hermes is a KNOWLEDGE + TOOLKIT, not a runtime or hosting platform.

## What this is NOT
- ❌ Not a blockchain node — use rippled/Clio for that
- ❌ Not a wallet — use a compatible user-owned external wallet whose exact network and transaction support has been verified
- ❌ Not a transaction broadcaster — you need an XRPL node for that
- ❌ Not an EVM runtime — use Foundry/Hardhat for that
- ❌ Not a hosted API — any external provider requires separate current contract/security acceptance

## What this IS
- ✅ 72 commands for building signer-ready XRPL transactions, checking live amendments, and querying ecosystem context
- ✅ 65 curated knowledge files with explicit certification and external-dependency boundaries
- ✅ An MCP server so any agent (Hermes, OpenClaw, Claude Code, Cursor) can use the knowledge base and the agent-safe command subset
- ✅ Reference implementations and patterns
- ✅ CLI-first, works in any environment

## What an agent does NOT get over MCP
The MCP surface is deliberately narrower than the 72-command registered dispatcher. Sixty-seven commands are agent-safe; five sensitive registrations are refused before execution:

| Command | Classification |
|---|---|
| `wallet-generate` | Legacy/quarantined: emits key material |
| `wallet-from-seed` | Legacy/quarantined: accepts key material |
| `submit` | Legacy/quarantined: broadcasts to a live network |
| `submit-multisigned` | Legacy/quarantined: broadcasts to a live network |
| `xaman-payload` | Guarded external side effect for a locally validated XRPL L1 Payment only |

The allowlist is default-deny, so any command not classified — including future additions — is refused until a maintainer adds it. Denial happens before the command is executed. Details: `SECURITY.md`.

## Honest coverage notes
- Axelar and Arweave commands are narrow reads: `bridge-status` is registration lookup, `bridge-tx` is GMP-index search, and `arweave-cost` is a point-in-time base fee estimate. They do not certify routes/transfers, upload data, guarantee retrieval, or touch keys.
- `flare-price` uses a public price API fallback and is labeled as such; use `flare-ftso` for direct read-only FTSOv2 `eth_call` lookups.
- Xahau support is read/planning only: `hooks-bitmask` calculates legacy `HookOn`, and `hooks-info` reads validated Mainnet/Testnet Hook chains. XRPL-Hermes does not compile, serialize, build, sign, submit, or deploy Xahau transactions. Verify live transaction types and enabled amendments before use.
- Never put a seed in a prompt, chat, or CLI argument. Builders emit unsigned, signer-ready JSON only — see `SECURITY.md`.
