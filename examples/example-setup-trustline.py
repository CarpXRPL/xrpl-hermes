#!/usr/bin/env python3
"""
xrpl-hermes — Set up a trust line for an issued currency.

Usage:
    export XRPL_SEED=sEd7...
    python3 example-setup-trustline.py
"""

import os
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import TrustSet
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.wallet import Wallet
from xrpl.transaction import submit_and_wait

TESTNET_URL = "https://s.altnet.rippletest.net:51234"

# USD issued by this testnet account
CURRENCY = "USD"
ISSUER = "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe"
LIMIT = "1000000000"


def main():
    seed = os.environ.get("XRPL_SEED")
    if not seed:
        print("Set XRPL_SEED environment variable")
        print("Get a testnet wallet: https://faucet.altnet.rippletest.net")
        return

    client = JsonRpcClient(TESTNET_URL)
    wallet = Wallet.from_seed(seed)

    print(f"Account:  {wallet.classic_address}")
    print(f"Currency: {CURRENCY} issued by {ISSUER}")
    print(f"Limit:    {LIMIT}")

    tx = TrustSet(
        account=wallet.classic_address,
        limit_amount=IssuedCurrencyAmount(
            currency=CURRENCY,
            issuer=ISSUER,
            value=LIMIT,
        ),
    )

    response = submit_and_wait(tx, client, wallet)
    result = response.result
    meta = result["meta"]["TransactionResult"]

    print(f"Tx:     {result['hash']}")
    print(f"Result: {meta}")
    if meta == "tesSUCCESS":
        print(f"Trust line set: you can now receive {CURRENCY} from {ISSUER}")


if __name__ == "__main__":
    main()
