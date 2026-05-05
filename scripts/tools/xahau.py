#!/usr/bin/env python3
"""Xahau Hooks tools."""
from ._shared import (
    json_out, note_out,
)
import httpx, sys

def tool_hooks_info(address: str):
    payload = {"method": "account_objects", "params": [{"account": address, "ledger_index": "validated", "type": "hook", "limit": 20}]}
    try:
        resp = httpx.post("https://xahau.network", json=payload, timeout=15)
        data = resp.json()
        hooks = data.get("result", {}).get("account_objects", [])
        json_out({"Account": address, "HookCount": len(hooks), "Hooks": hooks, "Raw": data.get("result", data)})
    except Exception as e:
        json_out({"Error": "HooksInfoError", "Message": str(e), "Account": address})

def tool_hooks_bitmask(*hook_names: str):
    json_out({
        "Error": "UnsupportedTool",
        "Command": "hooks-bitmask",
        "HookNames": list(hook_names),
        "Message": "hooks-bitmask is disabled because Xahau HookOn uses a 256-bit bitmap indexed by transaction-type ID, not named events.",
    })

COMMANDS = {
    "hooks-info": lambda: tool_hooks_info(sys.argv[2]) if len(sys.argv) >= 3 else print("Usage: hooks-info rADDRESS"),
    "hooks-bitmask": lambda: tool_hooks_bitmask(*sys.argv[2:]),
}
