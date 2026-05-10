# Security Policy

## Private Keys & Seeds

This project's build-* commands generate **unsigned JSON** client-side — no keys needed.

The optional `wallet-generate` and `wallet-from-seed` commands are **local developer utilities** that create or derive wallets entirely on your machine. They do not transmit seeds anywhere.

⚠️ **CLI arguments can be captured in shell history or process listings.** Never pass production seeds as command-line arguments. For production, use `wallet-from-seed` in an interactive script that reads from an env var or file, or sign transactions externally with Xaman/Crossmark.

## API Keys

Any API keys you configure (`XRPLSCAN_API_KEY`, `XRPL_TO_API_KEY`, `XRPL_PRIVATE_RPC`) are stored in your environment only and never logged or transmitted outside of direct API calls.

## Reporting

Report vulnerabilities by opening a GitHub Issue tagged `security`.
