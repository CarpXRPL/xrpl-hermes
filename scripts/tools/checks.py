#!/usr/bin/env python3
"""Check tools: create, cash, cancel."""
from ._shared import (
    note_out, json_tx_out, usage_out, parse_amount_arg, validate_positive_amount,
    _dispatch_build,
    CheckCreate, CheckCash, CheckCancel,
)

_AMOUNT_USAGE = "amounts are integer drops (1 XRP = 1000000 drops) or CUR:ISSUER:VALUE"

def tool_build_check_create(frm: str, to: str, amount: str, invoice_id: str = None,
                             expiry: str = None):
    # The inline split built a raw dict, which xrpl-py passes through unvalidated,
    # and let a decimal XRP amount reach the payload verbatim.
    try:
        send_max = validate_positive_amount(parse_amount_arg(amount))
    except ValueError as exc:
        usage_out("build-check-create",
                  f"build-check-create --from rSRC --to rDST --amount VALUE: {_AMOUNT_USAGE}. {exc}")
        return
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
    try:
        if amount: kwargs["amount"] = validate_positive_amount(parse_amount_arg(amount))
        if deliver_min: kwargs["deliver_min"] = validate_positive_amount(parse_amount_arg(deliver_min))
    except ValueError as exc:
        usage_out("build-check-cash",
                  f"build-check-cash --from rSRC --check-id ID --amount VALUE: {_AMOUNT_USAGE}. {exc}")
        return
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
