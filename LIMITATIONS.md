# Limitations

xrpl-hermes is a KNOWLEDGE + TOOLKIT, not a runtime or hosting platform.

## What this is NOT
- ❌ Not a blockchain node — use rippled/Clio for that
- ❌ Not a wallet — use Xaman, Crossmark, or MetaMask
- ❌ Not a transaction broadcaster — you need an XRPL node for that
- ❌ Not an EVM runtime — use Foundry/Hardhat for that
- ❌ Not a hosted API — use XRPSCAN or xrpl.to for that

## What this IS
- ✅ 73 commands for building signer-ready XRPL transactions, checking live amendments, and querying ecosystem context
- ✅ 65 knowledge files covering the full XRPL ecosystem
- ✅ An MCP server so any agent (Hermes, OpenClaw, Claude Code, Cursor) can use all of the above
- ✅ Reference implementations and patterns
- ✅ CLI-first, works in any environment

## Honest coverage notes
- Axelar and Arweave commands are read-only: `bridge-status`/`bridge-tx` inspect public status APIs, and `arweave-cost` estimates storage cost. They do not execute bridges, upload data, or touch keys.
- `flare-price` uses a public price API fallback and is labeled as such; use `flare-ftso` for direct read-only FTSOv2 `eth_call` lookups.
- `hooks-bitmask` calculates Xahau `HookOn` bitmasks, but builders should still verify transaction-type coverage against current Xahau docs before production use.
- Never put a seed in a prompt, chat, or CLI argument. Builders emit unsigned, signer-ready JSON only — see `SECURITY.md`.
