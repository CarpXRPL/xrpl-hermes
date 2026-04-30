#!/usr/bin/env python3
"""
xrpl-hermes — Clawback issued tokens from a holder.

The signing account MUST be the token issuer and must have
AllowTrustLineClawback set (AccountSet asfAllowTrustLineClawback flag).

Usage:
    export XRPL_SEED=sEd_ISSUER_SEED
    python3 example-clawback.py
"""

import os
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import Clawback
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.wallet import Wallet
from xrpl.transaction import submit_and_wait

TESTNET_URL = "https://s.altnet.rippletest.net:51234"

# The holder you are clawing back from
HOLDER_ADDRESS = "rN7n3473SaZBCG4dFL83w7PB5AMxgsJ9Wn"
CURRENCY = "USD"
CLAWBACK_AMOUNT = "50"


def main():
    seed = os.environ.get("XRPL_SEED")
    if not seed:
        print("Set XRPL_SEED to the ISSUER account seed")
        return

    client = JsonRpcClient(TESTNET_URL)
    wallet = Wallet.from_seed(seed)

    print(f"Issuer:  {wallet.classic_address}")
    print(f"Holder:  {HOLDER_ADDRESS}")
    print(f"Claw:    {CLAWBACK_AMOUNT} {CURRENCY}")

    # In Clawback, amount.issuer is the HOLDER (protocol convention)
    amount_obj = IssuedCurrencyAmount(
        currency=CURRENCY,
        issuer=HOLDER_ADDRESS,
        value=CLAWBACK_AMOUNT,
    )

    tx = Clawback(
        account=wallet.classic_address,
        amount=amount_obj,
    )

    response = submit_and_wait(tx, client, wallet)
    result = response.result
    meta = result["meta"]["TransactionResult"]

    print(f"Tx:     {result['hash']}")
    print(f"Result: {meta}")
    if meta == "tesSUCCESS":
        print(f"Clawback successful: {CLAWBACK_AMOUNT} {CURRENCY} reclaimed from {HOLDER_ADDRESS}")
    elif meta == "tecNO_PERMISSION":
        print("Error: issuer does not have AllowTrustLineClawback enabled")


if __name__ == "__main__":
    main()
