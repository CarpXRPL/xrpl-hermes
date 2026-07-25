#!/usr/bin/env python3
import json
import os
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

# All six reject decimal XRP amounts. check-create, escrow-create and
# paychannel-fund were strict xfails while their inline amount parsing sat outside
# Mission 2's file allowlist; Mission 3 owns those files, so the xfails are gone.
DECIMAL_XRP_REJECTION_CASES = tuple(sorted(DECIMAL_VALUE_BUILDERS))


@pytest.mark.parametrize("command", sorted(DECIMAL_VALUE_BUILDERS))
def test_value_builders_never_leak_internal_errors_on_decimal_input(command):
    assert_no_internal_error(run_cli(command, *DECIMAL_VALUE_BUILDERS[command]))


@pytest.mark.parametrize("command", DECIMAL_XRP_REJECTION_CASES)
def test_value_builders_reject_decimal_xrp_with_drops_guidance(command):
    result = run_cli(command, *DECIMAL_VALUE_BUILDERS[command])
    data = parse_json_stdout(result)

    # Every value builder answers with a controlled envelope that suppresses the
    # payload and names the required unit.
    assert "TransactionType" not in data
    assert "drops" in json.dumps(data).lower()


# --- TX-4: currency identity across every builder path this mission touches ---

RLUSD_HEX = "524C555344000000000000000000000000000000"
LONG_SYMBOL = "RLUSD"   # 4-20 char ASCII symbol -> 160-bit hex on-ledger
SHORT_CODE = "usd"      # 3-char code -> case-sensitive, must survive verbatim

# (label, argv template containing the CUR placeholder, path to the emitted code)
CURRENCY_IDENTITY_PATHS = (
    ("build-payment --cur/--iss",
     ("build-payment", "--from", SRC, "--to", DST, "--amount", "10",
      "--cur", "{CUR}", "--iss", ISSUER),
     ("Amount", "currency")),
    ("build-payment colon amount",
     ("build-payment", "--from", SRC, "--to", DST, "--amount", "{CUR}:" + ISSUER + ":10"),
     ("Amount", "currency")),
    ("build-trustset",
     ("build-trustset", "--from", SRC, "--currency", "{CUR}",
      "--issuer", ISSUER, "--value", "1000"),
     ("LimitAmount", "currency")),
    ("build-clawback",
     ("build-clawback", "--from", ISSUER, "--destination", DST,
      "--currency", "{CUR}", "--amount", "100"),
     ("Amount", "currency")),
    ("build-check-create",
     ("build-check-create", "--from", SRC, "--to", DST,
      "--amount", "{CUR}:" + ISSUER + ":100"),
     ("SendMax", "currency")),
    ("build-escrow-create",
     ("build-escrow-create", "--from", SRC, "--to", DST,
      "--amount", "{CUR}:" + ISSUER + ":100",
      "--condition", "A0258020E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855810100",
      "--cancel-after", "900000000"),
     ("Amount", "currency")),
    ("build-nft-create-offer",
     ("build-nft-create-offer", "--from", SRC, "--nftoken-id", NFT_ID,
      "--amount", "{CUR}:" + ISSUER + ":100"),
     ("Amount", "currency")),
    ("build-amm-deposit",
     ("build-amm-deposit", "--from", SRC, "--asset1", "XRP",
      "--asset2", "{CUR}:" + ISSUER, "--amount1", "1000000",
      "--amount2", "{CUR}:" + ISSUER + ":1"),
     ("Asset2", "currency")),
    ("build-cross-currency-payment",
     ("build-cross-currency-payment", "--from", SRC, "--to", DST,
      "--deliver", "{CUR}:" + ISSUER + ":10", "--send-max", "XRP:2000000"),
     ("Amount", "currency")),
)


def emitted_currency(argv_template, path, code):
    argv = [a.replace("{CUR}", code) for a in argv_template]
    data = parse_json_stdout(run_cli(*argv))
    node = data
    for key in path:
        assert key in node, data
        node = node[key]
    return node


@pytest.mark.parametrize(
    ("label", "argv", "path"), CURRENCY_IDENTITY_PATHS,
    ids=[c[0] for c in CURRENCY_IDENTITY_PATHS],
)
def test_long_symbol_normalizes_to_160bit_hex_on_every_touched_path(label, argv, path):
    # A 4-20 char ASCII symbol has no 3-byte slot on-ledger: it must travel as the
    # zero-padded 160-bit hex code, or the payload names an asset that cannot exist.
    assert emitted_currency(argv, path, LONG_SYMBOL) == RLUSD_HEX


@pytest.mark.parametrize(
    ("label", "argv", "path"), CURRENCY_IDENTITY_PATHS,
    ids=[c[0] for c in CURRENCY_IDENTITY_PATHS],
)
def test_three_char_code_case_is_preserved_on_every_touched_path(label, argv, path):
    # 3-char codes are case-sensitive on-ledger: usd and USD are different assets.
    # Uppercasing here silently retargets the transaction at another issuer's token.
    assert emitted_currency(argv, path, SHORT_CODE) == SHORT_CODE


