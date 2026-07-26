# Security Policy

## The rules, in plain English

1. **No secrets in supported workflows.** Two registered legacy compatibility commands can generate/accept key material, but they are quarantined, MCP-denied and must not be used by agents. No supported workflow asks for a seed/private key.
2. **No seeds in prompts.** Never paste a seed, secret key, or mnemonic into an AI chat, agent prompt, or MCP tool call. Agents using xrpl-hermes research and build — they must never hold signing power.
3. **Signer-ready JSON only.** Transaction builders emit unsigned JSON. Review it and authorize in a compatible user-owned external signer. Legacy local broadcast commands are quarantined and outside supported workflows.

> For the full transaction-safety ruleset every value transfer follows — the 8 **Safety rules** covering source/destination tags, memos, mainnet approval, autofill, and amount handling — see the canonical **Safety rules** block in `SKILL.md`. The points above are consistent with it.

## The agent boundary (MCP)

The local CLI and the MCP agent surface are deliberately not the same surface.

| Surface | Count | Contents |
|---|---:|---|
| Local developer CLI (`python3 -m scripts.xrpl_tools`) | 72 | Every registered command |
| MCP-safe (`xrpl_run`) | 67 | Read-only live queries and unsigned, signer-ready builders |
| Denied over MCP — local CLI only | 5 | `wallet-generate`, `wallet-from-seed`, `submit`, `submit-multisigned`, `xaman-payload` |

`scripts/mcp_server.py` enforces a **positive allowlist with default-deny**. The rules:

1. **Custody never crosses the boundary.** Two legacy registrations can emit/consume key material, so both are MCP-denied and quarantined from supported workflows. Do not route key material through Hermes or its CLI.
2. **Broadcast never crosses the boundary.** Legacy local broadcast registrations are MCP-denied and quarantined. Authorization/broadcast belongs to the separately accepted user-controlled external signing system.
3. **External signing requests never cross the boundary.** `xaman-payload` creates a real signing request in someone's wallet — a human-approval action, not an agent action.
4. **Denial happens before execution.** A denied command is refused before any subprocess is spawned. It never runs, and no MCP response can contain a seed. Refusals classify the boundary without recommending a sensitive local invocation.
5. **Default-deny covers the future.** Anything not on the allowlist — including commands added in later releases — is denied until a maintainer classifies it. A new secret-touching command is therefore safe on arrival rather than exposed by oversight. `tests/test_mcp_server.py` fails the build if the allowlist and deny-list ever stop exactly covering the dispatcher.

If a fork exposes `wallet-generate`, `wallet-from-seed`, `submit`, `submit-multisigned`, or `xaman-payload` over MCP, that is a downgrade of this boundary — treat it as untrusted.

## Private Keys & Seeds

This project's build-* commands generate **unsigned JSON** client-side — no keys needed.

The legacy `wallet-generate` and `wallet-from-seed` commands are quarantined compatibility surfaces.
They are denied over MCP and are not part of supported agent workflows. Hermes must not receive,
derive, print, persist or transmit key material. Use a compatible user-owned external wallet/HSM/KMS.

## API Keys

`XRPL_PRIVATE_RPC`, when deliberately configured, is sent only to that selected RPC endpoint. No
third-party explorer/token API key or route is certified by default.

## Reporting

Report vulnerabilities privately through [GitHub Security Advisories](https://github.com/CarpXRPL/xrpl-hermes/security/advisories/new). Do not open a public issue for an undisclosed vulnerability.
