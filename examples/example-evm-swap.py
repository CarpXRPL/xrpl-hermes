#!/usr/bin/env python3
"""
☤ xrpl-hermes — Simulate an ERC-20 swap on XRPL EVM Sidechain.

This script interacts with a UniswapV2-style pair on the XRPL EVM
Sidechain (chain ID 1440000). It reads reserves, calculates an output
amount, and simulates a swap. Requires web3.py.

Usage:
    export EVM_PRIVATE_KEY=0x...
    python3 example-evm-swap.py
"""

import os
from web3 import Web3
from web3.middleware import geth_poa_middleware

RPC_URL = "https://rpc.xrplevm.org"
CHAIN_ID = 1440000

# Minimal UniswapV2 Pair ABI (reserves + swap)
PAIR_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"name": "_reserve0", "type": "uint112"},
            {"name": "_reserve1", "type": "uint112"},
            {"name": "_blockTimestampLast", "type": "uint32"},
        ],
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [{"name": "amount0Out", "type": "uint256"}, {"name": "amount1Out", "type": "uint256"}, {"name": "to", "type": "address"}, {"name": "data", "type": "bytes"}],
        "name": "swap",
        "outputs": [],
        "type": "function",
    },
]

# wXRP contract (canonical address)
WXRP_ADDRESS = "0xCCccCCCc00000001000000000000000000000000"
WXRP_ABI = [
    {"constant": True, "inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "guy", "type": "address"}, {"name": "wad", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
]


def get_price_impact(reserve_in: int, reserve_out: int, amount_in: int) -> float:
    """Calculate price impact for a swap using constant product formula."""
    amount_in_with_fee = amount_in * 997
    numerator = amount_in_with_fee * reserve_out
    denominator = reserve_in * 1000 + amount_in_with_fee
    amount_out = numerator // denominator
    price_before = reserve_out / reserve_in if reserve_in > 0 else 0
    price_after = (reserve_out - amount_out) / (reserve_in + amount_in) if (reserve_in + amount_in) > 0 else 0
    impact = ((price_before - price_after) / price_before * 100) if price_before > 0 else 0
    return amount_out / 10**18, impact


def main():
    private_key = os.environ.get("EVM_PRIVATE_KEY")
    if not private_key:
        print("❌ Set EVM_PRIVATE_KEY environment variable")
        print("   (0x-prefixed hex private key for XRPL EVM Sidechain)")
        return

    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    account = w3.eth.account.from_key(private_key)
    print(f"Wallet: {account.address}")
    print(f"Chain:  {w3.eth.chain_id} ({'XRPL EVM' if w3.eth.chain_id == CHAIN_ID else 'unexpected'})")
    print(f"Block:  {w3.eth.block_number}")

    # Example pair address — replace with a real pair on XRPL EVM
    PAIR_ADDRESS = "0x0000000000000000000000000000000000000000"
    pair = w3.eth.contract(address=Web3.to_checksum_address(PAIR_ADDRESS), abi=PAIR_ABI)

    reserves = pair.functions.getReserves().call()
    reserve0, reserve1 = reserves[0], reserves[1]
    print(f"\nPair reserves: {reserve0 / 10**18:.4f} / {reserve1 / 10**18:.4f}")

    # Simulate a swap of 100 tokens
    amount_in = 100 * 10**18
    amount_out, impact = get_price_impact(reserve0, reserve1, amount_in)
    print(f"\nSwap simulation:")
    print(f"  Input:  {amount_in / 10**18:.2f} tokens")
    print(f"  Output: {amount_out:.4f} tokens")
    print(f"  Price impact: {impact:.2f}%")

    # Check wXRP balance
    wxrp = w3.eth.contract(address=Web3.to_checksum_address(WXRP_ADDRESS), abi=WXRP_ABI)
    balance = wxrp.functions.balanceOf(account.address).call()
    print(f"\nwXRP balance: {balance / 10**18:.4f}")

    print("\nTo execute a real swap, deploy a pair contract and replace PAIR_ADDRESS.")


if __name__ == "__main__":
    main()
