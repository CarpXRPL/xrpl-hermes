#!/usr/bin/env python3
"""
xrpl-hermes — Deposit into an AMM pool (AMMDeposit).

Deposits XRP into an existing XRP/USD AMM pool on testnet.
AMMDeposit requires the AMM to already exist (use build-amm-create first).

Usage:
    export XRPL_SEED=sEd7...
    python3 example-amm-deposit.py
"""

import os
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.transaction import submit_and_wait
from xrpl.utils import xrp_to_drops

TESTNET_URL = "https://s.altnet.rippletest.net:51234"

AMM_ASSET_CURRENCY = "USD"
AMM_ASSET_ISSUER = "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe"
DEPOSIT_XRP = 5
DEPOSIT_USD = "2.5"


def main():
    seed = os.environ.get("XRPL_SEED")
    if not seed:
        print("Set XRPL_SEED environment variable")
        return

    try:
        from xrpl.models.transactions import AMMDeposit
        from xrpl.models.transactions.amm_deposit import AMMDepositFlag
        from xrpl.models.amounts import IssuedCurrencyAmount
        from xrpl.models.currencies import XRP as XRPCurrency, IssuedCurrency
    except ImportError as e:
        print(f"xrpl-py version may not support AMMDeposit: {e}")
        print("Update with: pip install 'xrpl-py>=2.0.0'")
        return

    client = JsonRpcClient(TESTNET_URL)
    wallet = Wallet.from_seed(seed)

    print(f"Account:  {wallet.classic_address}")
    print(f"Deposit:  {DEPOSIT_XRP} XRP + {DEPOSIT_USD} USD into AMM pool")

    tx = AMMDeposit(
        account=wallet.classic_address,
        asset=XRPCurrency(),
        asset2=IssuedCurrency(currency=AMM_ASSET_CURRENCY, issuer=AMM_ASSET_ISSUER),
        amount=xrp_to_drops(DEPOSIT_XRP),
        amount2=IssuedCurrencyAmount(
            currency=AMM_ASSET_CURRENCY,
            issuer=AMM_ASSET_ISSUER,
            value=DEPOSIT_USD,
        ),
        flags=AMMDepositFlag.TF_TWO_ASSET,
    )

    response = submit_and_wait(tx, client, wallet)
    result = response.result
    meta = result["meta"]["TransactionResult"]

    print(f"Tx:     {result['hash']}")
    print(f"Result: {meta}")
    if meta == "tesSUCCESS":
        print("AMM deposit successful — you now hold LP tokens")


if __name__ == "__main__":
    main()
