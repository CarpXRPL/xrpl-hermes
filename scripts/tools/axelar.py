#!/usr/bin/env python3
"""Axelar bridge tools: read-only status for XRPL <-> XRPL EVM bridging.

Uses the public Axelarscan APIs. Never builds, signs, or submits bridge
transactions.
"""
from ._shared import json_out, usage_out
import httpx, sys

CHAINS_API = "https://api.axelarscan.io/api/getChains"
GMP_API = "https://api.gmp.axelarscan.io"
XRPL_CHAIN_IDS = ("xrpl", "xrpl-evm")


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
        resp = httpx.get(CHAINS_API, timeout=20)
        resp.raise_for_status()
        chains = resp.json()
    except Exception as e:
        json_out({"Error": "AxelarChainsUnavailable", "Message": str(e), "API": CHAINS_API})
        return
    by_id = {str(c.get("id", "")).lower(): c for c in chains}
    found, missing = {}, []
    for cid in wanted:
        if cid in by_id:
            found[cid] = _chain_summary(by_id[cid])
        else:
            missing.append(cid)
    json_out({
        "Source": CHAINS_API,
        "Chains": found,
        "MissingChains": missing,
        "Note": "Read-only registration/gateway data from Axelarscan. A listed, non-deprecated "
                "chain entry means Axelar currently serves the route; verify amounts and fees in "
                "your bridge UI or the Axelar docs before moving funds.",
    })


def tool_bridge_tx(tx_hash: str):
    try:
        resp = httpx.post(GMP_API, json={"method": "searchGMP", "txHash": tx_hash, "size": 5}, timeout=20)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as e:
        json_out({"Error": "AxelarGMPUnavailable", "Message": str(e), "API": GMP_API, "TxHash": tx_hash})
        return
    records = payload.get("data") or []
    if not records:
        json_out({"TxHash": tx_hash, "Found": False, "Source": GMP_API,
                  "Message": "No Axelar GMP message found for this hash (not a bridge tx, or not yet indexed)."})
        return
    messages = []
    for rec in records:
        call = rec.get("call") or {}
        rv = call.get("returnValues") or {}
        messages.append({
            "status": rec.get("status"),
            "simplified_status": rec.get("simplified_status"),
            "source_chain": call.get("chain") or rv.get("sourceChain"),
            "destination_chain": rv.get("destinationChain"),
            "message_id": rv.get("messageId"),
            "tx_hash": call.get("transactionHash"),
            "executed_tx_hash": ((rec.get("executed") or {}).get("transaction") or {}).get("hash"),
            "time_spent_seconds": (rec.get("time_spent") or {}).get("total"),
        })
    json_out({"TxHash": tx_hash, "Found": True, "MessageCount": len(messages),
              "Messages": messages, "Source": GMP_API})


COMMANDS = {
    "bridge-status": lambda: tool_bridge_status(*sys.argv[2:]),
    "bridge-tx": lambda: tool_bridge_tx(sys.argv[2]) if len(sys.argv) >= 3 else usage_out(
        "bridge-tx", "bridge-tx TXHASH  (source-chain tx hash of an Axelar bridge transfer)"),
}
