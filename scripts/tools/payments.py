#!/usr/bin/env python3
"""Payment tools: XRP/token payments, cross-currency payments, path finding."""
from ._shared import (
    _request, json_out, note_out, json_tx_out, parse_amount_arg, usage_out,
    validate_issued_currency_value,
    IssuedCurrencyAmount, _dispatch_build, make_amount,
    Payment, RipplePathFind, build_memos, to_uint32,
)

def tool_build_payment(frm: str, to: str, amount: str, cur: str = None,
                       iss: str = None, tag: int = None, memo: str = None,
                       source_tag: int = None, dest_tag: int = None):
    try:
        if cur and cur.upper() != "XRP" and iss:
            # 3-char codes are case-sensitive on-ledger, so `cur` passes through as typed.
            amt = IssuedCurrencyAmount(
                currency=cur, issuer=iss,
                value=validate_issued_currency_value(amount),
            )
        else:
            amt = parse_amount_arg(amount)
    except ValueError as exc:
        usage_out("build-payment",
                  "build-payment --from rSRC --to rDST --amount DROPS "
                  "[--cur CUR --iss rISSUER] | --amount CUR:ISSUER:VALUE. "
                  f"{exc}")
        return
    # `--dest-tag` is the explicit destination tag; `--tag` stays a back-compat alias for it.
    destination_tag = to_uint32(dest_tag if dest_tag is not None else tag, "destination tag")
    src_tag = to_uint32(source_tag, "source tag")
    kwargs: dict = dict(account=frm, destination=to, amount=amt)
    if destination_tag is not None:
        kwargs["destination_tag"] = destination_tag
    if src_tag is not None:
        kwargs["source_tag"] = src_tag
    memos = build_memos(memo)
    if memos:
        kwargs["memos"] = memos
    tx = Payment(**kwargs)
    note_out("# Payment TX JSON - signer-ready JSON - paste into Xaman Developer tab")
    if isinstance(amt, str):
        note_out(f"# Amount is {amt} drops (XRP amounts are integer drops; 1 XRP = 1000000 drops)")
    json_tx_out(tx)

def tool_build_cross_currency_payment(frm: str, to: str, deliver: str, send_max: str,
                                       paths: str = None, dest_tag: str = None,
                                       currency: str = None, issuer: str = None,
                                       source_tag: str = None, memo: str = None):
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
    destination_tag = to_uint32(dest_tag, "destination tag")
    if destination_tag is not None:
        kwargs["destination_tag"] = destination_tag
    src_tag = to_uint32(source_tag, "source tag")
    if src_tag is not None:
        kwargs["source_tag"] = src_tag
    memos = build_memos(memo)
    if memos:
        kwargs["memos"] = memos
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
