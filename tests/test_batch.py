#!/usr/bin/env python3
"""Regression tests for the XLS-56 Batch retirement (2026-07-11).

Official XRPL material lists the `Batch` amendment as obsolete following the February 2026
signature-validation (unauthorized-inner-transaction) disclosure. The `build-batch` builder is
therefore retired: it must not be reachable from CLI dispatch or the MCP surface, and the raw
`supported: true` feature flag must not be treated as authorization to expose it. The
implementation is preserved (unregistered) as a historical artifact so the change stays
auditable and reversible. See scripts/tools/batch.py and the v1.8.3 entry in CHANGELOG.md.

These tests are offline-safe: dispatcher/allowlist checks are pure imports and the CLI check is a
local subprocess. MCP-surface retirement (listing + xrpl_run denial) is proven in test_mcp_server.py.
"""
import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

BATCH_SOURCE = ROOT / "scripts" / "tools" / "batch.py"


def test_build_batch_absent_from_cli_dispatcher():
    """The retired builder must not be a registered dispatcher command."""
    from scripts.xrpl_tools import COMMANDS
    assert "build-batch" not in COMMANDS, "build-batch must be unregistered (retired)"
    assert len(COMMANDS) == 72, f"dispatcher should hold 72 commands, has {len(COMMANDS)}"


def test_build_batch_cli_reports_unknown_command():
    """Invoking build-batch on the CLI reports an unknown command (exit 0 is the dispatcher's
    normal path for an unrecognized name) and never emits a Batch payload."""
    proc = subprocess.run(
        [sys.executable, "scripts/xrpl_tools.py", "build-batch",
         "--from", "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe",
         "--inner-txs", "[]"],
        cwd=ROOT, text=True, capture_output=True, timeout=30,
    )
    out = proc.stdout + proc.stderr
    assert "Unknown command: build-batch" in out, out
    assert "RawTransactions" not in out, "must not emit a Batch payload"
    assert '"TransactionType": "Batch"' not in out, "must not emit a Batch payload"


def test_build_batch_absent_from_mcp_allowlist_and_denylist():
    """The MCP agent allowlist must not expose the retired builder."""
    import scripts.mcp_server as mcp
    assert "build-batch" not in mcp._ALLOWED_COMMANDS, "build-batch must not be MCP-runnable"
    # And it is not a phantom on the deny-list either (it is simply gone from the dispatcher),
    # so the allowlist/deny-list partition of the dispatcher stays exhaustive.
    assert "build-batch" not in mcp._DENIED_COMMANDS


def test_batch_module_registers_no_command():
    """Importing the module's COMMANDS yields an empty mapping — the retirement is
    'unregister', not a dangling entry."""
    import scripts.tools.batch as batch_mod
    assert batch_mod.COMMANDS == {}, "batch module must register no command"
    assert isinstance(batch_mod.COMMANDS, dict)


def test_batch_implementation_preserved_as_retirement_record():
    """The old implementation is kept for audit/history, but exposes no command. This proves the
    retirement is 'unregister', not 'delete' — the file and function remain importable and valid."""
    import scripts.tools.batch as batch_mod
    assert callable(getattr(batch_mod, "tool_build_batch", None)), \
        "preserved implementation must remain importable"
    assert BATCH_SOURCE.is_file(), "the Batch source must remain present as a retirement record"


def test_batch_source_states_a_clear_retirement_reason():
    """The rationale is documented at the source level so the builder is not silently re-enabled."""
    source = BATCH_SOURCE.read_text(encoding="utf-8")
    doc = ast.get_docstring(ast.parse(source)) or ""
    assert "RETIRED" in doc, "retirement notice must remain in the module docstring"
    for expected in ("obsolete", "BatchV1_1", "preserved"):
        assert expected in doc, f"retirement reason must mention {expected!r}"
    # The security disclosure that drove the retirement is cited, not just asserted.
    assert "xrpl.org" in doc, "retirement must cite its official source"
    assert "supported: true" in doc, "must warn that the raw feature flag is not authorization"


def test_dev_test_matrix_records_batch_as_retired_and_never_runs_it():
    """The matrix records the retirement instead of dropping the command silently, and holds no
    executable test argv for it. Parsed statically — importing the module would run the matrix."""
    tree = ast.parse((ROOT / "scripts" / "dev_test_matrix.py").read_text(encoding="utf-8"))
    tables = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", None) in ("TESTS", "RETIRED"):
            tables[node.targets[0].id] = {k.value: k for k in node.value.keys}
    assert "build-batch" not in tables["TESTS"], "matrix must hold no test argv for a retired command"
    assert "build-batch" in tables["RETIRED"], "matrix must record the Batch retirement"
