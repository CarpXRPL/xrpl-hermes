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


def test_build_clawback_validates_amount_greater_than_zero():
    buf = io.StringIO()
    with redirect_stdout(buf):
        tool_build_clawback(SRC, DST, "USD", "0")
    assert "amount must be positive" in buf.getvalue()


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
