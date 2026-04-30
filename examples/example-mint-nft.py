#!/usr/bin/env python3
"""
☤ xrpl-hermes — Mint an NFT (XLS-20) on XRPL testnet.

Creates an NFT with a URI pointing to metadata on Arweave/IPFS.
Replace the seed with your own testnet wallet.

Usage:
    export XRPL_SEED=sEd7...
    python3 example-mint-nft.py
"""

import os
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import NFTokenMint
from xrpl.models.transactions import NFTokenMintFlag
from xrpl.wallet import Wallet
from xrpl.transaction import submit_and_wait
from xrpl.utils import xrp_to_drops

TESTNET_URL = "https://s.altnet.rippletest.net:51234"


def main():
    seed = os.environ.get("XRPL_SEED")
    if not seed:
        print("❌ Set XRPL_SEED environment variable")
        print("   Get a testnet wallet: https://faucet.altnet.rippletest.net")
        return

    client = JsonRpcClient(TESTNET_URL)
    wallet = Wallet.from_seed(seed)

    # NFT metadata URI (Arweave, IPFS, or HTTPS)
    uri = "https://arweave.net/sample-nft-metadata.json"
    uri_hex = uri.encode("utf-8").hex().upper()

    print(f"Wallet: {wallet.classic_address}")
    print(f"URI:    {uri}")
    print(f"Flags:  burnable (1) + only XRP (8)")

    tx = NFTokenMint(
        account=wallet.classic_address,
        uri=uri_hex,
        flags=[NFTokenMintFlag.TF_BURNABLE, NFTokenMintFlag.TF_ONLY_XRP],
        transfer_fee=0,
        nftoken_taxon=0,
    )

    response = submit_and_wait(tx, client, wallet)
    result = response.result
    tx_hash = result["hash"]
    meta = result["meta"]

    # Extract NFT ID from metadata
    nft_id = None
    for node in meta.get("AffectedNodes", []):
        created = node.get("CreatedNode")
        if created and created.get("LedgerEntryType") == "NFTokenPage":
            nft_id = created["NewFields"].get("NFTokens", [{}])[0].get("NFToken", {}).get("NFTokenID")

    print(f"Tx:     {tx_hash}")
    print(f"Result: {meta['TransactionResult']}")
    if nft_id:
        print(f"NFT ID: {nft_id}")
    print(f"Explorer: https://testnet.xrpl.org/transactions/{tx_hash}")


if __name__ == "__main__":
    main()
