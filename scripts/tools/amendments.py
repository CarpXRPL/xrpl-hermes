#!/usr/bin/env python3
"""Live XRPL amendment status tools.

Queries public XRPL mainnet nodes at runtime. This keeps XRPL-Hermes from
claiming that amendment-dependent transaction types are usable when the live
network says otherwise.
"""
from typing import Optional
import sys
from ._shared import json_out, note_out, get_amendment_status, list_amendments


def tool_amendments(filter_text: Optional[str] = None):
    """Print all known amendments grouped by live mainnet state."""
    data = list_amendments()
    if filter_text:
        q = filter_text.lower()
        for bucket in ("enabled", "supported_not_enabled", "vetoed", "unsupported"):
            data[bucket] = [
                x for x in data.get(bucket, [])
                if q in x.get("name", "").lower() or q in x.get("id", "").lower()
            ]
        data["filter"] = filter_text
    json_out(data)


def tool_amendment(name_or_id: str):
    """Print one amendment's live status by name or feature ID."""
    json_out(get_amendment_status(name_or_id))


COMMANDS = {
    "amendments": lambda: tool_amendments(sys.argv[2] if len(sys.argv) > 2 else None),
    "amendment": lambda: tool_amendment(sys.argv[2]) if len(sys.argv) >= 3 else json_out({
        "Error": "UsageError",
        "Usage": "amendment NAME_OR_FEATURE_ID",
    }),
    "amendment-status": lambda: tool_amendments(sys.argv[2] if len(sys.argv) > 2 else None),
}
