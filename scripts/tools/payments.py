#!/usr/bin/env python3
"""Payment tools: XRP/token payments, cross-currency payments, path finding."""
from ._shared import (
    _request, json_out, note_out, json_tx_out, parse_amount_arg, usage_out,
    IssuedCurrencyAmount, _dispatch_build, make_amount,
    Payment, RipplePathFind,
)

def tool_build_payment(frm: str, to: str, amount: str, cur: str = None,
                       iss: str = None, tag: int = None, memo: str = None):
    if cur and cur.upper() != "XRP" and iss:
        amt = IssuedCurrencyAmount(currency=cur, issuer=iss, value=amount)
    else:
        amt = amount
    tx = Payment(account=frm, destination=to, amount=amt,
                 destination_tag=tag if tag else None)
    note_out("# Payment TX JSON - signer-ready JSON - paste into Xaman Developer tab")
    json_tx_out(tx)

def tool_build_cross_currency_payment(frm: str, to: str, deliver: str, send_max: str,
                                       paths: str = None, dest_tag: str = None,
                                       currency: str = None, issuer: str = None):
    d_parts = deliver.split(":", 2)
    if currency and currency.upper() != "XRP" and issuer and ":" not in deliver and "/" not in deliver:
        amount = IssuedCurrencyAmount(currency=currency.upper(), issuer=issuer, value=deliver)
    elif d_parts[0].upper() == "XRP":
        amount = d_parts[1] if len(d_parts) >= 2 else deliver
    elif len(d_parts) == 3:
        amount = IssuedCurrencyAmount(currency=d_parts[0], issuer=d_parts[1], value=d_parts[2])
    else:
        amount = deliver

    sm_parts = send_max.split(":", 2)
    if sm_parts[0].upper() == "XRP":
        send_max_val = sm_parts[1] if len(sm_parts) >= 2 else send_max
    elif len(sm_parts) == 3:
        send_max_val = IssuedCurrencyAmount(currency=sm_parts[0], issuer=sm_parts[1], value=sm_parts[2])
    else:
        send_max_val = send_max

    kwargs: dict = dict(account=frm, destination=to, amount=amount, send_max=send_max_val)
    if paths:
        import json
        try: kwargs["paths"] = json.loads(paths)
        except: print(f"Warning: could not parse --paths JSON: {paths}")
    if dest_tag: kwargs["destination_tag"] = int(dest_tag)
    tx = Payment(**kwargs)
    note_out("# Cross-Currency Payment TX JSON - signer-ready JSON")
    json_tx_out(tx)

def tool_path_find(src: str, dest: str, amount: str, cur: str, iss: str = None):
    dest_amt = make_amount(cur, iss, amount)
    try:
        resp = _request(RipplePathFind(source_account=src, destination_account=dest,
                                       destination_amount=dest_amt))
        alts = resp.result.get("alternatives", [])
        json_out({"SourceAccount": src, "DestinationAccount": dest,
                  "DestinationAmount": dest_amt, "PathCount": len(alts),
                  "Alternatives": alts})
    except Exception as e:
        json_out({"Error": "PathFindError", "Message": str(e)})

COMMANDS = {
    "build-payment": lambda: _dispatch_build(3, tool_build_payment),
    "build-cross-currency-payment": lambda: _dispatch_build(4, tool_build_cross_currency_payment),
}
