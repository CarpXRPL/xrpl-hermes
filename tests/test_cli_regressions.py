#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "xrpl_tools.py"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    )


def parse_json_stdout(result: subprocess.CompletedProcess[str]) -> dict:
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_evm_balance_missing_address_returns_usage_json():
    data = parse_json_stdout(run_cli("evm-balance"))

    assert data["Error"] == "UsageError"
    assert data["Command"] == "evm-balance"
    assert "0xADDRESS" in data["Usage"]


def test_trustlines_missing_address_returns_usage_json():
    data = parse_json_stdout(run_cli("trustlines"))

    assert data["Error"] == "UsageError"
    assert data["Command"] == "trustlines"
    assert "rADDRESS" in data["Usage"]


def test_build_payment_still_emits_transaction_json():
    result = run_cli(
        "build-payment",
        "--from",
        "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe",
        "--to",
        "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
        "--amount",
        "1000000",
    )
    data = parse_json_stdout(result)

    assert data["TransactionType"] == "Payment"
    assert data["Amount"] == "1000000"
