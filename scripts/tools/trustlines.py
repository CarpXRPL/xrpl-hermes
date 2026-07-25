#!/usr/bin/env python3
"""Trustline tools."""
from ._shared import (
    _request, json_out, note_out, json_tx_out, parse_amount_arg,
    IssuedCurrencyAmount, usage_out, _dispatch_build,
    normalize_currency_code, validate_nonnegative_issued_value, validate_xrpl_address,
    AccountLines, TrustSet,
)

def tool_trustlines(address: str, currency: str = None):
    all_lines = []
    marker = None
    while True:
        try:
            resp = _request(AccountLines(account=address, ledger_index="validated", marker=marker))
        except Exception as e:
            json_out({"Error": "AccountLinesError", "Message": str(e), "Account": address})
            return
        data = resp.result
        all_lines.extend(data.get("lines", []))
        marker = data.get("marker")
        if not marker:
            break
    wanted = None
    if currency:
        # Uppercasing the filter could never match a 4-20 char symbol, whose
        # on-ledger code is 160-bit hex, and retargeted case-sensitive 3-char codes.
        try:
            wanted = normalize_currency_code(currency)
        except ValueError as e:
            usage_out("trustlines", f"trustlines rADDRESS [CURRENCY]. {e}")
            return
        filtered = [l for l in all_lines if l.get("currency", "") == wanted]
        if not filtered:
            json_out({"Account": address, "Currency": wanted, "TrustLines": []})
            return
        all_lines = filtered
    json_out({"Account": address, "Currency": wanted,
              "TrustLineCount": len(all_lines), "TrustLines": all_lines})

def tool_build_trustset(frm: str, currency: str, issuer: str, value: str = "1000000000"):
    try:
        currency_code = normalize_currency_code(currency)
        if currency_code == "XRP":
            raise ValueError("XRP is native and cannot be a trust line currency")
        cur = IssuedCurrencyAmount(
            currency=currency_code,
            issuer=validate_xrpl_address(issuer, "issuer"),
            value=validate_nonnegative_issued_value(value),
        )
    except ValueError as exc:
        usage_out("build-trustset",
                  "build-trustset --from rSRC --currency CUR --issuer rISSUER "
                  f"[--value LIMIT]. {exc}")
        return
    tx = TrustSet(account=frm, limit_amount=cur)
    note_out("# TrustSet TX JSON - signer-ready JSON")
    json_tx_out(tx)

COMMANDS = {
    "trustlines": lambda: tool_trustlines(__import__('sys').argv[2], __import__('sys').argv[3] if len(__import__('sys').argv) >= 4 else None) if len(__import__('sys').argv) >= 3 else usage_out("trustlines", "trustlines rADDRESS [CURRENCY]"),
    "build-trustset": lambda: _dispatch_build(2, tool_build_trustset),
}
