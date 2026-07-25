#!/usr/bin/env python3
import io
import json
import sys
from contextlib import redirect_stdout

import pytest

from scripts.tools._shared import _dispatch_build, parse_amount_arg
from scripts.tools.accounts import tool_build_account_set
from scripts.tools.clawback import tool_build_clawback
from scripts.tools.nfts import tool_build_nft_create_offer
from scripts.tools.payments import tool_build_payment


SRC = "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe"
DST = "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh"
NFT_ID = "00080000B4F4A6D6B52B9AB638A6E5F69F7334E70000099B0000099B00000000"


def capture_json(fn, *args, **kwargs):
    buf = io.StringIO()
    with redirect_stdout(buf):
        fn(*args, **kwargs)
    return json.loads(buf.getvalue())


def test_build_payment_produces_payment_transaction_type():
    tx = capture_json(tool_build_payment, SRC, DST, "1000000")
    assert tx["TransactionType"] == "Payment"
    assert tx["Account"] == SRC
    assert tx["Destination"] == DST
    assert tx["Amount"] == "1000000"


def test_build_payment_applies_source_tag_and_memo():
    tx = capture_json(
        tool_build_payment, SRC, DST, "1000000",
        source_tag="20260615", memo="agent:settle-x402",
    )
    assert tx["TransactionType"] == "Payment"
    # SourceTag marks agent-initiated transactions and must be an integer UInt32.
    assert tx["SourceTag"] == 20260615
    assert isinstance(tx["SourceTag"], int)
    # Memo is an on-chain audit trail; MemoData is hex-encoded ASCII.
    memo_data = tx["Memos"][0]["Memo"]["MemoData"]
    assert bytes.fromhex(memo_data).decode("utf-8") == "agent:settle-x402"


def test_build_payment_carries_structured_agent_attribution_memo():
    # Official track-agent-behavior pattern: a hex-encoded JSON memo with
    # agent_id/session_id/action/task_id correlates an on-chain tx to the agent's
    # logs. Hermes hex-encodes the JSON string passed to --memo; it must decode
    # back to the same object so the audit trail round-trips.
    attribution = {"agent_id": "hermes-1", "session_id": "s-92",
                   "action": "settle", "task_id": "t-4417"}
    tx = capture_json(
        tool_build_payment, SRC, DST, "1000000",
        source_tag="4417", memo=json.dumps(attribution),
    )
    assert tx["SourceTag"] == 4417
    memo_data = tx["Memos"][0]["Memo"]["MemoData"]
    assert json.loads(bytes.fromhex(memo_data).decode("utf-8")) == attribution


def test_build_payment_default_has_no_tags_or_memos():
    tx = capture_json(tool_build_payment, SRC, DST, "1000000")
    assert "SourceTag" not in tx
    assert "Memos" not in tx
    assert "DestinationTag" not in tx


def test_build_payment_rejects_out_of_range_source_tag():
    with pytest.raises(ValueError, match="UInt32"):
        tool_build_payment(SRC, DST, "1000000", source_tag="999999999999")


def test_build_account_set_produces_accountset_with_set_flag():
    tx = capture_json(tool_build_account_set, SRC, set_flag=8)
    assert tx["TransactionType"] == "AccountSet"
    assert tx["Account"] == SRC
    assert tx["SetFlag"] == 8


def test_build_nft_create_offer_produces_nftoken_create_offer():
    tx = capture_json(tool_build_nft_create_offer, SRC, NFT_ID, "1000000")
    assert tx["TransactionType"] == "NFTokenCreateOffer"
    assert tx["Account"] == SRC
    assert tx["NFTokenID"] == NFT_ID
    assert tx["Amount"] == "1000000"


def test_parse_amount_arg_supports_xrp_and_token_amounts():
    assert parse_amount_arg("XRP:2500000") == "2500000"
    amount = parse_amount_arg(f"USD:{DST}:12.5")
    assert amount.to_dict() == {"currency": "USD", "issuer": DST, "value": "12.5"}


@pytest.mark.parametrize(
    "amount",
    ["not-a-number", "1.5", "-1000000", "XRP:1.5", "XRP", "XRP:1:extra"],
)
def test_parse_amount_arg_rejects_non_drops_xrp_amounts(amount):
    # XRP has no unit below a drop, so an XRP amount is an integer drops string.
    with pytest.raises(ValueError, match="drops"):
        parse_amount_arg(amount)


def test_parse_amount_arg_preserves_issued_decimal_value_exactly():
    amount = parse_amount_arg(f"USD:{DST}:0.000000000000000001")
    assert amount.value == "0.000000000000000001"


@pytest.mark.parametrize(
    "value",
    ["", "1e-18", "NaN", "Infinity", "1.000000000000000001", "12345678901234567890.5"],
)
def test_parse_amount_arg_rejects_unserializable_issued_values(value):
    with pytest.raises(ValueError, match="issued currency value"):
        parse_amount_arg(f"USD:{DST}:{value}")


@pytest.mark.parametrize(
    ("encoded", "currency"),
    [
        (f"usd:{DST}:1.25", "usd"),
        (f"1.25/usd:{DST}", "usd"),
    ],
)
def test_parse_amount_arg_preserves_case_sensitive_currency_identifier(encoded, currency):
    amount = parse_amount_arg(encoded)
    assert amount.currency == currency


def test_build_payment_returns_usage_guidance_for_unparseable_amount():
    payload = capture_json(tool_build_payment, SRC, DST, "not-a-number")
    assert payload["Error"] == "UsageError"
    assert payload["Command"] == "build-payment"
    assert "drops" in payload["Usage"].lower()


def test_build_payment_still_accepts_issued_currency_amounts():
    tx = capture_json(tool_build_payment, SRC, DST, "12.5", cur="usd", iss=DST)
    assert tx["Amount"] == {"currency": "usd", "issuer": DST, "value": "12.5"}


def test_build_clawback_validates_amount_greater_than_zero():
    buf = io.StringIO()
    with redirect_stdout(buf):
        tool_build_clawback(SRC, DST, "USD", "0")
    assert "amount must be positive" in buf.getvalue()


def test_dispatch_build_preserves_decimal_strings_exactly(monkeypatch):
    captured = {}

    def fake_builder(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(
        sys,
        "argv",
        ["xrpl_tools.py", "build-trustset", "--from", SRC, "--currency", "USD",
         "--issuer", DST, "--value", "1.000000000000000001"],
    )
    _dispatch_build(2, fake_builder)
    # The dispatcher has no currency context, so it must not decide that a dotted
    # argument is a number. Builders receive the operator's exact text.
    assert captured["value"] == "1.000000000000000001"
    assert isinstance(captured["value"], str)


def test_dispatch_build_keeps_uint_fields_as_ints(monkeypatch):
    captured = {}

    def fake_builder(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(
        sys,
        "argv",
        ["xrpl_tools.py", "build-nft-mint", "--from", SRC,
         "--taxon", "5", "--transfer-fee", "250"],
    )
    _dispatch_build(2, fake_builder)
    # The explicit list stays: these are genuine UInt32/UInt16 protocol fields.
    assert captured["taxon"] == 5
    assert captured["transfer_fee"] == 250


def test_dispatch_build_maps_from_to_frm(monkeypatch):
    captured = {}

    def fake_builder(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(
        sys,
        "argv",
        ["xrpl_tools.py", "build-payment", "--from", SRC, "--to", DST, "--amount", "1000000"],
    )
    _dispatch_build(3, fake_builder)
    assert captured["frm"] == SRC
    assert "from" not in captured
    assert captured["to"] == DST
    assert captured["amount"] == "1000000"
