# Limitations

xrpl-hermes is a KNOWLEDGE + TOOLKIT, not a runtime or hosting platform.

## What this is NOT
- ❌ Not a blockchain node — use rippled/Clio for that
- ❌ Not a wallet — use Xaman, Crossmark, or MetaMask
- ❌ Not a transaction broadcaster — you need an XRPL node for that
- ❌ Not an EVM runtime — use Foundry/Hardhat for that
- ❌ Not a hosted API — use XRPSCAN or xrpl.to for that

## What this IS
- ✅ 67 tools for building XRPL transactions, checking live amendments, and querying ecosystem context
- ✅ 65 knowledge files covering the full XRPL ecosystem
- ✅ An MCP server so any agent (Hermes, OpenClaw, Claude Code, Cursor) can use all of the above
- ✅ Reference implementations and patterns
- ✅ CLI-first, works in any environment

## Honest coverage notes
- Axelar and Arweave are covered by knowledge files and reference cards only — no CLI commands execute bridges or uploads. See the per-ecosystem labels in `docs/WORKFLOWS.md`.
- `flare-price` uses a public price API fallback and is labeled as such — it is not on-chain FTSO proof.
- `hooks-bitmask` is intentionally disabled (emits a warning) until a correct 256-bit `HookOn` implementation lands.
- Never put a seed in a prompt, chat, or CLI argument. Builders emit unsigned, signer-ready JSON only — see `SECURITY.md`.
