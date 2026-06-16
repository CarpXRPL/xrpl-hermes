# Freshness / Update Flow — "update XRPL-Hermes"

The playbook to run when the user says **"update it"**, "do a freshness pass", or "is this still
current?". Goal: refresh stale-able facts from authoritative sources, **never** invent them, and
leave the repo green and version-synced. This operationalizes
`knowledge/65-agent-freshness-and-source-policy.md` (live ledger > official docs > repo > claims).

> Golden rule: produce an **audit report first, edit second, verify third, commit last.** Do not
> edit a single doc until the audit report below is written.

## 1. Gather (sources to check, with how)

Check every source; record the result (value + date) even when nothing changed.

| Source | How to check | What it informs |
|---|---|---|
| rippled releases | `https://github.com/XRPLF/rippled/releases` (latest tag, date, GPG/key notes, amendment changes) | server version notes, amendment catalog, node-operator guidance |
| Live mainnet build | `python3 -m scripts.xrpl_tools server-info` → `BuildVersion` | what mainnet actually runs *now* (often trails the latest release) |
| Live amendments | `python3 -m scripts.xrpl_tools amendments` and `amendment NAME` | enabled/supported/vetoed truth — a new release's amendments read `UnknownAmendment` until mainnet lists them |
| xrpl.org docs | official docs for any feature you're about to claim (agents, payments, amendments) | protocol behavior, agent-skill patterns |
| xrpl.js (TS/JS SDK) | `npm view xrpl version` (+ `dist-tags`) | `knowledge/31`, `examples/js`, "choose your stack" |
| xrpl-py (Python SDK) | `https://pypi.org/project/xrpl-py/` (or `pip index versions xrpl-py`) | `knowledge/30`, `pyproject.toml` dependency pin |
| x402 / t54 | `https://xrpl.org/docs/agents/agentic-payments-x402/`, `https://xrpl-x402.t54.ai` | `references/x402-payments.md` |
| Ecosystem refs | Xahau, XRPL EVM Sidechain, Axelar, Flare, Arweave official docs/explorers | the `46–55` knowledge files and matching reference cards |

Verification discipline for each fact:
- Prefer a **non-fast-model** confirmation for any specific name/number (release body, npm/PyPI, live
  tool) over a summarizer's paraphrase. If two summaries disagree, fetch the primary source verbatim
  or omit the disputed detail.
- Anchor load-bearing conclusions on the most robust observation available (e.g. "mainnet is still on
  build X" from live `server-info`), not on a freshly-released, not-yet-propagated detail.

## 2. Audit report (write this before editing)

Produce a short report — `.hermes-*.md` scratch files are gitignored, or print inline — listing, per
source: **current repo claim → newly verified value → file:line to change (or "no change")**. Flag any
claim you could *not* verify; do not "fix" it by guessing. Nothing gets edited until this exists.

## 3. Edit (only what the audit found stale)

- Update the date-stamped status lines (`references/amendments.md`, `knowledge/37`, QUICKSTART
  server-info note) with **"checked live YYYY-MM-DD via <command>"** phrasing.
- Keep neutral, open-source positioning; keep honest labels (CLI / live tool / ref / pattern / roadmap).
- Do **not** add an amendment name→ID to `scripts/tools/_shared.py` unless you have the real feature ID
  from a primary source — a fabricated hash is worse than `UnknownAmendment`.
- Bump the SDK pins only after confirming compatibility (`pyproject.toml` `xrpl-py`, `examples/js/package.json` `xrpl`).

## 4. Verify (all must pass before commit)

```bash
python3 -m pytest -q
python3 scripts/dev_test_matrix.py            # regenerates AUDIT-tool-matrix.md (commit the diff)
python3 scripts/audit_project_quality.py      # no-seeds, neutral-language, command-count, version-sync, currency-literals
python3 -m scripts.xrpl_tools server-info     # live reachability + current BuildVersion
# JS lane, if touched:
cd examples/js && node --check *.js && npm install && node build-xrp-payment.js && cd ../..
# MCP stdio smoke: initialize -> tools/list -> a real xrpl_run (e.g. validate-address)
```

Scan the diff for: decodable seeds, fabricated numbers, hostile/competitor wording, and any "shipped"
claim that is really a roadmap item.

## 5. Version bump + record + ship

1. Bump the patch version in **four** places (the audit's `version-sync` check enforces agreement):
   `pyproject.toml`, `SKILL.md` frontmatter, `SERVER_INFO` in `scripts/mcp_server.py`, and a new
   top entry in `CHANGELOG.md`.
2. CHANGELOG entry header: `## vX.Y.Z — summary — <Audited tag> (YYYY-MM-DD)`; list Added / Changed /
   Fixed / **Verified** with the live-check dates and exact results.
3. Commit with the repo's `vX.Y.Z: summary` message style; push `origin main`. Fast-forward any local
   mirror checkout if present.

See also: `docs/DEVELOPERS.md` (release flow), `knowledge/65-agent-freshness-and-source-policy.md`.
