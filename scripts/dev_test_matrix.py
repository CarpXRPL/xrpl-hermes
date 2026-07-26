#!/usr/bin/env python3
"""Generate a safe dev-test matrix for XRPL-Hermes CLI commands.

This script validates live reads, unsigned builders, and registry wiring. Commands
that create a real external side effect remain unexecuted.
"""
from __future__ import annotations
import json
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.matrix_validation import builder_wire_error, elapsed_seconds, top_level_cli_error

TOOL = [sys.executable, "scripts/xrpl_tools.py"]
R = "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe"
GENESIS = "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh"
BITSTAMP = "rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B"
ZERO_HASH = "0" * 64
MPT_ISSUANCE_ID = "0" * 48
NFT_ID = "000813889418964705A72A064CEBEBFD8E7A04802B1A2F5F0F74796700000CEE"
VALIDATED_TX = "05EEB773E4F2A9B2917EA641246B842A04B65752DDDC95806CCDCF671110952E"
CHANNEL = "5DB01BDF4AB2D996B7B8E3A7B7D91E0A4C8B6A6B5F2D2B9E0A1C2D3E4F506070"
TXBLOB = "1200002280000000240000000161400000000000000168400000000000000A73210300000000000000000000000000000000000000000000000000000000000000008114" + "0"*40 + "8314" + "0"*40

