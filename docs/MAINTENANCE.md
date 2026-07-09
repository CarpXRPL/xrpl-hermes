# Maintenance — keeping XRPL-Hermes current and honest

XRPL-Hermes ships markdown knowledge plus live tools, so the load-bearing facts (amendment status,
fees, versions, endpoints) must be **verified live, not assumed**. This is the freshness cadence and
the exact commands to run. For the pre-release verification gate and the version-bump steps, see
[`DEVELOPERS.md`](DEVELOPERS.md) (*Testing and verification*, *Release flow*) — not repeated here.

Source-of-truth policy: live ledger > official docs > this repo > claims
([`../knowledge/65-agent-freshness-and-source-policy.md`](../knowledge/65-agent-freshness-and-source-policy.md)).

## Freshness cadence

| When | Check | How | If it changed, update |
|---|---|---|---|
| Weekly | Live mainnet build + amendments | `python3 scripts/xrpl_tools.py server-info` · `… amendments` | `knowledge/37-xrpl-amendments.md`, `references/amendments.md` (re-date the live-checked line) |
| Weekly | `xrpl.js` latest | `npm view xrpl version` vs `examples/js/package.json` | the pin + `examples/js/README.md` if the major moved |
| Weekly | `xrpl-py` latest | `pip index versions xrpl-py` (or PyPI) vs `pyproject.toml` | the pin in `pyproject.toml` / `requirements.txt` |
| Monthly | `xrpld`/`rippled` releases | https://github.com/XRPLF/rippled/releases | `knowledge/37`, `references/amendments.md`, `deploy/README.md` |
| Monthly | Known Amendments / docs index | https://xrpl.org/known-amendments.html · https://xrpl.org/llms.txt | the amendment notes + any cited doc |
| Monthly | Agent / x402 docs + T54 facilitator | https://xrpl.org/docs/agents/getting-started-with-agentic-transactions/ · T54 facilitator docs | `references/x402-payments.md`, `references/agentic-payments.md`, `references/track-agent-behavior.md` |
| As referenced | Xaman, XRPL EVM, Axelar, Xahau, Flare | their official docs/releases | the matching `knowledge/` + `references/` cards |

Rule: a check is only "done" when the repo line is re-dated against a live result. Never copy a
"latest = X" number into prose that will rot — cite the command and the date you ran it.

## Verify before any commit/release

The gate (full detail in [`DEVELOPERS.md`](DEVELOPERS.md#testing-and-verification)):

```bash
python3 scripts/audit_project_quality.py      # no-seeds, neutral-language, command-count, version-sync, currency-literals
python3 -m pytest -q                           # offline-safe regression + MCP end-to-end
python3 scripts/dev_test_matrix.py             # live, every command → regenerates AUDIT-tool-matrix.md
node --check examples/js/*.js                  # syntax-check any changed JS
git diff --check                               # whitespace / conflict markers
# MCP smoke: initialize must report the current version
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18"}}' | python3 scripts/mcp_server.py
```

`dev_test_matrix.py` rewrites `AUDIT-tool-matrix.md` with fresh timestamps/live output. If the command
set did **not** change, that diff is drift — revert it (`git checkout -- AUDIT-tool-matrix.md`) rather
than commit noise. Stage real files explicitly; don't `git add -A` the regenerated matrix.

## Safety invariants (never regress)

- Builders emit **unsigned, signer-ready JSON only** — no builder accepts, derives, or stores a seed.
  (Autonomous mainnet execution, if any, lives in a separate user-configured policy-gated signer/executor
  layer — never a builder.)
- No seeds/private keys in committed files (the `no-seeds` audit gate fails the build on any decodable one).
- No fabricated live data: a failed lookup names the failing endpoint; it never guesses a number.
- Amendment-gated builders check live mainnet status and print an explicit build-only note.
