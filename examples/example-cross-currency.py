#!/usr/bin/env python3
"""
xrpl-hermes — Cross-currency payment via DEX path-finding.

Sends USD to destination while paying with XRP — XRPL DEX auto-converts.
Uses path-find to discover routes before building the payment.

Usage:
    export XRPL_SEED=sEd7...
    python3 example-cross-currency.py
"""

import os
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import RipplePathFind
from xrpl.models.transactions import Payment
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.wallet import Wallet
from xrpl.transaction import submit_and_wait
from xrpl.utils import xrp_to_drops

TESTNET_URL = "https://s.altnet.rippletest.net:51234"

DESTINATION = "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe"
DELIVER_USD = "10"
USD_ISSUER = "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh"
# Max XRP to spend (in drops) — slippage buffer
SEND_MAX_XRP = 25


def main():
    seed = os.environ.get("XRPL_SEED")
    if not seed:
        print("Set XRPL_SEED environment variable")
        return

    client = JsonRpcClient(TESTNET_URL)
    wallet = Wallet.from_seed(seed)

    print(f"Sender:  {wallet.classic_address}")
    print(f"Dest:    {DESTINATION}")
    print(f"Deliver: {DELIVER_USD} USD, paying with up to {SEND_MAX_XRP} XRP")

    # Step 1: Find paths
    dest_amount = IssuedCurrencyAmount(
        currency="USD", issuer=USD_ISSUER, value=DELIVER_USD
    )
    path_req = RipplePathFind(
        source_account=wallet.classic_address,
        destination_account=DESTINATION,
        destination_amount=dest_amount,
    )
    path_resp = client.request(path_req)
    alternatives = path_resp.result.get("alternatives", [])

    if not alternatives:
        print("No path found — ensure USD trust line exists between sender and issuer")
        return

    best_path = alternatives[0]
    print(f"Path found: {len(alternatives)} alternative(s)")

    # Step 2: Build Payment with send_max and paths
    tx = Payment(
        account=wallet.classic_address,
        destination=DESTINATION,
        amount=dest_amount,
        send_max=xrp_to_drops(SEND_MAX_XRP),
        paths=best_path.get("paths_computed", []),
    )

    response = submit_and_wait(tx, client, wallet)
    result = response.result
    meta = result["meta"]["TransactionResult"]

    print(f"Tx:     {result['hash']}")
    print(f"Result: {meta}")


if __name__ == "__main__":
    main()
