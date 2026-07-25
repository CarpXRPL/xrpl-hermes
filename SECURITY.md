# Security Policy

## The rules, in plain English

1. **No secrets in this toolkit.** Nothing here needs your seed or private key, and nothing here asks for one. If a fork or wrapper of this project asks for a seed, treat it as hostile.
2. **No seeds in prompts.** Never paste a seed, secret key, or mnemonic into an AI chat, agent prompt, or MCP tool call. Agents using xrpl-hermes research and build — they must never hold signing power.
3. **Signer-ready JSON only.** Transaction builders emit unsigned JSON. You review it and sign it in your own wallet (Xaman, Crossmark, hardware-backed signer). The `submit` command is for advanced users with *already-signed* blobs only.

> For the full transaction-safety ruleset every value transfer follows — the 8 **Safety rules** covering source/destination tags, memos, mainnet approval, autofill, and amount handling — see the canonical **Safety rules** block in `SKILL.md`. The points above are consistent with it.

## The agent boundary (MCP)

The local CLI and the MCP agent surface are deliberately not the same surface.

| Surface | Count | Contents |
|---|---:|---|
| Local developer CLI (`python3 -m scripts.xrpl_tools`) | 72 | Every registered command |
| MCP-safe (`xrpl_run`) | 67 | Read-only live queries and unsigned, signer-ready builders |
| Denied over MCP — local CLI only | 5 | `wallet-generate`, `wallet-from-seed`, `submit`, `submit-multisigned`, `xaman-payload` |

`scripts/mcp_server.py` enforces a **positive allowlist with default-deny**. The rules:

1. **Custody never crosses the boundary.** `wallet-generate` emits a secret seed and `wallet-from-seed` consumes one, so neither is reachable by an agent. Key material stays on the operator's machine, in the operator's shell.
2. **Broadcast never crosses the boundary.** `submit` and `submit-multisigned` push signed material to a live network. An agent can build the transaction; only you can send it.
3. **External signing requests never cross the boundary.** `xaman-payload` creates a real signing request in someone's wallet — a human-approval action, not an agent action.
4. **Denial happens before execution.** A denied command is refused before any subprocess is spawned. It never runs, and no MCP response can contain a seed. The refusal tells you the local CLI invocation to use instead.
5. **Default-deny covers the future.** Anything not on the allowlist — including commands added in later releases — is denied until a maintainer classifies it. A new secret-touching command is therefore safe on arrival rather than exposed by oversight. `tests/test_mcp_server.py` fails the build if the allowlist and deny-list ever stop exactly covering the dispatcher.

If a fork exposes `wallet-generate`, `wallet-from-seed`, `submit`, `submit-multisigned`, or `xaman-payload` over MCP, that is a downgrade of this boundary — treat it as untrusted.

## Private Keys & Seeds

This project's build-* commands generate **unsigned JSON** client-side — no keys needed.

The optional `wallet-generate` and `wallet-from-seed` commands are **local developer utilities** that create or derive wallets entirely on your machine. They do not transmit seeds anywhere, and they are not exposed over MCP — see *The agent boundary* above.

⚠️ **CLI arguments can be captured in shell history or process listings.** Never pass production seeds as command-line arguments. For production, use `wallet-from-seed` in an interactive script that reads from an env var or file, or sign transactions externally with Xaman/Crossmark.

## API Keys

Any API keys you configure (`XRPLSCAN_API_KEY`, `XRPL_TO_API_KEY`, `XRPL_PRIVATE_RPC`) are stored in your environment only and never logged or transmitted outside of direct API calls.

## Reporting

Report vulnerabilities by opening a GitHub Issue tagged `security`.
