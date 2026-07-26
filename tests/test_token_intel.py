"""Offline tests for currency normalization, token-intel report shape, and amm-info parsing."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.tools._shared import normalize_currency_code, parse_asset_normalized
from scripts.tools import token_intel

ISSUER = "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe"
RLUSD_HEX = "524C555344000000000000000000000000000000"


# --- currency normalization ---

def test_normalize_three_char_passthrough():
    # 3-char codes occupy three raw bytes on-ledger and are case-sensitive, so
    # they pass through verbatim. This test previously asserted usd -> USD, which
    # is the retargeting defect itself: usd and USD are different assets.
    assert normalize_currency_code("USD") == "USD"
    assert normalize_currency_code("usd") == "usd"
    assert normalize_currency_code("XRP") == "XRP"


def test_normalize_symbol_to_160bit_hex():
    assert normalize_currency_code("RLUSD") == RLUSD_HEX
    assert normalize_currency_code("SOLO") == "534F4C4F" + "0" * 32


def test_normalize_hex_passthrough_uppercased():
    assert normalize_currency_code(RLUSD_HEX.lower()) == RLUSD_HEX


def test_normalize_rejects_bad_input():
    with pytest.raises(ValueError):
        normalize_currency_code("")
    with pytest.raises(ValueError):
        normalize_currency_code("AB")
    with pytest.raises(ValueError):
        normalize_currency_code("X" * 21)
    with pytest.raises(ValueError):
        normalize_currency_code("Z" * 40)  # 40 chars but not hex


# --- AMM asset parsing ---

def test_parse_asset_normalized():
    from xrpl.models.currencies import XRP, IssuedCurrency
    assert isinstance(parse_asset_normalized("XRP"), XRP)
    asset = parse_asset_normalized(f"RLUSD:{ISSUER}")
    assert isinstance(asset, IssuedCurrency)
    assert asset.currency == RLUSD_HEX
    assert asset.issuer == ISSUER
    assert parse_asset_normalized(f"USD:{ISSUER}").currency == "USD"
    with pytest.raises(ValueError):
        parse_asset_normalized("USD")  # issued currency without issuer


# --- token-intel report shape (offline, canned responses) ---

class FakeResponse:
    def __init__(self, result, successful=True):
        self.result = result
        self._successful = successful

    def is_successful(self):
        return self._successful


CANNED = {
    "AccountInfo": FakeResponse({"account_data": {
        "Balance": "100000000", "Flags": 0x00800000 | 0x00100000,
        "Domain": "6578616d706c652e636f6d", "OwnerCount": 2, "Sequence": 7,
        "TransferRate": 1005000000,
    }}),
    "AccountTx": FakeResponse({"transactions": [
        {"hash": "AB" * 32, "tx_json": {"TransactionType": "Payment"},
         "meta": {"TransactionResult": "tesSUCCESS"}, "ledger_index": 1},
    ]}),
    "AccountLines": FakeResponse({"lines": [
        {"currency": "FOO", "balance": "-25", "account": ISSUER},
        {"currency": "FOO", "balance": "0", "account": ISSUER},
        {"currency": "BAR", "balance": "-1", "account": ISSUER},
    ]}),
    "BookOffers": FakeResponse({"offers": []}),
    "AMMInfo": FakeResponse({"error": "actNotFound"}, successful=False),
}


def _fake_request(req):
    return CANNED[type(req).__name__]


REQUIRED_KEYS = {"input", "normalized_currency", "sources", "datapoints",
                 "risk_flags", "confidence", "missing_data", "plain_english_summary"}


def test_report_shape_with_all_datapoints(monkeypatch):
    monkeypatch.setattr(token_intel, "_request", _fake_request)
    report = token_intel.build_token_intel_report("FOO", ISSUER, tx_limit=5, trustline_limit=50)

    assert REQUIRED_KEYS <= set(report.keys())
    assert report["normalized_currency"] == "FOO"
    assert set(report["datapoints"]) == {
        "issuer_account", "issuer_recent_transactions", "trustline_sample",
        "dex_orderbook_vs_xrp", "amm_pool_vs_xrp"}
    assert report["confidence"] == "medium"
    assert report["recommendation"] == "not provided"
    assert "ledger snapshot only" in report["confidence_scope"]
    assert report["missing_data"] == []
    assert len(report["sources"]) == 5

    acct = report["datapoints"]["issuer_account"]
    assert acct["domain"] == "example.com"
    assert acct["transfer_fee_percent"] == 0.5
    assert "lsfDefaultRipple" in acct["flag_names"]

    trust = report["datapoints"]["trustline_sample"]
    assert trust["matching_currency_lines"] == 2  # BAR line filtered out
    assert trust["holders_with_balance_in_sample"] == 1
    assert trust["outstanding_in_sample"] == "25"

    assert report["datapoints"]["amm_pool_vs_xrp"] == {"amm_exists": False}
    # liquidity flag fires: empty book + no AMM
    assert any(f.startswith("no-xrp-liquidity") for f in report["risk_flags"])
    # transfer fee flag fires
    assert any(f.startswith("transfer-fee") for f in report["risk_flags"])
    assert report["plain_english_summary"]


def test_report_honest_when_everything_fails(monkeypatch):
    def boom(req):
        raise RuntimeError("network down")
    monkeypatch.setattr(token_intel, "_request", boom)
    report = token_intel.build_token_intel_report("FOO", ISSUER)

    assert report["datapoints"] == {}
    assert report["confidence"] == "none"
    assert {m["datapoint"] for m in report["missing_data"]} == {
        "issuer_account", "issuer_recent_transactions", "trustline_sample",
        "dex_orderbook_vs_xrp", "amm_pool_vs_xrp"}
    assert all("network down" in m["reason"] for m in report["missing_data"])


def test_report_rejects_xrp_and_bad_currency():
    xrp = token_intel.build_token_intel_report("XRP", ISSUER)
    assert xrp["datapoints"] == {}
    assert xrp["confidence"] == "none"

    bad = token_intel.build_token_intel_report("Z" * 40, ISSUER)
    assert bad["normalized_currency"] is None
    assert bad["missing_data"][0]["datapoint"] == "normalized_currency"


# --- command registration ---

def test_new_commands_registered():
    from scripts.xrpl_tools import COMMANDS
    assert "token-intel" in COMMANDS
    assert "amm-info" in COMMANDS
    assert len(COMMANDS) >= 69


def test_cli_usage_errors_offline():
    for cmd, hint in (("token-intel", "CURRENCY"), ("amm-info", "ASSET1")):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "xrpl_tools.py"), cmd],
            cwd=ROOT, text=True, capture_output=True, timeout=15)
        assert proc.returncode == 0, proc.stderr
        data = json.loads(proc.stdout)
        assert data["Error"] == "UsageError"
        assert hint in data["Usage"]
