#!/usr/bin/env python3
"""Clawback tool."""
from ._shared import (
    json_out, note_out, json_tx_out, usage_out, IssuedCurrencyAmount,
    normalize_currency_code, validate_positive_issued_value, validate_xrpl_address,
    _dispatch_build, Clawback,
)

def tool_build_clawback(frm: str, destination: str, currency: str,
                         amount: str, memo: str = None):
    # float() accepted 'nan' and turned '1e400' into inf, so both passed the
    # positivity guard and reached the payload. .upper() on the code retargeted
    # case-sensitive 3-char codes and rejected every 4-20 char symbol outright.
    try:
        currency_code = normalize_currency_code(currency)
        if currency_code == "XRP":
            raise ValueError("XRP is native and cannot be clawed back as an issued currency")
        amount_obj = IssuedCurrencyAmount(
            currency=currency_code,
            issuer=validate_xrpl_address(destination, "holder account"),
            value=validate_positive_issued_value(amount),
        )
    except ValueError as exc:
        usage_out("build-clawback",
                  "build-clawback --from rISSUER --destination rHOLDER --currency CUR "
                  f"--amount VALUE. {exc}")
        return
    kwargs: dict = dict(account=frm, amount=amount_obj)
    if memo:
        memo_hex = memo.encode("utf-8").hex().upper()
        from xrpl.models.transactions.transaction import Memo
        kwargs["memos"] = [Memo(memo_data=memo_hex)]
    tx = Clawback(**kwargs)
    note_out("# Clawback TX JSON - signer-ready JSON")
    json_tx_out(tx)

COMMANDS = {
    "build-clawback": lambda: _dispatch_build(4, tool_build_clawback),
}
