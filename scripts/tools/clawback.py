#!/usr/bin/env python3
"""Clawback tool."""
from ._shared import (
    json_out, note_out, json_tx_out, IssuedCurrencyAmount, _dispatch_build, Clawback,
)
import re

def tool_build_clawback(frm: str, destination: str, currency: str,
                         amount: str, issuer: str = None, memo: str = None):
    try:
        amt_val = float(amount)
        if amt_val <= 0:
            print("Error: amount must be positive")
            return
    except ValueError:
        print(f"Error: invalid amount '{amount}'")
        return
    cur = currency.upper()
    if not (re.match(r'^[A-Z0-9]{3}$', cur) or re.match(r'^[0-9A-F]{40}$', cur)):
        print(f"Error: currency must be 3-letter ISO code or 40-char hex, got '{currency}'")
        return
    amount_obj = IssuedCurrencyAmount(currency=cur, issuer=destination, value=amount)
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
