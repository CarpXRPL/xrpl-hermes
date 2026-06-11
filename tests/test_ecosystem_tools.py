"""Offline regression tests for the v1.5.2 ecosystem tools: Xahau HookOn math,
Arweave size parsing, Flare FTSOv2 feed encoding/decoding, and Axelar
response shaping."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.tools import arweave, axelar, flare, xahau


# --- Xahau HookOn bitmask ---

ALL_ONES = (1 << 256) - 1


def test_hookon_empty_fires_on_nothing():
    # Active-low baseline: all ones, except bit 22 (ttHOOK_SET, active-high) cleared.
    assert xahau.compute_hookon([]) == ALL_ONES & ~(1 << 22)


def test_hookon_payment_only_matches_documented_value():
    # Canonical example from the Xahau HookOn docs: fire on Payment only.
    expected = int("0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFBFFFFE", 16)
    assert xahau.compute_hookon([0]) == expected


def test_hookon_sethook_is_active_high():
    mask = xahau.compute_hookon([22])
    assert mask & (1 << 22)          # bit 22 set = fires on SetHook
    assert mask & 1                  # Payment bit still set = does not fire


def test_hookon_combined_types():
    mask = xahau.compute_hookon([0, 99])  # Payment + Invoke
    assert not mask & (1 << 0)
    assert not mask & (1 << 99)
    assert not mask & (1 << 22)      # active-high bit stays cleared
    assert mask & (1 << 1)           # EscrowCreate untouched


def test_normalize_tt_names_aliases_and_ids():
    assert xahau._normalize_tt("Payment") == ("Payment", 0)
    assert xahau._normalize_tt("payment") == ("Payment", 0)
    assert xahau._normalize_tt("ttPAYMENT") == ("Payment", 0)
    assert xahau._normalize_tt("PAYCHAN_CREATE") == ("PaymentChannelCreate", 13)
    assert xahau._normalize_tt("ttHOOK_SET") == ("SetHook", 22)
    assert xahau._normalize_tt("99") == ("Invoke", 99)
    assert xahau._normalize_tt("60") == ("tt60", 60)  # unnamed but valid tt ID


def test_normalize_tt_rejects_unknown():
    with pytest.raises(ValueError):
        xahau._normalize_tt("NotARealType")
    with pytest.raises(ValueError):
        xahau._normalize_tt("300")  # out of 0-255 range


# --- Arweave size parsing ---

def test_parse_size_suffixes():
    assert arweave._parse_size("512") == 512
    assert arweave._parse_size("100B") == 100
    assert arweave._parse_size("2KB") == 2048
    assert arweave._parse_size("1MB") == 1048576
    assert arweave._parse_size("1.5KB") == 1536
    assert arweave._parse_size("1 GB") == 1024 ** 3
    assert arweave._parse_size("1mb") == 1048576


def test_parse_size_rejects_garbage():
    with pytest.raises(Exception):
        arweave._parse_size("abc")


def test_arweave_cost_invalid_size_is_honest(capsys):
    arweave.tool_arweave_cost("notasize")
    out = json.loads(capsys.readouterr().out)
    assert out["Error"] == "InvalidSize"
    arweave.tool_arweave_cost("0")
    out = json.loads(capsys.readouterr().out)
    assert out["Error"] == "InvalidSize"


# --- Flare FTSOv2 feed encoding/decoding ---

def test_feed_id_layout():
    fid = flare._feed_id("XRP/USD")
    assert len(fid) == 42                      # 21 bytes hex
    assert fid.startswith("01")                # category 0x01 = crypto
    assert bytes.fromhex(fid[2:]).rstrip(b"\0") == b"XRP/USD"


def test_feed_id_rejects_long_names():
    with pytest.raises(ValueError):
        flare._feed_id("X" * 21 + "/USD")


def test_read_feed_decodes_value_decimals_timestamp(monkeypatch):
    value, decimals, timestamp = 1112928, 6, 1781182151
    canned = "0x" + f"{value:064x}" + f"{decimals:064x}" + f"{timestamp:064x}"
    monkeypatch.setattr(flare, "_eth_call", lambda to, data: canned)
    feed = flare._read_feed("0x" + "0" * 40, "XRP/USD")
    assert feed["value"] == value
    assert feed["decimals"] == decimals
    assert feed["price"] == pytest.approx(1.112928)
    assert feed["timestamp"] == timestamp
    assert feed["timestamp_iso"].endswith("+00:00")


def test_read_feed_sign_extends_negative_decimals(monkeypatch):
    # int8 decimals = -2 arrives sign-extended to 256 bits; price = value * 100.
    canned = "0x" + f"{1500:064x}" + f"{(1 << 256) - 2:064x}" + f"{1781182151:064x}"
    monkeypatch.setattr(flare, "_eth_call", lambda to, data: canned)
    feed = flare._read_feed("0x" + "0" * 40, "BTC/USD")
    assert feed["decimals"] == -2
    assert feed["price"] == pytest.approx(150000.0)


def test_read_feed_rejects_short_result(monkeypatch):
    monkeypatch.setattr(flare, "_eth_call", lambda to, data: "0x")
    with pytest.raises(RuntimeError):
        flare._read_feed("0x" + "0" * 40, "XRP/USD")


# --- Axelar response shaping ---

def test_chain_summary_shape():
    summary = axelar._chain_summary({
        "id": "xrpl", "chain_name": "xrpl", "chain_type": "vm", "chain_id": None,
        "gateway": {"address": "rfmS3zqrQrka8wVyhXifEeyTwe8AMz2Yhw"},
        "native_token": {"symbol": "XRP", "decimals": 6},
        "explorer": {"url": "https://livenet.xrpl.org"},
    })
    assert summary["id"] == "xrpl"
    assert summary["gateway"] == "rfmS3zqrQrka8wVyhXifEeyTwe8AMz2Yhw"
    assert summary["explorer"] == "https://livenet.xrpl.org"
    assert summary["deprecated"] is False
    assert summary["evm_chain_id"] is None


# --- ecosystem commands registered and usage-safe ---

def test_ecosystem_commands_registered():
    from scripts.xrpl_tools import COMMANDS
    for cmd in ("bridge-status", "bridge-tx", "arweave-cost", "flare-ftso",
                "flare-price", "hooks-bitmask", "hooks-info"):
        assert cmd in COMMANDS


def test_cli_usage_errors_offline():
    for cmd, hint in (("bridge-tx", "TXHASH"), ("arweave-cost", "SIZE"),
                      ("hooks-bitmask", "TXTYPE")):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "xrpl_tools.py"), cmd],
            cwd=ROOT, text=True, capture_output=True, timeout=15)
        assert proc.returncode == 0, proc.stderr
        data = json.loads(proc.stdout)
        assert data["Error"] == "UsageError"
        assert hint in data["Usage"]
