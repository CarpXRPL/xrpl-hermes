"""End-to-end tests for the stdio MCP server (offline-safe).

Covers the agent boundary added in v1.8.3: `xrpl_run` is a positive allowlist with
default-deny, so secret-touching, broadcast, and external-signing commands are refused
before any subprocess is spawned, and any unclassified/future command is refused too.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DENIED = ("wallet-generate", "wallet-from-seed", "submit", "submit-multisigned", "xaman-payload")

# XRPL family seeds are base58; anything matching this shape is decoded before it is called a seed.
_SEED_SHAPED = re.compile(r"\bs[1-9A-HJ-NP-Za-km-z]{20,40}\b")


def _contains_decodable_seed(text: str) -> bool:
    from xrpl.core.addresscodec import decode_seed
    for match in _SEED_SHAPED.finditer(text):
        try:
            decode_seed(match.group(0))
        except Exception:
            continue
        return True
    return False


def _rpc(proc, payload):
    proc.stdin.write(json.dumps(payload) + "\n")
    proc.stdin.flush()
    line = proc.stdout.readline()
    assert line, "server closed stdout unexpectedly"
    return json.loads(line)


def _start():
    return subprocess.Popen(
        [sys.executable, str(ROOT / "scripts" / "mcp_server.py")],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, cwd=ROOT,
    )


def test_mcp_session():
    proc = _start()
    try:
        init = _rpc(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                           "params": {"protocolVersion": "2025-06-18",
                                      "capabilities": {}, "clientInfo": {"name": "pytest", "version": "0"}}})
        assert init["result"]["serverInfo"]["name"] == "xrpl-hermes"
        assert init["result"]["serverInfo"]["version"] == "1.9.0"

        # notification: must produce no response (next reply is for id 2)
        proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        proc.stdin.flush()

        tools = _rpc(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        names = {t["name"] for t in tools["result"]["tools"]}
        assert names == {"xrpl_list_commands", "xrpl_run", "xrpl_knowledge_index", "xrpl_knowledge"}

        lst = _rpc(proc, {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                          "params": {"name": "xrpl_list_commands", "arguments": {}}})
        listing = json.loads(lst["result"]["content"][0]["text"])
        # xrpl_list_commands reflects the agent-safe allowlist: the 72 dispatcher
        # commands minus the 5 secret/broadcast/external-signing commands denied over MCP.
        assert listing["count"] == 67
        assert len(listing["commands"]) == 67
        for allowed in ("build-payment", "token-intel", "amm-info", "flare-ftso",
                        "bridge-status", "arweave-cost"):
            assert allowed in listing["commands"], allowed
        for denied in DENIED:
            assert denied not in listing["commands"], denied
        # build-batch (XLS-56) is retired — unregistered, so it is neither runnable nor listed.
        assert "build-batch" not in listing["commands"], "retired Batch builder must not be listed"

        # offline command through the real dispatcher
        run = _rpc(proc, {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                          "params": {"name": "xrpl_run",
                                     "arguments": {"command": "validate-address",
                                                   "args": ["rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh"]}}})
        assert run["result"]["isError"] is False
        assert "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh" in run["result"]["content"][0]["text"]

        idx = _rpc(proc, {"jsonrpc": "2.0", "id": 5, "method": "tools/call",
                          "params": {"name": "xrpl_knowledge_index", "arguments": {}}})
        files = json.loads(idx["result"]["content"][0]["text"])
        assert any(f["file"] == "knowledge/05-xrpl-amm.md" for f in files)

        doc = _rpc(proc, {"jsonrpc": "2.0", "id": 6, "method": "tools/call",
                          "params": {"name": "xrpl_knowledge",
                                     "arguments": {"file": "knowledge/05-xrpl-amm.md"}}})
        assert doc["result"]["isError"] is False
        assert "AMM" in doc["result"]["content"][0]["text"]
    finally:
        proc.terminate()
        proc.wait(timeout=10)


def test_mcp_rejects_bad_input():
    proc = _start()
    try:
        _rpc(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                    "params": {"protocolVersion": "2025-06-18"}})

        bad_cmd = _rpc(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                              "params": {"name": "xrpl_run",
                                         "arguments": {"command": "rm-rf", "args": []}}})
        assert bad_cmd["result"]["isError"] is True

        traversal = _rpc(proc, {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                                "params": {"name": "xrpl_knowledge",
                                           "arguments": {"file": "../SKILL.md"}}})
        assert traversal["result"]["isError"] is True

        unknown = _rpc(proc, {"jsonrpc": "2.0", "id": 4, "method": "no/such"})
        assert unknown["error"]["code"] == -32601
    finally:
        proc.terminate()
        proc.wait(timeout=10)


def test_allowlist_and_denylist_partition_the_dispatcher():
    """Every dispatcher command must be consciously classified — on the allowlist or the
    deny-list, never both, with nothing left unclassified. This fires the day a maintainer
    adds a dispatcher command without a tier decision; default-deny keeps it safe until then."""
    import scripts.mcp_server as mcp
    from scripts.xrpl_tools import COMMANDS
    allowed = set(mcp._ALLOWED_COMMANDS)
    denied = set(mcp._DENIED_COMMANDS)
    dispatcher = set(COMMANDS)

    assert allowed.isdisjoint(denied), f"classified as both: {sorted(allowed & denied)}"
    assert allowed | denied == dispatcher, {
        "unclassified (add to _ALLOWED_COMMANDS or _DENIED_COMMANDS)": sorted(dispatcher - allowed - denied),
        "phantom (in a set but not the dispatcher)": sorted((allowed | denied) - dispatcher),
    }
    # 72 = 67 + 5 — the exact partition this hotfix establishes.
    assert (len(dispatcher), len(allowed), len(denied)) == (72, 67, 5)
    assert set(denied) == set(DENIED)
    # The retired XLS-56 build-batch builder is fully out of the classification: not in the
    # dispatcher, not allowed, and not a phantom deny-list entry.
    assert "build-batch" not in dispatcher
    assert "build-batch" not in allowed and "build-batch" not in denied


@pytest.mark.parametrize("command", DENIED)
def test_denied_commands_refused_before_subprocess(monkeypatch, command):
    """The gate fires before any process is spawned — not after, and not by relying on the
    command's own safety behavior. A spawn here is a boundary failure, so it fails the test."""
    import scripts.mcp_server as mcp

    def _no_spawn(*args, **kwargs):  # pragma: no cover - must never run
        raise AssertionError(f"subprocess spawned for denied command {command!r}: {args!r}")

    monkeypatch.setattr(mcp.subprocess, "run", _no_spawn)
    with pytest.raises(ValueError) as exc:
        mcp._run_command(command, [])
    text = str(exc.value)
    assert "not available over MCP" in text
    assert "quarantined" in text
    assert not _contains_decodable_seed(text)


