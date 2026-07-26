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


def test_xahau_transaction_type_map_matches_pinned_live_definitions():
    # Mainnet and Testnet server_definitions.json were identical for these IDs
    # when pinned on 2026-07-25. Drift must trigger an explicit source refresh.
    assert len(xahau.HOOKON_TT) == 77
    assert xahau.HOOKON_TT["Payment"] == 0
    assert xahau.HOOKON_TT["SetHook"] == 22
    assert xahau.HOOKON_TT["URITokenMint"] == 45
    assert xahau.HOOKON_TT["XChainCreateBridge"] == 57
    assert xahau.HOOKON_TT["MPTokenAuthorize"] == 66
    assert xahau.HOOKON_TT["PermissionedDomainDelete"] == 72
    assert xahau.HOOKON_TT["Invoke"] == 99
    assert xahau.HOOKON_TT["UNLReport"] == 104


def test_normalize_tt_names_aliases_and_ids():
    assert xahau._normalize_tt("Payment") == ("Payment", 0)
    assert xahau._normalize_tt("payment") == ("Payment", 0)
    assert xahau._normalize_tt("ttPAYMENT") == ("Payment", 0)
    assert xahau._normalize_tt("PAYCHAN_CREATE") == ("PaymentChannelCreate", 13)
    assert xahau._normalize_tt("ttHOOK_SET") == ("SetHook", 22)
    assert xahau._normalize_tt("TTPAYMENT") == ("Payment", 0)
    assert xahau._normalize_tt("99") == ("Invoke", 99)
    assert xahau._normalize_tt("60") == ("OracleSet", 60)
    assert xahau._normalize_tt("200") == ("tt200", 200)  # unnamed but in-range


def test_normalize_tt_rejects_unknown():
    with pytest.raises(ValueError):
        xahau._normalize_tt("NotARealType")
    with pytest.raises(ValueError):
        xahau._normalize_tt("300")  # out of 0-255 range
    with pytest.raises(ValueError):
        xahau._normalize_tt("١٢")  # Unicode numerals are not protocol IDs


def test_hookon_cli_value_is_hash256_without_0x(capsys):
    xahau.tool_hooks_bitmask("Payment")
    out = json.loads(capsys.readouterr().out)
    assert out["HookOn"] == "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFBFFFFE"
    assert len(out["HookOn"]) == 64
    bytes.fromhex(out["HookOn"])


def test_hookon_rejects_duplicates_and_invalid_ids(capsys):
    xahau.tool_hooks_bitmask("Payment", "0")
    out = json.loads(capsys.readouterr().out)
    assert out["Error"] == "InvalidTransactionType"
    with pytest.raises(ValueError):
        xahau.compute_hookon([-1])
    with pytest.raises(ValueError):
        xahau.compute_hookon([True])


def test_hooks_info_flattens_chain_and_reports_provenance(monkeypatch, capsys):
    def fake_rpc(endpoint, method, params):
        if method == "server_info":
            return {"status": "success", "info": {
                "network_id": 21338, "build_version": "review-test",
            }}
        assert endpoint == "https://xahau-test.net"
        assert params["type"] == "hook"
        return {
            "status": "success", "validated": True, "ledger_index": 123,
            "ledger_hash": "A" * 64,
            "account_objects": [{
                "LedgerEntryType": "Hook",
                "Hooks": [
                    {"Hook": {"HookHash": "B" * 64, "Flags": 0}},
                    {"Hook": {}},
                    {"Hook": {"HookHash": "C" * 64}},
                ],
            }],
        }

    monkeypatch.setattr(xahau, "_rpc", fake_rpc)
    xahau.tool_hooks_info("rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe", "testnet")
    out = json.loads(capsys.readouterr().out)
    assert out["Network"] == "testnet"
    assert out["NetworkID"] == 21338
    assert out["Validated"] is True
    assert out["HookCount"] == 2
    assert [hook["Slot"] for hook in out["Hooks"]] == [0, 2]


def test_hooks_info_never_turns_rpc_error_into_zero_hooks(monkeypatch, capsys):
    monkeypatch.setattr(
        xahau,
        "_live_network_metadata",
        lambda config: {"Network": "mainnet", "NetworkID": 21337},
    )
    monkeypatch.setattr(
        xahau,
        "_rpc",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("actNotFound: Account not found.")),
    )
    xahau.tool_hooks_info("rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe")
    out = json.loads(capsys.readouterr().out)
    assert out["Error"] == "RuntimeError"
    assert "actNotFound" in out["Message"]
    assert "HookCount" not in out


