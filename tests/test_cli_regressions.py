#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

import pytest
from xrpl.core.binarycodec import encode_for_signing


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "xrpl_tools.py"

SRC = "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe"
DST = "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh"
ISSUER = "rMxCKbEDwqr76QuheSUMdEGf4B9xJ8m5De"
NFT_ID = "00080000B4F4A6D6B52B9AB638A6E5F69F7334E70000099B0000099B00000000"
CHANNEL_ID = "5DB01B7FFED6B67E6B0414DED11E051D2EE2B7619CE0EAA6286D67A3A4D5BDB3"

# Names a user should never see: an internal type error means the amount pipeline
# handed a wrong-typed value to xrpl-py instead of validating the input.
INTERNAL_ERROR_MARKERS = ("AttributeError", "TypeError", "XRPLModelException", "Traceback")


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


def assert_no_internal_error(result: subprocess.CompletedProcess[str]) -> None:
    combined = result.stdout + result.stderr
    for marker in INTERNAL_ERROR_MARKERS:
        assert marker not in combined, combined


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


def trustset_limit_value(value: str) -> str:
    data = parse_json_stdout(run_cli(
        "build-trustset", "--from", SRC, "--currency", "USD",
        "--issuer", ISSUER, "--value", value,
    ))
    return data["LimitAmount"]["value"]


def test_build_trustset_preserves_exact_decimal_value():
    # Issued-currency values travel as decimal strings. Generic float coercion
    # re-rendered this binary-codec-valid value as exponent notation (1e-18),
    # which changed the operator's exact text before the builder saw it.
    assert trustset_limit_value("0.000000000000000001") == "0.000000000000000001"


def test_build_trustset_never_emits_exponent_notation():
    # float() re-renders extreme decimals as "1e-18" / "1.23e+19". XRPL issued
    # amounts are decimal strings; exponent notation is not a valid value.
    for value in ("0.000000000000000001", "123456789012345.6"):
        emitted = trustset_limit_value(value)
        assert emitted == value
        assert "e" not in emitted.lower()


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


def test_build_payment_rejects_non_numeric_xrp_amount():
    data = parse_json_stdout(run_cli(
        "build-payment", "--from", SRC, "--to", DST, "--amount", "not-a-number"))

    assert data["Error"] == "UsageError"
    assert data["Command"] == "build-payment"
    assert "drops" in data["Usage"].lower()
    assert "not-a-number" in data["Usage"]
    # An unparseable amount must never reach the wire format.
    assert "TransactionType" not in data


def test_build_payment_rejects_decimal_xrp_amount():
    result = run_cli("build-payment", "--from", SRC, "--to", DST, "--amount", "1.5")
    data = parse_json_stdout(result)

    assert data["Error"] == "UsageError"
    assert "drops" in data["Usage"].lower()
    assert "TransactionType" not in data
    assert_no_internal_error(result)


def test_build_payment_rejects_negative_xrp_amount():
    data = parse_json_stdout(run_cli(
        "build-payment", "--from", SRC, "--to", DST, "--amount", "-1000000"))

    assert data["Error"] == "UsageError"
    assert "drops" in data["Usage"].lower()


@pytest.mark.parametrize("amount", ["1000000", "XRP:2500000"])
def test_build_payment_emits_integer_drops_string(amount):
    data = parse_json_stdout(run_cli(
        "build-payment", "--from", SRC, "--to", DST, "--amount", amount))

    assert data["TransactionType"] == "Payment"
    assert isinstance(data["Amount"], str)
    assert data["Amount"].isdigit()
    assert data["Amount"] == amount.split(":")[-1]


def test_build_payment_preserves_issued_currency_code_case():
    # 3-char codes are case-sensitive on-ledger: usd and USD are different assets.
    data = parse_json_stdout(run_cli(
        "build-payment", "--from", SRC, "--to", DST,
        "--amount", "10", "--cur", "usd", "--iss", ISSUER))

    assert data["Amount"] == {"currency": "usd", "issuer": ISSUER, "value": "10"}


