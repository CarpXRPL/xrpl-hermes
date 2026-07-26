# Maintenance

Current XRPL state must be read live. Do not preserve dated snapshots of fees, reserves, amendments, balances, liquidity, provider schemas, or endpoint behavior as product claims.

## Routine checks

| Area | Check |
|---|---|
| XRPL network | `xrpl-hermes server-info` and `xrpl-hermes amendments` |
| Python dependency | Compare `pyproject.toml` with current `xrpl-py` releases |
| JavaScript examples | Compare `examples/js/package.json` with current `xrpl.js` releases |
| External integrations | Recheck Xaman, Xahau, XRPL EVM, Flare, Axelar, and Arweave against first-party documentation and live read fixtures |
| Documentation | Confirm every advertised capability has a command or a concrete external-setup path |

If a fact changes frequently, document how to query it rather than copying the current value into Markdown.

## Before a commit

```bash
python3 -m pytest -q
python3 scripts/dev_test_matrix.py
python3 scripts/audit_project_quality.py
python3 -m scripts.package_acceptance
python3 -m compileall -q scripts tests examples
git diff --check
```

The matrix does not modify the repository by default. Set `XRPL_HERMES_MATRIX_REPORT` when a local detailed report is useful.

## Safety checks

- No command handles wallet secrets or broadcasts transactions.
- Builders remain unsigned.
- The MCP allowlist covers only reads and unsigned builders.
- Xaman remains local-only and requires explicit credentials.
- Live-data failures stay explicit and never become fabricated fallback values.
- Mainnet behavior is never inferred from Testnet or amendment support alone.
