# XRPL-Hermes v1.9.0 announcement draft (not posted)

Neutral announcement draft for a forum / social / README blurb. Every claim below is verifiable from
the repo. **Do not post automatically** — this is a draft for a human to review, edit, and publish.

---

## Short version

**XRPL-Hermes** is an open-source, self-hostable XRPL agent stack. The agent researches the ledger,
builds **unsigned, signer-ready** transactions, explains the risks, and attributes/monitors activity —
then hands off to your wallet to sign. Keys stay with you.

- **72 registered CLI commands + a default-deny MCP server** — MCP permits 67 of them; five sensitive registrations are refused before execution.
- **Signer-separated by design** — `build-*` commands emit unsigned JSON; authorization stays in a separately accepted user-controlled signer. No builder asks for a seed.
- **Python *and* JavaScript** — runnable `xrpl-py` and `xrpl.js` examples; pick the stack you already use.
- **Live XRPL knowledge** — 65 knowledge files + 15 reference cards, with live amendment/version checks
  instead of stale claims.
- **Agentic-payment foundations** — XRP/RLUSD unsigned builders, `SourceTag`/Memos/WebSocket attribution and monitoring. x402 remains an experimental external integration plan.
- **MIT licensed**, self-hosted, with dual-version tests, wheel acceptance, custody-boundary tests and offline CLI checks in CI.

It is **not** a wallet, a seed-custody service, or an auto-signer. The agent builds; your wallet signs.

Repo: https://github.com/CarpXRPL/xrpl-hermes

---

## Notes for the human posting this

- Keep it neutral — describe what it does, don't compare it to other tools.
- Don't add metrics or claims you can't back from the repo (no "fastest", no token-price talk).
- If you cite a version, cite it the day you post and link the release.