def test_build_payment_preserves_issued_decimal_value_exactly():
    data = parse_json_stdout(run_cli(
        "build-payment", "--from", SRC, "--to", DST,
        "--amount", f"USD:{ISSUER}:0.000000000000000001"))

    assert data["Amount"]["currency"] == "USD"
    assert data["Amount"]["issuer"] == ISSUER
    assert data["Amount"]["value"] == "0.000000000000000001"
    # "Signer-ready" is a binary-codec property, not merely a JSON shape.
    assert encode_for_signing(data)


@pytest.mark.parametrize(
    "value",
    ["", "1e-18", "NaN", "Infinity", "1.000000000000000001", "12345678901234567890.5"],
)
def test_build_payment_rejects_unserializable_issued_values(value):
    data = parse_json_stdout(run_cli(
        "build-payment", "--from", SRC, "--to", DST,
        "--amount", f"USD:{ISSUER}:{value}"))

    assert data["Error"] == "UsageError"
    assert "issued currency value" in data["Usage"].lower()
    assert "TransactionType" not in data


def test_build_payment_rejects_malformed_xrp_amount_with_extra_component():
    data = parse_json_stdout(run_cli(
        "build-payment", "--from", SRC, "--to", DST, "--amount", "XRP:1:extra"))

    assert data["Error"] == "UsageError"
    assert "drops" in data["Usage"].lower()
    assert "TransactionType" not in data


def test_build_payment_colon_form_preserves_issued_currency_code_case():
    data = parse_json_stdout(run_cli(
        "build-payment", "--from", SRC, "--to", DST,
        "--amount", f"usd:{ISSUER}:1.25"))

    assert data["Amount"] == {"currency": "usd", "issuer": ISSUER, "value": "1.25"}


# The six value-carrying builder paths, each invoked with a decimal XRP amount.
DECIMAL_VALUE_BUILDERS = {
    "build-payment": ("--from", SRC, "--to", DST, "--amount", "1.5"),
    "build-check-create": ("--from", SRC, "--to", DST, "--amount", "1.5"),
    "build-escrow-create": ("--from", SRC, "--to", DST, "--amount", "1.5"),
    "build-nft-create-offer": ("--from", SRC, "--nftoken-id", NFT_ID, "--amount", "1.5"),
    "build-paychannel-fund": ("--from", SRC, "--channel-id", CHANNEL_ID, "--amount", "1.5"),
    "build-amm-deposit": ("--from", SRC, "--asset1", "XRP",
                          "--asset2", f"USD:{ISSUER}", "--amount1", "1.5"),
}

# All six should reject decimal XRP amounts. Three builders still own inline amount
# parsing outside this mission's file allowlist; strict xfails make that debt visible
# and turn into XPASS failures as soon as Mission 3 fixes the implementation.
DECIMAL_XRP_REJECTION_CASES = (
    "build-payment",
    "build-nft-create-offer",
    "build-amm-deposit",
    pytest.param(
        "build-check-create",
        marks=pytest.mark.xfail(strict=True, reason="Mission 3: route CheckCreate through drops validation"),
    ),
    pytest.param(
        "build-escrow-create",
        marks=pytest.mark.xfail(strict=True, reason="Mission 3: route EscrowCreate through drops validation"),
    ),
    pytest.param(
        "build-paychannel-fund",
        marks=pytest.mark.xfail(strict=True, reason="Mission 3: route PaymentChannelFund through drops validation"),
    ),
)


@pytest.mark.parametrize("command", sorted(DECIMAL_VALUE_BUILDERS))
def test_value_builders_never_leak_internal_errors_on_decimal_input(command):
    # Transitional floor while Mission 3 replaces the remaining invalid-payload
    # paths with explicit drops guidance.
    assert_no_internal_error(run_cli(command, *DECIMAL_VALUE_BUILDERS[command]))


@pytest.mark.parametrize("command", DECIMAL_XRP_REJECTION_CASES)
def test_value_builders_reject_decimal_xrp_with_drops_guidance(command):
    result = run_cli(command, *DECIMAL_VALUE_BUILDERS[command])
    data = parse_json_stdout(result)

    # build-payment answers with a UsageError envelope; builders that call the
    # shared parser directly surface its ValueError. Both must suppress a payload
    # and name the required unit.
    assert "TransactionType" not in data
    assert "drops" in json.dumps(data).lower()
