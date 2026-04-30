#!/usr/bin/env python3
"""
☤ xrpl-hermes — Build and submit an XRP payment.

This example constructs a Payment transaction, signs it, and submits
to the XRPL testnet. Replace the seed and destination with your own.

Usage:
    export XRPL_SEED=sEd7...
    python3 example-build-payment.py
"""

import os
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import Payment
from xrpl.wallet import Wallet
from xrpl.transaction import submit_and_wait
from xrpl.utils import xrp_to_drops

TESTNET_URL = "https://s.altnet.rippletest.net:51234"
DESTINATION = "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe"


def main():
    seed = os.environ.get("XRPL_SEED")
    if not seed:
        print("❌ Set XRPL_SEED environment variable")
        print("   Get a testnet wallet: https://faucet.altnet.rippletest.net")
        return

    client = JsonRpcClient(TESTNET_URL)
    wallet = Wallet.from_seed(seed)

    print(f"From: {wallet.classic_address}")
    print(f"To:   {DESTINATION}")
    print(f"Amt:  10 XRP")

    tx = Payment(
        account=wallet.classic_address,
        destination=DESTINATION,
        amount=xrp_to_drops(10),
    )

    response = submit_and_wait(tx, client, wallet)
    result = response.result
    tx_hash = result["hash"]
    meta = result["meta"]["TransactionResult"]

    print(f"Tx:    {tx_hash}")
    print(f"Result: {meta}")
    print(f"Explorer: https://testnet.xrpl.org/transactions/{tx_hash}")


if __name__ == "__main__":
    main()
