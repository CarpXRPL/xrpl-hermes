# Developer guide

## Architecture

```text
scripts/xrpl_tools.py       CLI dispatcher
scripts/mcp_server.py       stdio MCP server
scripts/tools/              command modules
knowledge/                  deep topic guides
references/                 quick-reference cards
skills/                     multi-step workflows
examples/                   unsigned build and read examples
tests/                      regression and boundary tests
```

Each tool module exports a `COMMANDS` dictionary. The dispatcher merges those dictionaries. The MCP server applies a positive allowlist: 67 read/unsigned-builder commands are available, while the local Xaman request helper is excluded because it creates a real external side effect.

## Safety invariants

1. No shipped command generates, accepts, derives, stores, signs with, or broadcasts key material.
2. Every `build-*` command returns unsigned transaction JSON.
3. Current network facts come from live reads; failures report unavailable data rather than substitutes.
4. Amendment-gated builders report public XRPL Mainnet feature state before producing an intent; other target networks require a separate direct check.
5. New dispatcher commands are unavailable over MCP until explicitly classified.
6. Xaman request creation stays local-only and Payment-only.

## Adding a command

1. Add the implementation to the appropriate module under `scripts/tools/`.
2. Register it in that module’s `COMMANDS` dictionary.
3. Add a safe invocation to `scripts/dev_test_matrix.py`.
4. Add pytest coverage for validation and output shape.
5. Add the command to `_ALLOWED_COMMANDS` only if it is read-only or produces unsigned intent without external side effects.
6. Document the actual activation path in `README.md` and `docs/WORKFLOWS.md`.
7. Run the full verification suite.

Do not add roadmap items or unsupported protocol amendments to the command catalog.

## MCP server

The server uses newline-delimited JSON-RPC 2.0 over stdio and exposes:

- `xrpl_list_commands`
- `xrpl_run`
- `xrpl_knowledge_index`
- `xrpl_knowledge`

Commands execute in a subprocess with a timeout. Knowledge reads are restricted to Markdown under `knowledge/`, `references/`, and `skills/`. Unknown commands and unclassified future commands are denied before subprocess execution.

## Verification

```bash
python3 -m pytest -q
python3 scripts/dev_test_matrix.py
python3 scripts/audit_project_quality.py
python3 -m compileall -q scripts tests examples
python3 -m scripts.package_acceptance
git diff --check
```

The matrix prints a JSON summary. To produce a local detailed report without committing generated evidence:

```bash
XRPL_HERMES_MATRIX_REPORT=/tmp/xrpl-hermes-matrix.md \
  python3 scripts/dev_test_matrix.py
```

CI runs Python 3.10, 3.11, and 3.12 plus clean-wheel installation acceptance.

## Release checklist

1. Verify the exact clean candidate in both supported xrpl-py environments.
2. Update synchronized version fields and `CHANGELOG.md`.
3. Build and install the wheel from a clean archive.
4. Review the public README, security policy, limits, capability map, and links as product documentation.
5. Push, tag, create the GitHub Release, and verify branch/tag CI and published checksums.
