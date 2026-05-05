#!/usr/bin/env python3
"""XRPL-Hermes Tool Suite — Thin CLI dispatcher.

All tool logic lives in scripts/tools/*.py modules.
This file just merges their COMMANDS dicts and dispatches.
"""
import sys, json
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.tools import (accounts, payments, trustlines, dex, amm, nfts, escrow,
                   checks, paychannel, mpts, clawback, oracles,
                   credentials, batch, ledger, wallet, evm, xahau,
                   flare, xaman)

COMMANDS = {}
for mod in (accounts, payments, trustlines, dex, amm, nfts, escrow,
            checks, paychannel, mpts, clawback, oracles,
            credentials, batch, ledger, wallet, evm, xahau,
            flare, xaman):
    COMMANDS.update(getattr(mod, 'COMMANDS', {}))

# path-find is dispatched via _shared._dispatch_path_find
def _path_find_wrapper():
    from scripts.tools._shared import _dispatch_path_find
    _dispatch_path_find()

COMMANDS["path-find"] = _path_find_wrapper

# Optional streaming tools (requires websockets / async support)
try:
    from scripts import xrpl_streams
    COMMANDS.update(getattr(xrpl_streams, 'COMMANDS', {}))
except ImportError as e:
    COMMANDS["subscribe"] = lambda: sys.stderr.write(
        "subscribe requires websockets. "
        "Install: pip install 'xrpl-py[websockets]'\n"
    )

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print("XRPL-Hermes Tool Suite")
        print("Commands: " + ", ".join(sorted(COMMANDS.keys())))
        return

    cmd = sys.argv[1].lower()
    fn = COMMANDS.get(cmd)
    if fn:
        fn()
    else:
        print(f"Unknown command: {cmd}")
        print("Available: " + ", ".join(sorted(COMMANDS.keys())))

if __name__ == "__main__":
    main()
