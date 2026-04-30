#!/usr/bin/env python3
"""
xrpl-hermes — Place a DEX limit order (OfferCreate).

Sells 10 XRP for 5 USD on the XRPL DEX testnet.

Usage:
    export XRPL_SEED=sEd7...
    python3 example-create-offer.py
"""

import os
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import OfferCreate
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.wallet import Wallet
from xrpl.transaction import submit_and_wait
from xrpl.utils import xrp_to_drops

TESTNET_URL = "https://s.altnet.rippletest.net:51234"

SELL_XRP = 10           # XRP to sell
BUY_USD = "5"           # USD to receive
USD_ISSUER = "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe"


def main():
    seed = os.environ.get("XRPL_SEED")
    if not seed:
        print("Set XRPL_SEED environment variable")
        return

    client = JsonRpcClient(TESTNET_URL)
    wallet = Wallet.from_seed(seed)

    print(f"Account: {wallet.classic_address}")
    print(f"Sell:    {SELL_XRP} XRP")
    print(f"Buy:     {BUY_USD} USD")

    tx = OfferCreate(
        account=wallet.classic_address,
        taker_gets=xrp_to_drops(SELL_XRP),
        taker_pays=IssuedCurrencyAmount(
            currency="USD",
            issuer=USD_ISSUER,
            value=BUY_USD,
        ),
    )

    response = submit_and_wait(tx, client, wallet)
    result = response.result
    meta = result["meta"]["TransactionResult"]

    print(f"Tx:     {result['hash']}")
    print(f"Result: {meta}")
    if meta == "tesSUCCESS":
        print("Offer placed — check order book with: book-offers XRP USD:rISSUER")


if __name__ == "__main__":
    main()
