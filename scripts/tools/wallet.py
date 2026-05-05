#!/usr/bin/env python3
"""Wallet utility tools: generate, from-seed, validate-address."""
from ._shared import (
    json_out, note_out,
)

def tool_wallet_generate(algorithm: str = "ed25519"):
    from xrpl.wallet import Wallet
    from xrpl.constants import CryptoAlgorithm
    algo = CryptoAlgorithm.ED25519 if algorithm.lower() == "ed25519" else CryptoAlgorithm.SECP256K1
    w = Wallet.create(algo)
    note_out("# WARNING: This output contains a SECRET SEED. Save it offline. Do not paste in chat logs.")
    json_out({"Address": w.classic_address, "Seed": w.seed,
              "PublicKey": w.public_key, "Algorithm": algorithm})

def tool_wallet_from_seed(seed: str):
    from xrpl.wallet import Wallet
    w = Wallet.from_seed(seed)
    json_out({"Address": w.classic_address, "PublicKey": w.public_key})

def tool_validate_address(addr: str):
    from xrpl.core.addresscodec import is_valid_classic_address, is_valid_xaddress
    json_out({"Address": addr, "ValidClassic": is_valid_classic_address(addr),
              "ValidX": is_valid_xaddress(addr)})

import sys

COMMANDS = {
    "wallet-generate": lambda: tool_wallet_generate(sys.argv[2] if len(sys.argv) >= 3 else "ed25519"),
    "wallet-from-seed": lambda: tool_wallet_from_seed(sys.argv[2]) if len(sys.argv) >= 3 else print("Usage: wallet-from-seed sEd..."),
    "validate-address": lambda: tool_validate_address(sys.argv[2]) if len(sys.argv) >= 3 else print("Usage: validate-address rADDR"),
}
