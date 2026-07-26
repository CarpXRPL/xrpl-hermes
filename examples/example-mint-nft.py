#!/usr/bin/env python3
"""Retired direct-sign example; use the validated unsigned builder instead."""
import json


def main() -> int:
    print(json.dumps({
        "Status": "retired-direct-sign-example",
        "Transaction": 'NFTokenMint',
        "Reason": "The former example read key material, signed and submitted inside the process. That violates XRPL-Hermes signer separation.",
        "SafeReplacement": "Run `python3 -m scripts.xrpl_tools build-nft-mint ...` with reviewed parameters to produce unsigned JSON, hand it to a compatible user-owned signer, then verify the validated result with `tx-info`.",
        "SigningPerformed": False,
        "SubmissionPerformed": False
    }, indent=2))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
