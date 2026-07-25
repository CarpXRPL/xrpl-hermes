#!/usr/bin/env python3
"""xrpl-hermes MCP server — stdio transport, stdlib only.

Exposes an agent-safe subset of the CLI dispatcher plus the full knowledge base
to any MCP client (Claude Code, OpenClaw, Cursor, etc.):

    claude mcp add xrpl-hermes -- python3 /path/to/xrpl-hermes/scripts/mcp_server.py

Tools:
    xrpl_list_commands   — list the agent-safe command allowlist
    xrpl_run             — run one allowlisted command (same args as the CLI)
    xrpl_knowledge_index — list knowledge/reference/workflow files with titles
    xrpl_knowledge       — read one knowledge/reference/workflow file

Agent boundary (positive allowlist, default-deny). The MCP surface exposes
read-only live queries and unsigned/signer-ready transaction builders only.
Secret-touching commands (`wallet-generate`, `wallet-from-seed`), broadcast
commands (`submit`, `submit-multisigned`), and external signing-request creation
(`xaman-payload`) are denied here and remain in the local developer CLI.
Any command not on the allowlist — including future additions — is denied until
a maintainer explicitly adds it, so the boundary is a maintainable invariant
rather than a one-time patch.

Commands run in a subprocess so a tool crash can never take down the server.
No secrets are read, accepted, or stored; signing stays with the user.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_VERSION = "2025-06-18"
SERVER_INFO = {"name": "xrpl-hermes", "version": "1.8.3"}
RUN_TIMEOUT_SECONDS = 90

_KNOWLEDGE_DIRS = ("knowledge", "references", "skills")

# Positive, default-deny agent boundary for xrpl_run. Only names in this set are
# runnable over MCP. Anything else — including any command added to the dispatcher
# later — is denied until a maintainer explicitly adds it here. This keeps the
# boundary a maintainable invariant: a new secret-touching command is safe by default.
_ALLOWED_COMMANDS = frozenset({
    # Tier R — read-only live queries (no keys, no writes).
    "account", "balance", "trustlines", "account_objects", "account-tx",
    "book-offers", "path-find", "ledger", "ledger-entry", "server-info",
    "tx-info", "decode", "amendments", "amendment", "amendment-status",
    "amm-info", "token-intel", "nft-info", "nft-offers", "evm-balance",
    "evm-bridge", "hooks-info", "flare-price", "flare-ftso", "bridge-status",
    "bridge-tx", "arweave-cost", "validate-address", "subscribe",
    # Tier B — unsigned builders. Emit signer-ready JSON only; never sign or submit.
    "build-account-delete", "build-account-set", "build-amm-bid",
    "build-amm-create", "build-amm-deposit", "build-amm-vote",
    "build-amm-withdraw", "build-check-cancel",
    "build-check-cash", "build-check-create", "build-clawback",
    "build-credential-accept", "build-credential-create",
    "build-credential-delete", "build-cross-currency-payment",
    "build-deposit-preauth", "build-escrow-cancel", "build-escrow-create",
    "build-escrow-finish", "build-mpt-authorize", "build-mpt-issuance-create",
    "build-nft-accept-offer", "build-nft-burn", "build-nft-cancel-offer",
    "build-nft-create-offer", "build-nft-mint", "build-offer",
    "build-paychannel-claim", "build-paychannel-create", "build-paychannel-fund",
    "build-payment", "build-set-oracle", "build-set-regular-key",
    "build-signer-list-set", "build-ticket-create", "build-trustset",
    "evm-contract", "hooks-bitmask",
    # NOTE: `build-batch` (XLS-56) is intentionally absent — the Batch builder was retired
    # (obsolete amendment after the February 2026 security disclosure; see
    # scripts/tools/batch.py and CHANGELOG.md). It is also unregistered in the dispatcher,
    # so a request for it is default-denied as an unknown command.
})

# Denied on the agent surface, with the reason to relay to the client. These stay
# available in the local developer CLI (developer-owned, explicit, shell-audited).
_DENIED_COMMANDS = {
    "wallet-generate": "generates a wallet and emits a secret seed",
    "wallet-from-seed": "takes a secret seed as input",
    "submit": "broadcasts an already-signed transaction blob to a live network",
    "submit-multisigned": "broadcasts an already-signed multisigned transaction to a live network",
    "xaman-payload": "creates a real external wallet signing request",
}


def _deny_reason(command: str, known: bool) -> str:
    """Human-readable denial for a non-allowlisted command, redirecting to the CLI."""
    reason = _DENIED_COMMANDS.get(command)
    if reason:
        return (f"'{command}' is not available over MCP: it {reason}. XRPL-Hermes keeps "
                "key material and broadcasting out of the agent boundary. Run it yourself in "
                f"the local developer CLI: python3 -m scripts.xrpl_tools {command} …")
    if not known:
        return (f"unknown command '{command}'. Use xrpl_list_commands to see the "
                "agent-safe surface.")
    return (f"'{command}' is not on the MCP agent allowlist (default-deny). This surface "
            "exposes read-only live queries and unsigned transaction builders only. "
            "Use xrpl_list_commands, or run it in the local developer CLI.")


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
    # Default-deny gate — enforced before any subprocess launch.
    if command not in _ALLOWED_COMMANDS:
        raise ValueError(_deny_reason(command, known=command in names))
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
        "description": "List the agent-safe xrpl-hermes commands exposed over MCP: live XRPL "
                       "queries, signer-ready (unsigned) transaction builders, amendment checks, "
                       "and EVM/Xahau/Flare helpers. Key-management, broadcast, and Xaman signing "
                       "request creation are not exposed here — they live in the local developer CLI.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "xrpl_run",
        "description": "Run one agent-safe xrpl-hermes command with CLI-style args. Examples: "
                       "command='account' args=['rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe']; "
                       "command='build-payment' args=['--from','rSRC','--to','rDST','--amount','1000000'] "
                       "— --amount is integer drops, so 1000000 means 1 XRP; an issued "
                       "currency is 'CUR:ISSUER:VALUE'; "
                       "command='amendment' args=['MPTokensV1']. Builders return signer-ready "
                       "JSON — they never ask for or use secret keys. Secret-touching and broadcast "
                       "commands are denied on this surface (see xrpl_list_commands); run those in the "
                       "local developer CLI.",
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
        "description": "List the XRPL knowledge base, reference cards, and skills/ workflow "
                       "flows with titles. Read the relevant file with xrpl_knowledge before building.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "xrpl_knowledge",
        "description": "Read one knowledge, reference, or workflow file, e.g. "
                       "'knowledge/05-xrpl-amm.md' or 'skills/failed-transaction-diagnosis-flow.md'.",
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
        # Reflect the agent boundary: only allowlisted commands are runnable here.
        allowed = sorted(n for n in names if n in _ALLOWED_COMMANDS)
        return json.dumps({"count": len(allowed), "commands": allowed}, indent=2)
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