TESTS = {
    "account": ["account", R],
    "account-tx": ["account-tx", R, "1"],
    "account_objects": ["account_objects", R],
    "amendment": ["amendment", "Batch"],
    "amendment-status": ["amendment-status", "MPTokensV1"],
    "amendments": ["amendments", "AMMClawback"],
    "amm-info": ["amm-info", "XRP", f"USD:{BITSTAMP}"],
    "arweave-cost": ["arweave-cost", "1MB"],
    "balance": ["balance", R],
    "book-offers": ["book-offers", "XRP", f"USD:{BITSTAMP}"],
    "bridge-status": ["bridge-status"],
    "bridge-tx": ["bridge-tx", ZERO_HASH],
    "build-account-delete": ["build-account-delete", "--from", R, "--to", GENESIS],
    "build-account-set": ["build-account-set", "--from", R, "--set-flag", "8"],
    "build-amm-bid": ["build-amm-bid", "--from", R, "--asset1", "XRP", "--asset2", f"USD:{BITSTAMP}"],
    "build-amm-create": ["build-amm-create", "--from", R, "--amount1", "XRP:1000000", "--amount2", f"USD:{BITSTAMP}:1", "--fee", "500"],
    "build-amm-deposit": ["build-amm-deposit", "--from", R, "--asset1", "XRP", "--asset2", f"USD:{BITSTAMP}", "--amount1", "1000000", "--amount2", f"USD:{BITSTAMP}:1"],
    "build-amm-vote": ["build-amm-vote", "--from", R, "--asset1", "XRP", "--asset2", f"USD:{BITSTAMP}", "--trading-fee", "500"],
    "build-amm-withdraw": ["build-amm-withdraw", "--from", R, "--asset1", "XRP", "--asset2", f"USD:{BITSTAMP}", "--amount1", "XRP:500000", "--amount2", f"USD:{BITSTAMP}:0.5"],
    "build-check-cancel": ["build-check-cancel", "--from", R, "--check-id", ZERO_HASH],
    "build-check-cash": ["build-check-cash", "--from", R, "--check-id", ZERO_HASH, "--amount", "1"],
    "build-check-create": ["build-check-create", "--from", R, "--to", GENESIS, "--amount", "1"],
    "build-clawback": ["build-clawback", "--from", R, "--destination", GENESIS, "--currency", "USD", "--amount", "1"],
    "build-credential-accept": ["build-credential-accept", "--from", R, "--issuer", GENESIS, "--credential-type", "4B5943"],
    "build-credential-create": ["build-credential-create", "--from", R, "--subject", GENESIS, "--credential-type", "4B5943"],
    "build-credential-delete": ["build-credential-delete", "--from", R, "--subject", GENESIS, "--credential-type", "4B5943"],
    "build-cross-currency-payment": ["build-cross-currency-payment", "--from", R, "--to", GENESIS, "--deliver", f"USD:{BITSTAMP}:1", "--send-max", "XRP:1000000"],
    "build-deposit-preauth": ["build-deposit-preauth", "--from", R, "--authorize", GENESIS],
    "build-escrow-cancel": ["build-escrow-cancel", "--from", R, "--owner", GENESIS, "--offer-sequence", "1"],
    "build-escrow-create": ["build-escrow-create", "--from", R, "--to", GENESIS, "--amount", "1", "--finish-after", "900000000"],
    "build-escrow-finish": ["build-escrow-finish", "--from", R, "--owner", GENESIS, "--offer-sequence", "1"],
    "build-mpt-authorize": ["build-mpt-authorize", "--from", R, "--mpt-issuance-id", MPT_ISSUANCE_ID],
    "build-mpt-issuance-create": ["build-mpt-issuance-create", "--from", R, "--asset-scale", "6", "--maximum-amount", "1000"],
    "build-nft-accept-offer": ["build-nft-accept-offer", "--from", R, "--sell-offer", ZERO_HASH],
    "build-nft-burn": ["build-nft-burn", "--from", R, "--nftoken-id", NFT_ID],
    "build-nft-cancel-offer": ["build-nft-cancel-offer", "--from", R, "--offers", ZERO_HASH],
    "build-nft-create-offer": ["build-nft-create-offer", "--from", R, "--nftoken-id", NFT_ID, "--amount", "1"],
    "build-nft-mint": ["build-nft-mint", "--from", R, "--taxon", "1", "--uri", "ipfs://example"],
    "build-offer": ["build-offer", "--from", R, "--sell", "XRP:1000000", "--buy", f"USD:{BITSTAMP}:1"],
    "build-paychannel-claim": ["build-paychannel-claim", "--from", R, "--channel-id", CHANNEL],
    "build-paychannel-create": ["build-paychannel-create", "--from", R, "--to", GENESIS, "--amount", "1", "--settle-delay", "60", "--public-key", "ED" + "0"*64],
    "build-paychannel-fund": ["build-paychannel-fund", "--from", R, "--channel-id", CHANNEL, "--amount", "1"],
    "build-payment": ["build-payment", "--from", R, "--to", GENESIS, "--amount", "1"],
    "build-set-oracle": ["build-set-oracle", "--from", R, "--oracle-doc-id", "1", "--provider", "5852504C", "--asset-class", "63757272656e6379", "--last-update-time", "2000000000", "--price-data", "XRP/USD:1150000:6"],
    "build-set-regular-key": ["build-set-regular-key", "--from", R, "--regular-key", GENESIS],
    "build-signer-list-set": ["build-signer-list-set", "--from", R, "--quorum", "1", "--signers", f"{GENESIS}:1"],
    "build-ticket-create": ["build-ticket-create", "--from", R, "--count", "1"],
    "build-trustset": ["build-trustset", "--from", R, "--currency", "USD", "--issuer", BITSTAMP, "--value", "1"],
    "decode": ["decode", TXBLOB],
    "evm-balance": ["evm-balance", "0x0000000000000000000000000000000000000000"],
    "evm-bridge": ["evm-bridge"],
    "evm-contract": ["evm-contract", "--from", "0x0000000000000000000000000000000000000000", "--bytecode", "0x00"],
    "flare-price": ["flare-price", "XRP", "FLR"],
    "flare-ftso": ["flare-ftso", "XRP/USD"],
    "hooks-bitmask": ["hooks-bitmask", "Payment"],
    # Public mainnet account with one installed Hook; verified in the Xahau
    # certification pass. A missing XRPL genesis account must not masquerade as
    # a successful zero-Hook read.
    "hooks-info": ["hooks-info", "rsownxgTwCbZ2TvTtimi95uGrwW4LGXUMq", "mainnet"],
    "ledger": ["ledger"],
    "ledger-entry": ["ledger-entry", "--index", ZERO_HASH],
    "nft-info": ["nft-info", NFT_ID],
    "nft-offers": ["nft-offers", NFT_ID, "sell"],
    "path-find": ["path-find", R, GENESIS, "1", f"USD:{BITSTAMP}"],
    "server-info": ["server-info"],
    "subscribe": ["subscribe", "streams=ledger"],
    "token-intel": ["token-intel", "USD", BITSTAMP, "3", "20"],
    "trustlines": ["trustlines", R],
    "tx-info": ["tx-info", VALIDATED_TX],
    "validate-address": ["validate-address", R],
}

