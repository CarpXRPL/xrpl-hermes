#!/usr/bin/env python3
"""Payment tools: XRP/token payments, cross-currency payments, path finding."""
from ._shared import (
    _request, json_out, note_out, json_tx_out, parse_amount_arg, usage_out,
    validate_positive_issued_value, validate_positive_amount,
    normalize_currency_code, validate_xrpl_address,
    IssuedCurrencyAmount, _dispatch_build, make_amount,
    Payment, RipplePathFind, build_memos, to_uint32,
)

def tool_build_payment(frm: str, to: str, amount: str, cur: str = None,
                       iss: str = None, tag: int = None, memo: str = None,
                       source_tag: int = None, dest_tag: int = None):
    try:
        native = not cur or cur == "XRP"
        if not native and not iss:
            # --cur used to be dropped when --iss was absent, so a token payment
            # silently became an XRP payment for the same numeric value.
            raise ValueError(f"--cur {cur} also needs --iss rISSUER (or use CUR:ISSUER:VALUE).")
        if iss and native:
            raise ValueError("--iss needs a matching --cur naming the issued currency.")
        if not native:
            # normalize_currency_code preserves case-sensitive 3-char codes and
            # hexifies 4-20 char symbols, which have no 3-byte slot on-ledger.
            amt = IssuedCurrencyAmount(
                currency=normalize_currency_code(cur),
                issuer=validate_xrpl_address(iss, "issuer"),
                value=validate_positive_issued_value(amount),
            )
        else:
            amt = validate_positive_amount(parse_amount_arg(amount))
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
    # Every branch here used to fall through to the raw argument on a malformed
    # input, so a decimal XRP amount reached the payload verbatim; the --currency
    # branch additionally uppercased a case-sensitive code.
    try:
        if bool(currency) != bool(issuer):
            raise ValueError("--currency and --issuer must be supplied together")
        if currency and issuer:
            if currency == "XRP":
                raise ValueError("XRP does not take an issuer")
            if ":" in deliver or "/" in deliver:
                raise ValueError("use either --currency/--issuer or an encoded --deliver amount, not both")
            amount = IssuedCurrencyAmount(
                currency=normalize_currency_code(currency),
                issuer=validate_xrpl_address(issuer, "issuer"),
                value=validate_positive_issued_value(deliver),
            )
        else:
            amount = validate_positive_amount(parse_amount_arg(deliver))
        send_max_val = validate_positive_amount(parse_amount_arg(send_max))
    except ValueError as exc:
        usage_out("build-cross-currency-payment",
                  "build-cross-currency-payment --from rSRC --to rDST --deliver AMOUNT "
                  "--send-max AMOUNT: amounts are integer drops or CUR:ISSUER:VALUE. "
                  f"{exc}")
        return

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
    try:
        dest_amt = make_amount(cur, iss, amount)
        resp = _request(RipplePathFind(source_account=src, destination_account=dest,
                                       destination_amount=dest_amt))
        alts = resp.result.get("alternatives", [])
        json_out({"SourceAccount": src, "DestinationAccount": dest,
                  "DestinationAmount": dest_amt, "PathCount": len(alts),
                  "Alternatives": alts})
    except ValueError as e:
        json_out({"Error": "InvalidAmount", "Message": str(e)})
    except Exception as e:
        json_out({"Error": "PathFindError", "Message": str(e)})

COMMANDS = {
    "build-payment": lambda: _dispatch_build(3, tool_build_payment),
    "build-cross-currency-payment": lambda: _dispatch_build(4, tool_build_cross_currency_payment),
}
