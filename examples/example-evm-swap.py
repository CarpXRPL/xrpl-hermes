#!/usr/bin/env python3
"""Retired: the former EVM swap example was not route/contract certified."""
import json


def main() -> int:
    print(json.dumps({
        "Error": "RetiredExample",
        "Message": (
            "example-evm-swap.py is intentionally non-runnable. A swap requires current router/asset "
            "contracts, allowance and slippage logic, simulation, gas estimation, an external wallet, "
            "and finalized receipt verification. No such route is certified in this release."
        ),
        "SafeNextStep": "Use evm-balance/evm-bridge for experimental network evidence and current official XRPL EVM documentation for research.",
    }, indent=2))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
