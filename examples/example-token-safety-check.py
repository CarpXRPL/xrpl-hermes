#!/usr/bin/env python3
"""
☤ xrpl-hermes — Minimal token safety checker (read-only, mainnet).

Runs the same live token-intel report the `token-intel` command uses and
turns it into a pass/caution/fail verdict for scripts and CI. No wallet,
no seed, no transaction — it only reads public ledger data.

Usage:
    python3 example-token-safety-check.py RLUSD rMxCKbEDwqr76QuheSUMdEGf4B9xJ8m5De

Exit codes:
    0 = no risk flags found       (still do your own research)
    1 = risk flags found          (printed below the summary)
    2 = could not assess          (bad input or no live datapoints)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.tools.token_intel import build_token_intel_report


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__.strip())
        return 2

    currency, issuer = sys.argv[1], sys.argv[2]
    print(f"Checking {currency} issued by {issuer} (live mainnet data)...\n")
    report = build_token_intel_report(currency, issuer)

    print(report["plain_english_summary"])
    print(f"\nLive datapoints: {len(report['datapoints'])}/5  "
          f"(confidence: {report['confidence']})")

    for miss in report["missing_data"]:
        print(f"  missing: {miss['datapoint']} — {miss['reason']}")

    if report["confidence"] == "none":
        print("\nVerdict: CANNOT ASSESS — no live datapoints were available.")
        return 2

    if report["risk_flags"]:
        print(f"\nVerdict: {len(report['risk_flags'])} RISK FLAG(S)")
        for flag in report["risk_flags"]:
            print(f"  ⚠ {flag}")
        return 1

    print("\nVerdict: no risk flags found. This is not investment advice — "
          "a clean report means the issuer config showed no red flags, "
          "nothing more.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
