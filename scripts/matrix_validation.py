#!/usr/bin/env python3
"""Pure validation helpers for the generated CLI test matrix."""
from __future__ import annotations

import json


def builder_wire_error(name: str, stdout: str) -> str | None:
    """Return an error when successful builder stdout is not a complete signer transaction."""
    if not name.startswith("build-"):
        return None

    try:
        payload = json.loads(stdout)
    except Exception as exc:
        return f"builder stdout is not valid JSON: {exc}"
    if not isinstance(payload, dict):
        return "builder stdout is not a transaction JSON object"
    if "Error" in payload:
        return f"builder returned {payload.get('Error')}"
    if not payload.get("TransactionType"):
        return "builder transaction is missing TransactionType"
    if not payload.get("Account"):
        return "builder transaction is missing Account"

    try:
        from xrpl.models.transactions import Transaction
        Transaction.from_xrpl(payload)
    except Exception as exc:
        return f"transaction model validation failed: {exc}"

    try:
        from xrpl.core.binarycodec import encode_for_signing
        encode_for_signing(payload)
    except Exception as exc:
        return f"binary signing serialization failed: {exc}"
    return None
