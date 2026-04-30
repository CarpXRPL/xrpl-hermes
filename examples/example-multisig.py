#!/usr/bin/env python3
"""
xrpl-hermes — Multi-signature wallet setup and signing.

Step 1: Set a signer list on an account (requires 1 existing key).
Step 2: Demonstrates how to multi-sign a payment transaction.

Usage:
    export XRPL_SEED=sEd7...           # account owner seed
    export SIGNER1_SEED=sEd8...        # first signer seed
    export SIGNER2_SEED=sEd9...        # second signer seed
    python3 example-multisig.py
"""

import os
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import SignerListSet, Payment
from xrpl.models.transactions.signer_list_set import SignerEntry, SignerEntryWrapper
from xrpl.wallet import Wallet
from xrpl.transaction import submit_and_wait, sign
from xrpl.utils import xrp_to_drops

TESTNET_URL = "https://s.altnet.rippletest.net:51234"
DESTINATION = "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe"


def main():
    owner_seed = os.environ.get("XRPL_SEED")
    signer1_seed = os.environ.get("SIGNER1_SEED")
    signer2_seed = os.environ.get("SIGNER2_SEED")

    if not all([owner_seed, signer1_seed, signer2_seed]):
        print("Set XRPL_SEED, SIGNER1_SEED, and SIGNER2_SEED")
        return

    client = JsonRpcClient(TESTNET_URL)
    owner = Wallet.from_seed(owner_seed)
    signer1 = Wallet.from_seed(signer1_seed)
    signer2 = Wallet.from_seed(signer2_seed)

    print(f"Owner:   {owner.classic_address}")
    print(f"Signer1: {signer1.classic_address}")
    print(f"Signer2: {signer2.classic_address}")

    # Step 1: Set signer list (quorum=2, both signers needed)
    print("\n--- Step 1: Set signer list (quorum=2) ---")
    set_list_tx = SignerListSet(
        account=owner.classic_address,
        signer_quorum=2,
        signer_entries=[
            SignerEntryWrapper(signer_entry=SignerEntry(
                account=signer1.classic_address, signer_weight=1
            )),
            SignerEntryWrapper(signer_entry=SignerEntry(
                account=signer2.classic_address, signer_weight=1
            )),
        ],
    )
    resp = submit_and_wait(set_list_tx, client, owner)
    print(f"SignerListSet: {resp.result['meta']['TransactionResult']}")

    # Step 2: Build a payment and multi-sign it
    print("\n--- Step 2: Multi-sign a Payment ---")
    payment = Payment(
        account=owner.classic_address,
        destination=DESTINATION,
        amount=xrp_to_drops(1),
        sequence=None,  # will be filled by autofill
    )

    from xrpl.transaction import autofill, multisign
    payment = autofill(payment, client)
    sig1 = sign(payment, signer1, multisign=True)
    sig2 = sign(payment, signer2, multisign=True)
    signed_tx = multisign(payment, [sig1, sig2])

    response = client.request(
        __import__('xrpl.models.requests', fromlist=['SubmitMultisigned']).SubmitMultisigned(tx_json=signed_tx)
    )
    print(f"Multisig Payment: {response.result.get('engine_result', 'unknown')}")


if __name__ == "__main__":
    main()