def test_future_dispatcher_command_denied_before_subprocess(monkeypatch):
    """A command added to the dispatcher later but not classified in the allowlist is
    default-denied — the boundary stays safe without a maintainer touching this file."""
    import scripts.mcp_server as mcp
    from scripts.xrpl_tools import COMMANDS

    future = "build-future-unclassified"
    assert future not in COMMANDS and future not in mcp._ALLOWED_COMMANDS

    def _no_spawn(*args, **kwargs):  # pragma: no cover - must never run
        raise AssertionError(f"subprocess spawned for unclassified command: {args!r}")

    monkeypatch.setattr(mcp.subprocess, "run", _no_spawn)
    # Simulate the dispatcher having grown a new command that nobody classified.
    monkeypatch.setattr(mcp, "_command_names", lambda: (sorted(set(COMMANDS) | {future}), None))

    with pytest.raises(ValueError) as exc:
        mcp._run_command(future, [])
    assert "default-deny" in str(exc.value)

    # A name that is not even in the dispatcher is denied on the same path.
    with pytest.raises(ValueError) as exc:
        mcp._run_command("definitely-not-a-command", [])
    assert "unknown command" in str(exc.value)


def test_mcp_denies_secret_and_broadcast_commands_over_stdio():
    """Same boundary, proven over the real MCP wire: every denied command returns
    isError:true with a denial message, and no response ever carries a seed."""
    proc = _start()
    try:
        _rpc(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                    "params": {"protocolVersion": "2025-06-18"}})
        mid = 1
        # No seed-like argument is ever passed here — the gate fires before subprocess.
        for cmd in DENIED:
            mid += 1
            resp = _rpc(proc, {"jsonrpc": "2.0", "id": mid, "method": "tools/call",
                               "params": {"name": "xrpl_run",
                                          "arguments": {"command": cmd, "args": []}}})
            assert resp["result"]["isError"] is True, cmd
            text = resp["result"]["content"][0]["text"]
            assert "not available over MCP" in text, (cmd, text)
            assert "quarantined" in text, (cmd, text)
            assert not _contains_decodable_seed(text), (cmd, "denial response leaked a seed")
            assert "master_seed" not in text and "seed_hex" not in text, cmd

        # a name that is not on the allowlist (and not in the dispatcher) is denied too
        mid += 1
        unknown = _rpc(proc, {"jsonrpc": "2.0", "id": mid, "method": "tools/call",
                              "params": {"name": "xrpl_run",
                                         "arguments": {"command": "definitely-not-a-command",
                                                       "args": []}}})
        assert unknown["result"]["isError"] is True
        assert "xrpl_list_commands" in unknown["result"]["content"][0]["text"]

        # the retired XLS-56 build-batch builder is denied over MCP as well: it is unregistered,
        # so it takes the same default-deny/unknown-command path and never emits a Batch payload.
        mid += 1
        retired = _rpc(proc, {"jsonrpc": "2.0", "id": mid, "method": "tools/call",
                              "params": {"name": "xrpl_run",
                                         "arguments": {"command": "build-batch", "args": []}}})
        assert retired["result"]["isError"] is True
        rtext = retired["result"]["content"][0]["text"]
        assert "build-batch" in rtext
        assert "RawTransactions" not in rtext and "TransactionType" not in rtext
    finally:
        proc.terminate()
        proc.wait(timeout=10)