# --- TX-2: AMM auction bid protocol shape ---

def test_build_amm_bid_emits_nested_auth_account_objects():
    data = parse_json_stdout(run_cli(
        "build-amm-bid", "--from", SRC, "--asset1", "XRP",
        "--asset2", f"USD:{ISSUER}", "--auth-accounts", DST))

    # AuthAccounts is an array of inner objects. A raw lowercase dict bypasses
    # model validation and is not the wire shape rippled parses.
    assert data["AuthAccounts"] == [{"AuthAccount": {"Account": DST}}]


def test_build_amm_bid_rejects_malformed_bid_min_instead_of_dropping_it():
    result = run_cli("build-amm-bid", "--from", SRC, "--asset1", "XRP",
                     "--asset2", f"USD:{ISSUER}", "--bid-min", "100")
    data = parse_json_stdout(result)

    # A silently discarded bid ceiling turns a bounded auction bid into an
    # unbounded one, so it must fail loudly rather than build without the limit.
    assert "TransactionType" not in data
    assert "BidMin" not in json.dumps(data)
    assert_no_internal_error(result)


# --- TX-3: NFT URI encoding contract ---

def test_build_nft_mint_hex_encodes_hex_lookalike_text_uri():
    data = parse_json_stdout(run_cli(
        "build-nft-mint", "--from", SRC, "--taxon", "0", "--uri", "cafe"))

    # "cafe" is ordinary text that happens to be even-length hex. NFT URIs are
    # immutable for the token's life, so guessing here is permanent.
    assert data["URI"] == "63616665"


def test_build_nft_mint_hex_encodes_ordinary_uri_text():
    uri = "https://example.com/1.json"
    data = parse_json_stdout(run_cli(
        "build-nft-mint", "--from", SRC, "--taxon", "0", "--uri", uri))

    assert bytes.fromhex(data["URI"]).decode("utf-8") == uri


def test_build_nft_mint_accepts_explicit_pre_encoded_uri():
    data = parse_json_stdout(run_cli(
        "build-nft-mint", "--from", SRC, "--taxon", "0", "--uri-hex", "63616665"))

    assert data["URI"] == "63616665"


def test_build_nft_mint_rejects_ambiguous_double_uri():
    data = parse_json_stdout(run_cli(
        "build-nft-mint", "--from", SRC, "--taxon", "0",
        "--uri", "cafe", "--uri-hex", "63616665"))

    assert data["Error"] == "UsageError"
    assert "TransactionType" not in data


@pytest.mark.parametrize("bad_hex", ["zz", "abc", ""])
def test_build_nft_mint_rejects_invalid_pre_encoded_uri(bad_hex):
    data = parse_json_stdout(run_cli(
        "build-nft-mint", "--from", SRC, "--taxon", "0", "--uri-hex", bad_hex))

    assert data["Error"] == "UsageError"
    assert "TransactionType" not in data


# --- TX-5: token amounts where the ledger supports them ---

@pytest.mark.parametrize(
    ("command", "argv", "field"),
    [
        ("build-check-create",
         ("--from", SRC, "--to", DST, "--amount", f"USD:{ISSUER}:100"), "SendMax"),
        ("build-escrow-create",
         ("--from", SRC, "--to", DST, "--amount", f"USD:{ISSUER}:100",
          "--condition", "A0258020E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855810100",
          "--cancel-after", "900000000"), "Amount"),
    ],
)
def test_token_amounts_are_accepted_by_check_and_escrow(command, argv, field):
    result = run_cli(command, *argv)
    data = parse_json_stdout(result)

    assert data[field] == {"currency": "USD", "issuer": ISSUER, "value": "100"}
    # "Signer-ready" is a binary-codec property, not merely a JSON shape.
    assert encode_for_signing(data)
    assert_no_internal_error(result)


# --- TX-6: AccountDelete guardrails ---

def run_cli_verbose(*args: str) -> subprocess.CompletedProcess[str]:
    """Run without XRPL_TOOLS_QUIET so stderr guidance is observable."""
    env = {k: v for k, v in os.environ.items() if k != "XRPL_TOOLS_QUIET"}
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT, text=True, capture_output=True, timeout=10, check=False, env=env,
    )


def test_build_account_delete_emits_destructive_precondition_guidance():
    result = run_cli_verbose("build-account-delete", "--from", SRC, "--to", DST)
    data = json.loads(result.stdout)

    assert data["TransactionType"] == "AccountDelete"
    guidance = result.stderr
    assert "DESTRUCTIVE" in guidance.upper()
    assert "irreversible" in guidance.lower()
    # The builder is offline: it must say it cannot prove the preconditions.
    assert "cannot" in guidance.lower()
    for precondition in ("Sequence", "256", "owner reserve", "destination"):
        assert precondition.lower() in guidance.lower(), guidance
    assert_no_internal_error(result)


