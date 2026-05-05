#!/usr/bin/env python3
"""Check tools: create, cash, cancel."""
from ._shared import (
    note_out, json_tx_out, _dispatch_build,
    CheckCreate, CheckCash, CheckCancel,
)

def tool_build_check_create(frm: str, to: str, amount: str, invoice_id: str = None,
                             expiry: str = None):
    parts = amount.split(":", 2)
    if len(parts) == 3:
        send_max = {"currency": parts[0], "issuer": parts[1], "value": parts[2]}
    else:
        send_max = amount
    kwargs = dict(account=frm, destination=to, send_max=send_max)
    if invoice_id: kwargs["invoice_id"] = invoice_id
    if expiry: kwargs["expiration"] = int(expiry)
    tx = CheckCreate(**kwargs)
    note_out("# CheckCreate TX JSON - signer-ready JSON")
    json_tx_out(tx)

def tool_build_check_cash(frm: str, check_id: str, amount: str = None,
                           deliver_min: str = None):
    if not amount and not deliver_min:
        print("CheckCash requires --amount OR --deliver-min")
        return
    kwargs = dict(account=frm, check_id=check_id)
    if amount: kwargs["amount"] = amount
    if deliver_min: kwargs["deliver_min"] = deliver_min
    tx = CheckCash(**kwargs)
    note_out("# CheckCash TX JSON - signer-ready JSON")
    json_tx_out(tx)

def tool_build_check_cancel(frm: str, check_id: str):
    tx = CheckCancel(account=frm, check_id=check_id)
    note_out("# CheckCancel TX JSON - signer-ready JSON")
    json_tx_out(tx)

COMMANDS = {
    "build-check-create": lambda: _dispatch_build(3, tool_build_check_create),
    "build-check-cash": lambda: _dispatch_build(2, tool_build_check_cash),
    "build-check-cancel": lambda: _dispatch_build(2, tool_build_check_cancel),
}