def test_version_surfaces_report_1_9_0():
    """Version synchronization: pyproject, SKILL.md, MCP SERVER_INFO, and the newest
    CHANGELOG entry all report this hotfix release."""
    import scripts.mcp_server as mcp
    from scripts.audit_project_quality import check_version_sync

    assert mcp.SERVER_INFO["version"] == "1.9.0"
    assert re.search(r'^version\s*=\s*"1\.9\.0"', (ROOT / "pyproject.toml").read_text(), re.M)
    assert re.search(r"^version:\s*1\.9\.0\s*$", (ROOT / "SKILL.md").read_text(), re.M)
    assert re.search(r"^##\s*v?1\.9\.0\b", (ROOT / "CHANGELOG.md").read_text(), re.M)
    assert check_version_sync([]) == [], "version surfaces disagree"


def test_dev_matrix_never_generates_a_wallet_seed():
    """The verification matrix must not run wallet-generate and redact afterward.

    Safety means the seed is never created. Parse the module without importing it because the
    matrix executes at import time.
    """
    import ast

    tree = ast.parse((ROOT / "scripts" / "dev_test_matrix.py").read_text(encoding="utf-8"))
    tables = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or not node.targets:
            continue
        name = getattr(node.targets[0], "id", None)
        if name in ("TESTS", "SKIPPED_SAFETY") and isinstance(node.value, ast.Dict):
            tables[name] = {k.value for k in node.value.keys if isinstance(k, ast.Constant)}

    for command in ("wallet-generate", "xaman-payload"):
        assert command not in tables["TESTS"]
        assert command in tables["SKIPPED_SAFETY"]
