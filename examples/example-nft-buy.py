#!/usr/bin/env python3
"""
xrpl-hermes — Accept an NFT sell offer (buy an NFT).

Lists open sell offers for a given NFT ID, then accepts the cheapest one.

Usage:
    export XRPL_SEED=sEd7...      # buyer seed
    export NFT_ID=00080000...     # the NFT token ID
    python3 example-nft-buy.py
"""

import os
import json
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import NFTSellOffers
from xrpl.models.transactions import NFTokenAcceptOffer
from xrpl.wallet import Wallet
from xrpl.transaction import submit_and_wait

TESTNET_URL = "https://s.altnet.rippletest.net:51234"


def main():
    seed = os.environ.get("XRPL_SEED")
    nft_id = os.environ.get("NFT_ID")

    if not seed:
        print("Set XRPL_SEED environment variable")
        return
    if not nft_id:
        print("Set NFT_ID environment variable (the 64-char NFT token ID)")
        return

    client = JsonRpcClient(TESTNET_URL)
    wallet = Wallet.from_seed(seed)

    print(f"Buyer: {wallet.classic_address}")
    print(f"NFT:   {nft_id}")

    # Fetch sell offers
    try:
        offers_resp = client.request(NFTSellOffers(nft_id=nft_id))
    except Exception as e:
        print(f"Failed to fetch sell offers: {e}")
        return

    offers = offers_resp.result.get("offers", [])
    if not offers:
        print("No sell offers found for this NFT")
        return

    print(f"Found {len(offers)} sell offer(s):")
    for o in offers:
        amt = o.get("amount", "0")
        drops = int(amt) if isinstance(amt, str) else 0
        print(f"  Offer {o['nft_offer_index']}: {drops / 1_000_000:.6f} XRP")

    # Accept cheapest offer
    cheapest = min(offers, key=lambda o: int(o.get("amount", "0")))
    offer_id = cheapest["nft_offer_index"]
    price_drops = cheapest.get("amount", "0")

    print(f"\nAccepting offer {offer_id} for {int(price_drops)/1_000_000:.6f} XRP")

    tx = NFTokenAcceptOffer(
        account=wallet.classic_address,
        nftoken_sell_offer=offer_id,
    )

    response = submit_and_wait(tx, client, wallet)
    result = response.result
    meta = result["meta"]["TransactionResult"]

    print(f"Tx:     {result['hash']}")
    print(f"Result: {meta}")
    if meta == "tesSUCCESS":
        print("NFT purchased successfully!")


if __name__ == "__main__":
    main()
