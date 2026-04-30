#!/usr/bin/env python3
"""
DEPRECATED: Use scripts/xrpl_tools.py instead (same functionality + more tools).

XRPL Transaction Builder — XRPL-Hermes Companion Script (LEGACY)
All functionality is now in xrpl_tools.py. This file kept for backward compatibility.

Usage (redirected):
  python3 xrpl_tools.py account rADDRESS
  python3 xrpl_tools.py build-payment --from rADDR --to rADDR --amount 1000000
  python3 xrpl_tools.py decode TX_BLOB
"""

import json, sys
from typing import Optional
from decimal import Decimal

try:
    import xrpl
    from xrpl.models.requests import AccountInfo, AccountLines
    from xrpl.clients import JsonRpcClient
    from xrpl.utils import drops_to_xrp, xrp_to_drops
    from xrpl.models.transactions import Payment, TrustSet
    from xrpl.models.currencies import IssuedCurrency
except ImportError as e:
    print(f'ERROR: missing xrpl-py ({e}). Run: uv pip install xrpl-py')
    sys.exit(1)

CLIENT = JsonRpcClient("https://xrplcluster.com")


def fmt_xrp(drops_val) -> str:
    return f"{drops_to_xrp(str(drops_val)):,.6f} XRP"


def short_addr(addr: str) -> str:
    return f"{addr[:8]}...{addr[-6:]}"


def cmd_account(address: str):
    req = AccountInfo(account=address, ledger_index="validated")
    resp = CLIENT.request(req)
    data = resp.result.get("account_data", {})
    bal = int(data.get("Balance", 0))
    flags = data.get("Flags", 0)
    seq = data.get("Sequence", 0)
    owner = data.get("OwnerCount", 0)
    reserved = Decimal("1") + Decimal("0.2") * Decimal(owner)  # current: 1 XRP base + 0.2 XRP per object (query server for live)
    spendable = drops_to_xrp(str(bal)) - reserved
    print(f"Account:   {address}")
    print(f"Balance:   {fmt_xrp(bal)}")
    print(f"Reserved:  {reserved:.2f} XRP ({owner} objects)")
    print(f"Spendable: {spendable:.6f} XRP")
    print(f"Sequence:  {seq}")
    print(f"Flags:     {flags}")


def cmd_trustlines(address: str, currency: Optional[str] = None):
    req = AccountLines(account=address, ledger_index="validated")
    resp = CLIENT.request(req)
    lines = resp.result.get("lines", [])
    if currency:
        lines = [l for l in lines if l.get("currency", "").upper() == currency.upper()]
    if not lines:
        print("No matching trust lines.")
        return
    for l in lines:
        cur = l.get("currency", "??")
        iss = l.get("account", "??")
        bal = float(l.get("balance", 0))
        lim = float(l.get("limit", 0))
        print(f"{cur:12s}  {bal:>20,.6f}  / limit {lim:,.0f}  ({short_addr(iss)})")


def cmd_build_payment(frm: str, to: str, amount: str):
    tx = Payment(account=frm, destination=to, amount=amount)
    print("# Transaction JSON — sign with Xaman/Joey")
    print(json.dumps(tx.to_xrpl(), indent=2))


def cmd_build_trustset(frm: str, currency: str, issuer: str):
    cur = IssuedCurrency(currency=currency, issuer=issuer)
    tx = TrustSet(account=frm, limit_amount=cur)
    print("# TrustSet JSON — sign with Xaman/Joey")
    print(json.dumps(tx.to_xrpl(), indent=2))


def cmd_decode(blob: str):
    from xrpl.binary_codec import decode
    try:
        print(json.dumps(decode(blob), indent=2))
    except Exception as e:
        print(f"Decode error: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1].lower()
    if cmd in ("account", "balance") and len(sys.argv) >= 3:
        cmd_account(sys.argv[2])
    elif cmd == "trustlines":
        cur = sys.argv[3] if len(sys.argv) >= 4 else None
        cmd_trustlines(sys.argv[2], cur)
    elif cmd == "build" and len(sys.argv) >= 3:
        tx_type = sys.argv[2].upper()
        kwargs = {}
        for i in range(3, len(sys.argv) - 1, 2):
            k = sys.argv[i].lstrip("--").replace("-", "_")
            v = sys.argv[i + 1]
            kwargs[k] = v
        if tx_type == "PAYMENT":
            cmd_build_payment(kwargs.get("from", ""), kwargs.get("to", ""), kwargs.get("amount", "1000000"))
        elif tx_type == "TRUSTSET":
            cmd_build_trustset(kwargs.get("from", ""), kwargs.get("currency", "XRP"), kwargs.get("issuer", ""))
        else:
            print(f"Unknown tx type: {tx_type}")
    elif cmd == "decode" and len(sys.argv) >= 3:
        cmd_decode(sys.argv[2])
    else:
        print(__doc__)
