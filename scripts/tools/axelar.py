#!/usr/bin/env python3
"""Read-only Axelarscan registration and GMP-index helpers."""
from datetime import datetime, timezone
import re
import sys

import httpx

from ._shared import json_out, usage_out

CHAINS_API = "https://api.axelarscan.io/api/getChains"
GMP_API = "https://api.gmp.axelarscan.io"
XRPL_CHAIN_IDS = ("xrpl", "xrpl-evm")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _chain_summary(chain: dict) -> dict:
    return {
        "id": chain.get("id"),
        "name": chain.get("chain_name"),
        "chain_type": chain.get("chain_type"),
        "evm_chain_id": chain.get("chain_id"),
        "gateway": (chain.get("gateway") or {}).get("address"),
        "native_token": chain.get("native_token"),
        "explorer": (chain.get("explorer") or {}).get("url"),
        "deprecated": bool(chain.get("deprecated")),
    }


def tool_bridge_status(*chain_ids: str):
    wanted = [c.lower() for c in chain_ids] if chain_ids else list(XRPL_CHAIN_IDS)
    try:
        response = httpx.get(CHAINS_API, timeout=20)
        response.raise_for_status()
        chains = response.json()
        if not isinstance(chains, list):
            raise RuntimeError("Axelarscan chain response was not a list")
    except Exception as exc:
        json_out({"Error": "AxelarChainsUnavailable", "Message": str(exc), "API": CHAINS_API})
        return
    by_id = {str(item.get("id", "")).lower(): item for item in chains if isinstance(item, dict)}
    found = {cid: _chain_summary(by_id[cid]) for cid in wanted if cid in by_id}
    missing = [cid for cid in wanted if cid not in by_id]
    json_out({
        "Source": CHAINS_API,
        "FetchedAt": _now(),
        "Capability": "Axelarscan chain-registration lookup only",
        "Chains": found,
        "MissingChains": missing,
        "RouteCertified": False,
        "Note": (
            "Registration does not establish route availability, supported assets, minimums, "
            "fees, liquidity, pause state, or transfer success."
        ),
    })


def tool_bridge_tx(tx_hash: str):
    if not re.fullmatch(r"(?:0x)?[0-9A-Fa-f]{64}", tx_hash or "", re.ASCII):
        json_out({
            "Error": "InvalidTransactionHash",
            "Message": "Expected 64 hexadecimal characters, optionally 0x-prefixed.",
            "TxHash": tx_hash,
        })
        return
    try:
        response = httpx.post(
            GMP_API,
            json={"method": "searchGMP", "txHash": tx_hash, "size": 5},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise RuntimeError("Axelarscan GMP response was not an object")
    except Exception as exc:
        json_out({"Error": "AxelarGMPUnavailable", "Message": str(exc), "API": GMP_API, "TxHash": tx_hash})
        return
    records = payload.get("data") or []
    if not isinstance(records, list):
        json_out({"Error": "AxelarGMPMalformed", "Message": "GMP data was not a list", "API": GMP_API, "TxHash": tx_hash})
        return
    if not records:
        json_out({
            "TxHash": tx_hash,
            "Found": False,
            "Source": GMP_API,
            "FetchedAt": _now(),
            "Capability": "Axelar GMP-index search only",
            "Message": "No GMP record found; this may be non-GMP activity, an unknown hash, or indexing delay.",
        })
        return
    messages = []
    for record in records:
        if not isinstance(record, dict):
            json_out({"Error": "AxelarGMPMalformed", "Message": "GMP record was not an object", "API": GMP_API, "TxHash": tx_hash})
            return
        call = record.get("call") or {}
        if not isinstance(call, dict):
            json_out({"Error": "AxelarGMPMalformed", "Message": "GMP call was not an object", "API": GMP_API, "TxHash": tx_hash})
            return
        return_values = call.get("returnValues") or {}
        if not isinstance(return_values, dict):
            json_out({"Error": "AxelarGMPMalformed", "Message": "GMP returnValues was not an object", "API": GMP_API, "TxHash": tx_hash})
            return
        executed = record.get("executed") or {}
        if not isinstance(executed, dict):
            executed = {}
        executed_tx = executed.get("transaction") or {}
        if not isinstance(executed_tx, dict):
            executed_tx = {}
        message = {
            "status": record.get("status"),
            "simplified_status": record.get("simplified_status"),
            "source_chain": call.get("chain") or return_values.get("sourceChain"),
            "destination_chain": return_values.get("destinationChain"),
            "message_id": return_values.get("messageId"),
            "tx_hash": call.get("transactionHash"),
            "executed_tx_hash": executed_tx.get("hash"),
            "time_spent_seconds": (record.get("time_spent") or {}).get("total") if isinstance(record.get("time_spent") or {}, dict) else None,
        }
        if not any(message.values()):
            json_out({"Error": "AxelarGMPMalformed", "Message": "GMP record contained no recognized evidence fields", "API": GMP_API, "TxHash": tx_hash})
            return
        messages.append(message)
    json_out({
        "TxHash": tx_hash,
        "Found": True,
        "MessageCount": len(messages),
        "Messages": messages,
        "Source": GMP_API,
        "FetchedAt": _now(),
        "Capability": "Axelar GMP-index search only",
        "TokenTransferCertified": False,
    })


COMMANDS = {
    "bridge-status": lambda: tool_bridge_status(*sys.argv[2:]),
    "bridge-tx": lambda: tool_bridge_tx(sys.argv[2]) if len(sys.argv) >= 3 else usage_out(
        "bridge-tx", "bridge-tx TXHASH  (source-chain hash for Axelar GMP-index search)"
    ),
}