def test_hooks_info_rejects_unknown_network_and_x_address(capsys):
    xahau.tool_hooks_info("rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe", "devnet")
    out = json.loads(capsys.readouterr().out)
    assert out["Error"] == "ValueError"
    xahau.tool_hooks_info("XV5kHfQmzDQjbFNv4jX3FX9Y7ig5Qh97nmiT13NvP34UcNg", "testnet")
    out = json.loads(capsys.readouterr().out)
    assert out["Error"] == "ValueError"


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


def test_arweave_rejects_unicode_and_huge_sizes(capsys):
    arweave.tool_arweave_cost("١٢٣")
    assert json.loads(capsys.readouterr().out)["Error"] == "InvalidSize"
    arweave.tool_arweave_cost("1025GB")
    out = json.loads(capsys.readouterr().out)
    assert out["Error"] == "InvalidSize"
    assert "1 TiB" in out["Message"]


def test_arweave_rejects_wrong_network_identity(monkeypatch, capsys):
    class Response:
        def __init__(self, *, text="", payload=None):
            self.text = text
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    responses = iter([
        Response(text="1000"),
        Response(payload={"network": "unexpected"}),
    ])
    monkeypatch.setattr(arweave.httpx, "get", lambda *args, **kwargs: next(responses))
    arweave.tool_arweave_cost("1KB")
    out = json.loads(capsys.readouterr().out)
    assert out["Error"] == "ArweaveNetworkUnavailable"


def test_axelar_gmp_rejects_malformed_hash_without_network(monkeypatch, capsys):
    monkeypatch.setattr(axelar.httpx, "post", lambda *a, **k: (_ for _ in ()).throw(AssertionError("network called")))
    axelar.tool_bridge_tx("not-a-hash")
    assert json.loads(capsys.readouterr().out)["Error"] == "InvalidTransactionHash"


def test_axelar_gmp_rejects_malformed_records(monkeypatch, capsys):
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"data": ["junk"]}

    monkeypatch.setattr(axelar.httpx, "post", lambda *args, **kwargs: Response())
    axelar.tool_bridge_tx("A" * 64)
    out = json.loads(capsys.readouterr().out)
    assert out["Error"] == "AxelarGMPMalformed"
    assert out.get("Found") is not True


def test_axelar_registration_does_not_certify_route(monkeypatch, capsys):
    class Response:
        def raise_for_status(self):
            return None
        def json(self):
            return [{"id": "xrpl", "chain_name": "XRPL", "gateway": {"address": "rGateway"}}]
    monkeypatch.setattr(axelar.httpx, "get", lambda *a, **k: Response())
    axelar.tool_bridge_status("xrpl")
    out = json.loads(capsys.readouterr().out)
    assert out["RouteCertified"] is False
    assert out["Capability"] == "Axelarscan chain-registration lookup only"
    assert out["FetchedAt"]


def test_flare_tool_rejects_chain_mismatch(monkeypatch, capsys):
    monkeypatch.setattr(flare, "_chain_id", lambda: 1)
    monkeypatch.setattr(flare, "_resolve_ftso_v2", lambda: (_ for _ in ()).throw(AssertionError("resolved")))
    flare.tool_flare_ftso("XRP/USD")
    out = json.loads(capsys.readouterr().out)
    assert out["Error"] == "FtsoV2Unavailable"
    assert "does not match" in out["Message"]


def test_flare_tool_marks_old_feed_stale(monkeypatch, capsys):
    monkeypatch.setattr(flare, "_chain_id", lambda: 14)
    monkeypatch.setattr(flare, "_resolve_ftso_v2", lambda: "0x" + "1" * 40)
    monkeypatch.setattr(flare, "_read_feed", lambda _a, _p: {
        "value": 1, "decimals": 0, "price": 1,
        "timestamp": 1, "timestamp_iso": "1970-01-01T00:00:01+00:00",
    })
    flare.tool_flare_ftso("XRP/USD")
    out = json.loads(capsys.readouterr().out)
    assert out["ObservedChainID"] == 14
    assert out["Feeds"]["XRP/USD"]["stale"] is True
    assert out["FetchedAt"]
