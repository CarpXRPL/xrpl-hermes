#!/usr/bin/env python3
"""xrpl-hermes MCP server — stdio transport, stdlib only.

Exposes the 67-command dispatcher and the 63-file knowledge base to any
MCP client (Claude Code, OpenClaw, Cursor, etc.):

    claude mcp add xrpl-hermes -- python3 /path/to/xrpl-hermes/scripts/mcp_server.py

Tools:
    xrpl_list_commands   — list every dispatcher command
    xrpl_run             — run one command (same args as the CLI)
    xrpl_knowledge_index — list knowledge/reference files with titles
    xrpl_knowledge       — read one knowledge/reference file

Commands run in a subprocess so a tool crash can never take down the
server. No secrets are read or stored; signing stays with the user.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_VERSION = "2025-06-18"
SERVER_INFO = {"name": "xrpl-hermes", "version": "1.4.1"}
RUN_TIMEOUT_SECONDS = 90

_KNOWLEDGE_DIRS = ("knowledge", "references")


def _command_names():
    """Command list from the dispatcher, without crashing if xrpl-py is absent."""
    try:
        sys.path.insert(0, str(ROOT))
        from scripts.xrpl_tools import COMMANDS
        return sorted(COMMANDS.keys()), None
    except Exception as e:  # noqa: BLE001 — report import problems to the client
        return [], f"dispatcher unavailable: {e}"


def _knowledge_files():
    out = []
    for d in _KNOWLEDGE_DIRS:
        base = ROOT / d
        if not base.is_dir():
            continue
        for p in sorted(base.glob("*.md")):
            title = ""
            try:
                for line in p.read_text(encoding="utf-8").splitlines():
                    if line.startswith("#"):
                        title = line.lstrip("# ").strip()
                        break
            except OSError:
                pass
            out.append({"file": f"{d}/{p.name}", "title": title})
    return out


def _read_knowledge(rel: str) -> str:
    p = (ROOT / rel).resolve()
    allowed = any(p.is_relative_to((ROOT / d).resolve()) for d in _KNOWLEDGE_DIRS)
    if not allowed or p.suffix != ".md":
        raise ValueError(f"file must be a .md under {' or '.join(_KNOWLEDGE_DIRS)}/")
    if not p.is_file():
        raise ValueError(f"not found: {rel}")
    return p.read_text(encoding="utf-8")


def _run_command(command: str, args) -> str:
    names, err = _command_names()
    if err:
        raise ValueError(err)
    if command not in names:
        raise ValueError(f"unknown command '{command}'. Use xrpl_list_commands.")
    if not isinstance(args, list) or not all(isinstance(a, str) for a in args):
        raise ValueError("args must be a list of strings")
    proc = subprocess.run(
        [sys.executable, "-m", "scripts.xrpl_tools", command, *args],
        cwd=ROOT, capture_output=True, text=True, timeout=RUN_TIMEOUT_SECONDS,
    )
    out = proc.stdout.strip()
    if proc.stderr.strip():
        out = (out + "\n[stderr] " + proc.stderr.strip()).strip()
    return out or f"(no output, exit code {proc.returncode})"


TOOLS = [
    {
        "name": "xrpl_list_commands",
        "description": "List all xrpl-hermes commands (live XRPL queries, signer-ready "
                       "transaction builders, amendment checks, EVM/Xahau/Flare helpers).",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "xrpl_run",
        "description": "Run one xrpl-hermes command with CLI-style args. Examples: "
                       "command='account' args=['rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe']; "
                       "command='build-payment' args=['--from','rSRC','--to','rDST','--amount','1000000']; "
                       "command='amendment' args=['MPTokensV1']. Builders return signer-ready "
                       "JSON — they never ask for or use secret keys.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Command name from xrpl_list_commands"},
                "args": {"type": "array", "items": {"type": "string"},
                         "description": "CLI arguments, one element per token"},
            },
            "required": ["command"],
            "additionalProperties": False,
        },
    },
    {
        "name": "xrpl_knowledge_index",
        "description": "List the XRPL knowledge base (63 files) and references with titles. "
                       "Read the relevant file with xrpl_knowledge before building.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "xrpl_knowledge",
        "description": "Read one knowledge or reference file, e.g. 'knowledge/05-xrpl-amm.md'.",
        "inputSchema": {
            "type": "object",
            "properties": {"file": {"type": "string", "description": "Path from xrpl_knowledge_index"}},
            "required": ["file"],
            "additionalProperties": False,
        },
    },
]


def _call_tool(name: str, arguments: dict) -> str:
    if name == "xrpl_list_commands":
        names, err = _command_names()
        if err:
            raise ValueError(err)
        return json.dumps({"count": len(names), "commands": names}, indent=2)
    if name == "xrpl_run":
        return _run_command(arguments.get("command", ""), arguments.get("args", []))
    if name == "xrpl_knowledge_index":
        return json.dumps(_knowledge_files(), indent=2)
    if name == "xrpl_knowledge":
        return _read_knowledge(arguments.get("file", ""))
    raise ValueError(f"unknown tool: {name}")


def _handle(msg: dict):
    method = msg.get("method")
    msg_id = msg.get("id")
    if method == "initialize":
        client_proto = (msg.get("params") or {}).get("protocolVersion") or PROTOCOL_VERSION
        return {"jsonrpc": "2.0", "id": msg_id, "result": {
            "protocolVersion": client_proto,
            "capabilities": {"tools": {}},
            "serverInfo": SERVER_INFO,
        }}
    if method == "ping":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = msg.get("params") or {}
        try:
            text = _call_tool(params.get("name", ""), params.get("arguments") or {})
            result = {"content": [{"type": "text", "text": text}], "isError": False}
        except subprocess.TimeoutExpired:
            result = {"content": [{"type": "text", "text":
                      f"command timed out after {RUN_TIMEOUT_SECONDS}s"}], "isError": True}
        except Exception as e:  # noqa: BLE001 — tool errors go back to the client
            result = {"content": [{"type": "text", "text": f"error: {e}"}], "isError": True}
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}
    if msg_id is None:
        return None  # notification — nothing to send
    return {"jsonrpc": "2.0", "id": msg_id,
            "error": {"code": -32601, "message": f"method not found: {method}"}}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = _handle(msg)
        if resp is not None:
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