# Registered commands for which a valid invocation creates an external side effect.
# Never execute these in an automated matrix.
SKIPPED_SAFETY = {
    "xaman-payload": "Not executed: when Xaman credentials are configured, invoking this command "
                     "creates a real external wallet signing request. MCP denial is covered by "
                     "tests/test_mcp_server.py.",
}


def run(cmd, timeout=12):
    start = time.monotonic()
    try:
        p = subprocess.run(TOOL + cmd, cwd=ROOT, text=True, capture_output=True, timeout=timeout)
        stdout = p.stdout.strip()
        out = (p.stdout + p.stderr).strip()
        out = re.sub(r'\bs[a-zA-Z0-9]{25,}\b', 's████REDACTED_TEST_SEED████', out)
        return (p.returncode, elapsed_seconds(start, time.monotonic()),
                out[:500].replace("\n", " "), stdout)
    except subprocess.TimeoutExpired as e:
        stdout = e.stdout.decode(errors="ignore") if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr = e.stderr.decode(errors="ignore") if isinstance(e.stderr, bytes) else (e.stderr or "")
        out = (stdout + stderr).strip()
        return "timeout", timeout, out[:500].replace("\n", " "), stdout

# Import command registry after writing TESTS so we catch drift.
import scripts.xrpl_tools as registry
commands = sorted(registry.COMMANDS)

missing_safety_skip = sorted(set(SKIPPED_SAFETY) - set(commands))
if missing_safety_skip:
    raise SystemExit(f"safety-skipped command(s) are no longer registered: {missing_safety_skip}")
rows = []
for name in commands:
    if name in SKIPPED_SAFETY:
        rows.append({"command": name, "argv": "(not executed)", "exit": "-", "seconds": 0,
                     "status": "SKIPPED-SAFETY", "sample": SKIPPED_SAFETY[name]})
        continue
    cmd = TESTS.get(name, [name])
    # bridge-tx's upstream client has a 20-second network timeout; the matrix
    # process timeout must be longer or it can kill a legitimate controlled
    # response before the command reports it.
    code, seconds, sample, stdout = run(cmd, timeout=30 if name == "bridge-tx" else 12)
    long_ok = name == "subscribe" and code == "timeout"
    wire_error = builder_wire_error(name, stdout) if code == 0 else None
    builder_error = name.startswith("build-") and ('"Error"' in sample or wire_error)
    cli_error = top_level_cli_error(stdout) if code == 0 else None
    if wire_error:
        sample = f"{sample} [WIRE ERROR: {wire_error}]"
    if cli_error:
        sample = f"{sample} [CLI ERROR: {cli_error}]"
    ok = (code == 0 or long_ok) and "Traceback" not in sample and not builder_error and not cli_error
    report_argv = " ".join(shlex.quote(x) for x in cmd)
    report_sample = sample

    rows.append({"command": name, "argv": report_argv, "exit": code, "seconds": seconds, "status": "PASS" if ok else "FAIL", "sample": report_sample})

passed = sum(1 for r in rows if r["status"] == "PASS")
skipped_safety = sum(1 for r in rows if r["status"] == "SKIPPED-SAFETY")
failed = sum(1 for r in rows if r["status"] == "FAIL")
md = [
    "# XRPL-Hermes dev-test matrix",
    "",
    f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}",
    f"Commands registered: {len(commands)}",
    f"Passed: {passed}",
    f"Failed: {failed}",
    f"Skipped for safety: {skipped_safety}",
    "",
    "Commands that create an external request are not executed and are marked SKIPPED-SAFETY. `subscribe` passes when it starts and reaches the controlled timeout because it is a long-running stream.",
    "",
    "| Command | Status | Exit | Seconds | Test argv | Output sample |",
    "|---|---|---:|---:|---|---|",
]
for r in rows:
    sample = r["sample"].replace("|", "\\|")
    md.append(f"| `{r['command']}` | {r['status']} | `{r['exit']}` | {r['seconds']} | `{r['argv']}` | {sample} |")

report_path = os.environ.get("XRPL_HERMES_MATRIX_REPORT")
if report_path:
    Path(report_path).write_text("\n".join(md) + "\n")
print(json.dumps({"commands": len(commands), "passed": passed, "failed": failed,
                  "skipped_external": sorted(SKIPPED_SAFETY),
                  "report": report_path}, indent=2))
if failed:
    print("FAILED COMMANDS:")
    for r in rows:
        if r["status"] == "FAIL":
            print(r["command"], r["exit"], r["sample"])
    raise SystemExit(1)
