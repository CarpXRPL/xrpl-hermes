#!/usr/bin/env python3
"""Ledger tools: info, server-info, tx-info, decode, ledger-entry, submit."""
from ._shared import (
    _request, json_out, note_out, json_tx_out, drops_to_xrp, ripple_time_to_iso,
    ENDPOINTS, _dispatch_build, JsonRpcClient,
    Ledger, ServerInfo, Tx, LedgerEntry,
)
from xrpl.models.requests import SubmitOnly, SubmitMultisigned
import sys, json as json_mod

def tool_ledger(index: int = None):
    try:
        resp = _request(Ledger(ledger_index=index if index else "validated", transactions=False))
    except Exception as e:
        json_out({"Error": "LedgerError", "Message": str(e), "LedgerIndex": index})
        return
    data = resp.result.get("ledger", {})
    json_out({
        "LedgerIndex": data.get("ledger_index"),
        "LedgerHash": data.get("ledger_hash"),
        "CloseTimeHuman": data.get("close_time_human"),
        "TotalCoinsDrops": data.get("total_coins"),
        "TotalCoinsXRP": str(drops_to_xrp(str(data.get("total_coins", "0")))),
        "TransactionCount": data.get("transaction_count", 0),
        "CloseFlags": data.get("close_flags", 0),
    })

def tool_server_info():
    try:
        resp = _request(ServerInfo())
    except Exception as e:
        json_out({"Error": "ServerInfoError", "Message": str(e)})
        return
    info = resp.result.get("info", {})
    validated = info.get("validated_ledger", {})
    json_out({"BuildVersion": info.get("build_version"), "Uptime": info.get("uptime", 0),
              "CompleteLedgers": info.get("complete_ledgers"),
              "ValidatedLedger": validated, "ServerState": info.get("server_state"),
              "Info": info})

def tool_tx_info(tx_hash: str):
    try:
        resp = _request(Tx(transaction=tx_hash))
    except Exception as e:
        json_out({"Error": "TxError", "Message": str(e), "Transaction": tx_hash})
        return
    data = resp.result
    tx_json = data.get("tx_json", data)
    status = data.get("meta", {}).get("TransactionResult", "?")
    tx_type = tx_json.get("TransactionType", "?")
    account = tx_json.get("Account", "?")
    dest = tx_json.get("Destination", "")
    fee = tx_json.get("Fee", "0")
    date_value = data.get("close_time_iso") or tx_json.get("date") or data.get("date")
    json_out({"Hash": tx_hash, "TransactionType": tx_type, "Status": status,
              "Account": account, "Destination": dest or None,
              "FeeDrops": fee, "FeeXRP": str(drops_to_xrp(str(fee))),
              "LedgerIndex": data.get("ledger_index"),
              "Date": ripple_time_to_iso(date_value), "Raw": data})

def tool_decode(blob: str):
    from xrpl.core.binarycodec import decode
    try:
        decoded = decode(blob)
        json_out(decoded)
    except Exception as e:
        json_out({"Error": "DecodeError", "Message": str(e), "Blob": blob})

def tool_ledger_entry(index: str = None, account_root: str = None,
                       offer: str = None, ripple_state: str = None):
    try:
        if index:
            req = LedgerEntry(index=index, ledger_index="validated")
        elif account_root:
            req = LedgerEntry(account_root=account_root, ledger_index="validated")
        else:
            json_out({"Error": "BadArgs", "Message": "need --index or --account-root"})
            return
        resp = _request(req)
        json_out(resp.result)
    except Exception as e:
        json_out({"Error": "LedgerEntryError", "Message": str(e)})

def tool_submit(blob: str):
    try:
        resp = _request(SubmitOnly(tx_blob=blob))
        json_out(resp.result)
    except Exception as e:
        json_out({"Error": "SubmitError", "Message": str(e)})

def tool_submit_multisigned(tx_json_str: str):
    try:
        tx_obj = json_mod.loads(tx_json_str)
        resp = _request(SubmitMultisigned(tx_json=tx_obj))
        json_out(resp.result)
    except Exception as e:
        json_out({"Error": "SubmitMultisignedError", "Message": str(e)})

COMMANDS = {
    "ledger": lambda: tool_ledger(int(sys.argv[2]) if len(sys.argv) >= 3 and sys.argv[2].isdigit() else None),
    "server-info": lambda: tool_server_info(),
    "tx-info": lambda: tool_tx_info(sys.argv[2]) if len(sys.argv) >= 3 else print("Usage: tx-info TX_HASH"),
    "decode": lambda: tool_decode(sys.argv[2]) if len(sys.argv) >= 3 else print("Usage: decode TX_BLOB"),
    "ledger-entry": lambda: _dispatch_build(0, tool_ledger_entry),
    "submit": lambda: tool_submit(sys.argv[2]) if len(sys.argv) >= 3 else print("Usage: submit TX_BLOB"),
    "submit-multisigned": lambda: tool_submit_multisigned(sys.argv[2]) if len(sys.argv) >= 3 else print("Usage: submit-multisigned '{\"TransactionType\":...}'"),
}
