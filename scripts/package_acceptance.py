#!/usr/bin/env python3
"""Offline acceptance check for a source tree or installed XRPL-Hermes wheel."""
from __future__ import annotations

import json

from scripts import mcp_server
from scripts.xrpl_tools import COMMANDS

EXPECTED = {
    "version": "1.9.1",
    "dispatcher": 68,
    "allowed": 67,
    "denied": 1,
    "knowledge": 65,
    "references": 15,
    "skills": 25,
}


def main() -> None:
    counts = {
        "version": mcp_server.SERVER_INFO["version"],
        "dispatcher": len(COMMANDS),
        "allowed": len(mcp_server._ALLOWED_COMMANDS),
        "denied": len(mcp_server._DENIED_COMMANDS),
        "knowledge": len(list((mcp_server.ROOT / "knowledge").glob("*.md"))),
        "references": len(list((mcp_server.ROOT / "references").glob("*.md"))),
        "skills": len(list((mcp_server.ROOT / "skills").glob("*.md"))),
    }
    assert counts == EXPECTED, {"expected": EXPECTED, "observed": counts, "root": str(mcp_server.ROOT)}
    assert mcp_server._ALLOWED_COMMANDS.isdisjoint(mcp_server._DENIED_COMMANDS)
    assert mcp_server._ALLOWED_COMMANDS | set(mcp_server._DENIED_COMMANDS) == set(COMMANDS)
    text = mcp_server._read_knowledge("knowledge/01-xrpl-accounts.md")
    assert "XRPL Accounts" in text
    print(json.dumps({"status": "PASS", "root": str(mcp_server.ROOT), **counts}, indent=2))


if __name__ == "__main__":
    main()