def test_build_account_delete_includes_destination_tag():
    data = parse_json_stdout(run_cli(
        "build-account-delete", "--from", SRC, "--to", DST, "--dest-tag", "12345"))

    assert data["DestinationTag"] == 12345
    assert isinstance(data["DestinationTag"], int)


@pytest.mark.parametrize(
    "argv",
    [
        ("--from", "not-an-address", "--to", DST),
        ("--from", SRC, "--to", "rNOTVALID"),
        ("--from", SRC, "--to", DST, "--dest-tag", "4294967296"),
        ("--from", SRC, "--to", DST, "--dest-tag", "abc"),
    ],
)
def test_build_account_delete_validates_fields(argv):
    result = run_cli("build-account-delete", *argv)
    data = parse_json_stdout(result)

    assert "TransactionType" not in data
    assert_no_internal_error(result)


# --- TX-10: no silently dropped CLI arguments ---

@pytest.mark.parametrize(
    "argv",
    [
        ("build-payment", "--from", SRC, "--to", DST, "--amount", "1000000", "--memo"),
        ("build-trustset", "--from", SRC, "--currency", "USD", "--issuer", ISSUER, "--value"),
        ("build-account-set", "--from", SRC, "--transfer-rate"),
    ],
)
def test_missing_value_after_flag_is_a_usage_error(argv):
    result = run_cli(*argv)
    data = parse_json_stdout(result)

    assert data["Error"] == "UsageError"
    assert argv[-1] in data["Usage"]
    # Silently dropping the pair emitted a payload that omitted what was asked for.
    assert "TransactionType" not in data
    assert_no_internal_error(result)


def test_positional_argument_without_flag_is_a_usage_error():
    data = parse_json_stdout(run_cli(
        "build-payment", "--from", SRC, "--to", DST, "1000000"))

    assert data["Error"] == "UsageError"
    assert "TransactionType" not in data


# --- TX-11: TransferRate clear/reset shortcut ---

def test_build_account_set_accepts_transfer_rate_zero():
    data = parse_json_stdout(run_cli("build-account-set", "--from", SRC, "--transfer-rate", "0"))

    # 0 is the documented shortcut for 1000000000 (no fee): the only way an issuer
    # can clear an existing transfer rate.
    assert data["TransactionType"] == "AccountSet"
    assert data["TransferRate"] == 0


@pytest.mark.parametrize("rate", ["1", "999999999", "2000000001", "-1"])
def test_build_account_set_still_rejects_invalid_nonzero_transfer_rate(rate):
    data = parse_json_stdout(run_cli("build-account-set", "--from", SRC, "--transfer-rate", rate))

    assert data["Error"] == "InvalidTransferRate"
    assert "TransactionType" not in data


# --- TX-19: NaN / infinity / negative / malformed amount forms ---

NON_FINITE = ["nan", "NaN", "inf", "-inf", "Infinity", "-Infinity"]


@pytest.mark.parametrize("value", NON_FINITE + ["-1000000", "1e400"])
def test_native_amount_rejects_non_finite_and_negative_values(value):
    result = run_cli("build-payment", "--from", SRC, "--to", DST, "--amount", value)
    data = parse_json_stdout(result)

    assert "TransactionType" not in data
    assert_no_internal_error(result)


@pytest.mark.parametrize("value", NON_FINITE + ["-100", "1e400"])
def test_clawback_rejects_non_finite_and_negative_values(value):
    result = run_cli("build-clawback", "--from", ISSUER, "--destination", DST,
                     "--currency", "USD", "--amount", value)
    data = parse_json_stdout(result)

    assert "TransactionType" not in data
    assert_no_internal_error(result)


@pytest.mark.parametrize(
    "amount",
    ["USD::100", f":{ISSUER}:100", f"USD:{ISSUER}:", f"USD:{ISSUER}:100:200",
     "USD:not-an-address:100", f"USD:{ISSUER}"],
)
def test_malformed_colon_amount_forms_are_rejected(amount):
    result = run_cli("build-payment", "--from", SRC, "--to", DST, "--amount", amount)
    data = parse_json_stdout(result)

    assert data["Error"] == "UsageError"
    assert "TransactionType" not in data
    assert_no_internal_error(result)


def test_build_payment_currency_without_issuer_is_rejected():
    # --cur used to be dropped when --iss was absent, emitting the value as drops:
    # a token payment silently became an XRP payment.
    data = parse_json_stdout(run_cli(
        "build-payment", "--from", SRC, "--to", DST, "--amount", "10", "--cur", "usd"))

    assert data["Error"] == "UsageError"
    assert "TransactionType" not in data
