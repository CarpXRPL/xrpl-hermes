# Developer Guide — architecture, extending tools, MCP internals, testing

This is the advanced companion to [`CONTRIBUTING.md`](../CONTRIBUTING.md). Read this before adding a command or touching the MCP server.

## Repository layout

```
xrpl-hermes/
├── scripts/
│   ├── xrpl_tools.py        # thin CLI dispatcher — merges COMMANDS dicts, no logic
│   ├── mcp_server.py        # stdio MCP server (stdlib-only JSON-RPC 2.0)
│   ├── xrpl_streams.py      # WebSocket `subscribe` (optional, needs websockets)
│   ├── dev_test_matrix.py   # regenerates AUDIT-tool-matrix.md across all commands
│   └── tools/               # one module per domain, each exporting COMMANDS
│       ├── _shared.py       # endpoints, failover, JSON output, arg dispatch helpers
│       ├── accounts.py  payments.py  trustlines.py  dex.py  amm.py  nfts.py
│       ├── escrow.py  checks.py  paychannel.py  mpts.py  clawback.py  oracles.py
│       ├── credentials.py  batch.py  ledger.py  wallet.py  amendments.py
│       └── evm.py  xahau.py  flare.py  xaman.py
├── knowledge/               # 65 numbered deep-dive files (the agent's library)
├── references/              # 14 quick-reference cards pointing into knowledge/
├── skills/                  # multi-step workflow playbooks (token launch, AMM bot, …)
├── examples/                # runnable end-to-end scripts (Python; testnet, env-var seeds)
│   └── js/                  # runnable xrpl.js twins (build-only, no seeds) — npm install
├── tests/                   # pytest: CLI regressions, tool outputs, MCP end-to-end
├── deploy/                  # rippled/Clio docker-compose for a private node
├── SKILL.md                 # Hermes Agent master prompt (agent behavior rules live here)
└── STANDALONE.md            # in-depth CLI usage for humans (full 73-command list: SKILL.md)
```

### Dispatcher pattern

`scripts/xrpl_tools.py` imports every module in `scripts/tools/` and merges their `COMMANDS` dicts (`command-name -> zero-arg callable that reads sys.argv`). It contains no tool logic itself. The MCP server, the CLI, the dev-test matrix, and the tests all consume this single registry, so a command added to one module is automatically available everywhere.

### Dual-stack boundary (Python engine, language-neutral output)

The CLI and MCP server are **Python (`xrpl-py`) by design** — that is the engine, not a constraint on the user. The signer-ready JSON they emit is language-neutral, so the application code a user builds on top can be Python (`xrpl-py`, `knowledge/30`) **or** TypeScript/JavaScript (`xrpl.js`, `knowledge/31`). Keep both lanes first-class in docs and examples: the Python examples live in `examples/`, their build-only `xrpl.js` twins in `examples/js/`. Do **not** port the CLI/MCP server to Node.

### Networking and failover (`scripts/tools/_shared.py`)

- Default JSON-RPC endpoints: `xrplcluster.com`, then `s1.ripple.com:51234`, then `s2.ripple.com:51234`, rotated on failure.
- `XRPL_PRIVATE_RPC` (your own rippled/Clio) is prepended and takes priority when set.
- Amendment checks query `s1`/`s2` directly (full-history servers answer `feature` reliably).
- All output goes through shared helpers (`json_out`, `note_out`, `usage_out`) so every command emits machine-readable JSON plus optional `#`-prefixed human notes — keep that contract when adding commands.

### Safety invariants (do not break these)

1. `build-*` commands emit **unsigned, signer-ready JSON only**. No builder may accept, derive, or require a seed.
2. Amendment-gated builders (`MPT`, `Credential`, `Oracle`, `Batch`) check live mainnet status and print an explicit note; new builders for not-yet-enabled features must do the same.
3. No fabricated data: a failed lookup reports the failing endpoint, never a plausible guess.
4. `wallet-generate` / `wallet-from-seed` are local-only utilities and must never transmit anything.

## Adding a command (checklist)

1. **Pick or create a module** in `scripts/tools/`. New module? Export a `COMMANDS` dict and add it to the import + merge lists in `scripts/xrpl_tools.py`.
2. **Implement** using `_shared` helpers for endpoints and output. Validate args and print a `Usage:` line on bad input rather than raising.
3. **Register a safe test invocation** in the `TESTS` dict in `scripts/dev_test_matrix.py` — one that exercises the real code path without submitting a transaction or printing a seed.
4. **Add pytest coverage** in `tests/` for the output shape (see `tests/test_tool_outputs.py` for the pattern).
5. **Document it** in `STANDALONE.md` (in-depth usage) and, if user-facing, the README command-coverage table and `SKILL.md` tool table. Update the command count everywhere it appears (README, SKILL.md, LIMITATIONS.md, mcp_server docstring) — the MCP test asserts a minimum command count (`count >= 73`) — keep it in sync, so additions are cheap, removals are not.
6. **Run the verification suite** (below) and regenerate the matrix.

