# Security Policy

## The rules, in plain English

1. **No secrets in this toolkit.** Nothing here needs your seed or private key, and nothing here asks for one. If a fork or wrapper of this project asks for a seed, treat it as hostile.
2. **No seeds in prompts.** Never paste a seed, secret key, or mnemonic into an AI chat, agent prompt, or MCP tool call. Agents using xrpl-hermes research and build — they must never hold signing power.
3. **Signer-ready JSON only.** Transaction builders emit unsigned JSON. You review it and sign it in your own wallet (Xaman, Crossmark, hardware-backed signer). The `submit` command is for advanced users with *already-signed* blobs only.

> For the full transaction-safety ruleset every value transfer follows — the 8 **Safety rules** covering source/destination tags, memos, mainnet approval, autofill, and amount handling — see the canonical **Safety rules** block in `SKILL.md`. The points above are consistent with it.

## Private Keys & Seeds

This project's build-* commands generate **unsigned JSON** client-side — no keys needed.

The optional `wallet-generate` and `wallet-from-seed` commands are **local developer utilities** that create or derive wallets entirely on your machine. They do not transmit seeds anywhere.

⚠️ **CLI arguments can be captured in shell history or process listings.** Never pass production seeds as command-line arguments. For production, use `wallet-from-seed` in an interactive script that reads from an env var or file, or sign transactions externally with Xaman/Crossmark.

## API Keys

Any API keys you configure (`XRPLSCAN_API_KEY`, `XRPL_TO_API_KEY`, `XRPL_PRIVATE_RPC`) are stored in your environment only and never logged or transmitted outside of direct API calls.

## Reporting

Report vulnerabilities by opening a GitHub Issue tagged `security`.
