"""End-to-end tests for the stdio MCP server (offline-safe)."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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

        # notification: must produce no response (next reply is for id 2)
        proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        proc.stdin.flush()

        tools = _rpc(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        names = {t["name"] for t in tools["result"]["tools"]}
        assert names == {"xrpl_list_commands", "xrpl_run", "xrpl_knowledge_index", "xrpl_knowledge"}

        lst = _rpc(proc, {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                          "params": {"name": "xrpl_list_commands", "arguments": {}}})
        listing = json.loads(lst["result"]["content"][0]["text"])
        assert listing["count"] >= 69
        assert "build-payment" in listing["commands"]
        assert "token-intel" in listing["commands"]
        assert "amm-info" in listing["commands"]

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