## MCP server internals

`scripts/mcp_server.py` is intentionally minimal (~200 lines, stdlib only):

- **Transport:** newline-delimited JSON-RPC 2.0 over stdio. Handles `initialize` (echoes the client's protocol version), `ping`, `tools/list`, `tools/call`; notifications get no response; unknown methods get `-32601`.
- **Protocol version:** `2025-06-18` by default.
- **Execution model:** `xrpl_run` shells out to `python3 -m scripts.xrpl_tools <command> [...args]` in a subprocess (`RUN_TIMEOUT_SECONDS = 90`), capturing stdout and stderr. Crashes and timeouts become `isError: true` tool results, never server death.
- **Command allowlist:** only names present in the dispatcher's `COMMANDS` registry can run — there is no arbitrary-shell surface.
- **Knowledge sandbox:** `xrpl_knowledge` resolves the path and requires it to be a `.md` under `knowledge/` or `references/`; traversal attempts are rejected (tested in `tests/test_mcp_server.py::test_mcp_rejects_bad_input`).

If you change tool schemas or add a tool, update `TOOLS`, `_call_tool`, the test's expected tool-name set, and `docs/MCP-CLIENTS.md`.

## Testing and verification

Two layers, both required before a release:

### 1. Pytest (fast, offline-safe)

```bash
python3 -m pytest -q
```

- `tests/test_cli_regressions.py` — CLI dispatch and argument regressions.
- `tests/test_tool_outputs.py` — output-shape checks for builders.
- `tests/test_mcp_server.py` — full stdio session against the real server: initialize, tools/list, a real dispatcher call, knowledge reads, and rejection of bad commands/path traversal.

CI (`.github/workflows/ci.yml`) runs pytest plus a live `server-info` on every push/PR.

### 2. Dev-test matrix (live, every command)

```bash
python3 scripts/dev_test_matrix.py
```

Runs all registered commands with safe arguments and writes [`AUDIT-tool-matrix.md`](../AUDIT-tool-matrix.md) — command, status, exit code, latency, exact argv, and a 500-char output sample (with any seed-shaped strings redacted). Pass criteria are deliberately strict:

- read commands must exit 0 with no traceback;
- `build-*` output containing an `"Error"` payload is a FAIL even at exit 0;
- dangerous commands (`submit`, `submit-multisigned`, `wallet-from-seed`) pass only by *failing safely* (usage/error text, no action);
- `subscribe` passes by starting and hitting the timeout, since it is a long-running stream.

The script exits non-zero and lists failures if anything regresses. The committed matrix is the verification record for the release — regenerate it whenever commands change, and skim the diff: latency drift is noise, but changed output samples are signal.

## Knowledge base conventions

- Files are numbered (`66-...` is next). One topic per file, `# Title` first line (the MCP index reads it), runnable code with real public endpoints.
- Date-stamp anything that can go stale (amendment status, endpoints, issuer facts) and follow `knowledge/65-agent-freshness-and-source-policy.md`: live ledger > official docs > repo > claims.
- Currency codes longer than 3 characters must appear in 160-bit hex form in any transaction JSON.
- References (`references/*.md`) are condensed cards that point at their deep file — keep them short.

## Release flow

1. All checks green: pytest, dev-test matrix 73/73 (or the new count), MCP smoke test.
2. Bump the version in **three places**: `pyproject.toml`, `SKILL.md` frontmatter, and `SERVER_INFO` in `scripts/mcp_server.py`.
3. Add a `CHANGELOG.md` entry: what was Added / Fixed / Verified, with dates on live verifications.
4. Commit with the `vX.Y.Z: summary` message format used throughout the history.
5. **Publish + repo metadata.** Push the branch, then keep the public GitHub metadata current. Describe
   XRPL-Hermes in absolute, open-source terms — what it *is*, never relative to another product:

   ```bash
   git push origin main
   # after `gh auth login`:
   gh repo edit CarpXRPL/xrpl-hermes \
     --description "Open-source XRPL agent stack: MCP tools, signer-separated transaction builders, live XRPL knowledge, Python + xrpl.js examples, x402, RLUSD, and on-ledger receipts."
   gh repo edit CarpXRPL/xrpl-hermes \
     --add-topic xrpl --add-topic xrp-ledger --add-topic mcp --add-topic ai-agents \
     --add-topic agentic-payments --add-topic x402 --add-topic xrpl-js --add-topic xrpl-py \
     --add-topic xaman --add-topic rlusd
   ```

   On WSL, if `gh auth login` can't open a browser, open `https://github.com/login/device` in Windows and
   enter the device code; if GitHub returns `slow_down`, wait a few minutes before retrying.
