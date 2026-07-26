#!/usr/bin/env python3
import io
import json
import sys
from contextlib import redirect_stdout
from decimal import Decimal

import pytest

from scripts.tools import _shared
from scripts.tools._shared import (
    _dispatch_build, make_amount, normalize_currency_code, parse_amount_arg,
    parse_asset_normalized, validate_xrpl_address,
)
from scripts.tools.accounts import tool_build_account_delete, tool_build_account_set
from scripts.tools.amm import (
    tool_build_amm_bid, tool_build_amm_create,
    tool_build_amm_deposit, tool_build_amm_withdraw,
)
from scripts.tools.checks import tool_build_check_create
from scripts.tools.clawback import tool_build_clawback
from scripts.tools.escrow import tool_build_escrow_create, tool_build_escrow_finish
from scripts.tools.nfts import tool_build_nft_create_offer, tool_build_nft_mint
from scripts.tools.mpts import tool_build_mpt_authorize, tool_build_mpt_issuance_create
from scripts.tools.paychannel import (
    tool_build_paychannel_claim, tool_build_paychannel_create, tool_build_paychannel_fund,
)
from scripts.tools.payments import tool_build_payment
from scripts.tools.trustlines import tool_build_trustset


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


# --- TX-4: currency identity ---

RLUSD_HEX = "524C555344000000000000000000000000000000"
LP_TOKEN_CODE = "03" + "A" * 38   # LP tokens carry a 40-char hex currency


def test_normalize_currency_code_preserves_three_char_case():
    # 3-char codes are case-sensitive on-ledger. Uppercasing them retargets the
    # transaction at a different asset than the operator named.
    assert normalize_currency_code("usd") == "usd"
    assert normalize_currency_code("USD") == "USD"
    assert normalize_currency_code("XRP") == "XRP"


def test_normalize_currency_code_hexifies_long_symbol():
    assert normalize_currency_code("RLUSD") == RLUSD_HEX


def test_normalize_currency_code_uppercases_only_the_hex_form():
    assert normalize_currency_code(RLUSD_HEX.lower()) == RLUSD_HEX


def test_parse_amount_arg_normalizes_long_symbol_to_hex():
    amount = parse_amount_arg(f"RLUSD:{DST}:100")
    assert amount.currency == RLUSD_HEX


def test_parse_amount_arg_slash_form_normalizes_long_symbol():
    amount = parse_amount_arg(f"100/RLUSD:{DST}")
    assert amount.currency == RLUSD_HEX


@pytest.mark.parametrize(
    "amount",
    ["USD::100", ":rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh:100",
     "USD:not-an-address:100", "100/USD:not-an-address"],
)
def test_parse_amount_arg_rejects_malformed_issuer(amount):
    # An empty or malformed issuer is accepted by the model layer, so it has to be
    # caught here or the payload names an account that cannot exist.
    with pytest.raises(ValueError):
        parse_amount_arg(amount)


@pytest.mark.parametrize("value", ["nan", "NaN", "inf", "-inf", "Infinity", "1e400"])
def test_parse_amount_arg_rejects_non_finite_amounts(value):
    with pytest.raises(ValueError):
        parse_amount_arg(value)
    with pytest.raises(ValueError):
        parse_amount_arg(f"USD:{DST}:{value}")


# --- TX-2: AMM auction bid ---

def test_build_amm_bid_nests_auth_account_objects():
    tx = capture_json(tool_build_amm_bid, SRC, "XRP", f"USD:{DST}", auth_accounts=DST)
    assert tx["AuthAccounts"] == [{"AuthAccount": {"Account": DST}}]


def test_build_amm_bid_accepts_positive_lp_token_shaped_bounds():
    # Offline validation can prove only the 03-prefixed LP-token wire shape.
    # Operators must copy the exact currency+issuer from amm-info for this pair.
    tx = capture_json(
        tool_build_amm_bid, SRC, "XRP", f"USD:{DST}",
        bid_min=f"{LP_TOKEN_CODE}:{DST}:10", bid_max=f"{LP_TOKEN_CODE}:{DST}:20")
    assert tx["BidMin"]["value"] == "10"
    assert tx["BidMax"]["value"] == "20"


@pytest.mark.parametrize("bad", ["100", "XRP:100", f"USD:{DST}"])
def test_build_amm_bid_rejects_malformed_bid_bounds(bad):
    payload = capture_json(tool_build_amm_bid, SRC, "XRP", f"USD:{DST}", bid_min=bad)
    assert payload["Error"] == "UsageError"
    assert "TransactionType" not in payload


def test_build_amm_bid_rejects_invalid_auth_account():
    payload = capture_json(tool_build_amm_bid, SRC, "XRP", f"USD:{DST}",
                           auth_accounts="not-an-address")
    assert payload["Error"] == "UsageError"
    assert "TransactionType" not in payload


# --- TX-3: NFT URI contract ---

def test_build_nft_mint_hex_encodes_text_that_looks_like_hex():
    tx = capture_json(tool_build_nft_mint, SRC, uri="cafe")
    assert tx["URI"] == "63616665"


def test_build_nft_mint_accepts_explicit_pre_encoded_hex():
    tx = capture_json(tool_build_nft_mint, SRC, uri_hex="63616665")
    assert tx["URI"] == "63616665"


def test_build_nft_mint_rejects_both_uri_forms_at_once():
    payload = capture_json(tool_build_nft_mint, SRC, uri="cafe", uri_hex="63616665")
    assert payload["Error"] == "UsageError"
    assert "TransactionType" not in payload


# --- TX-5: token amounts in checks and escrow ---

def test_build_check_create_accepts_issued_currency_send_max():
    tx = capture_json(tool_build_check_create, SRC, DST, f"USD:{DST}:100")
    assert tx["SendMax"] == {"currency": "USD", "issuer": DST, "value": "100"}


def test_build_escrow_create_accepts_issued_currency_amount():
    tx = capture_json(
        tool_build_escrow_create, SRC, DST, f"USD:{DST}:100",
        condition="A0258020E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855810100",
        cancel_after="900000000")
    assert tx["Amount"] == {"currency": "USD", "issuer": DST, "value": "100"}


@pytest.mark.parametrize("value", ["1.5", "-1000000", "nan", "inf", "-inf", "1e6"])
@pytest.mark.parametrize(
    ("fn", "args"),
    [
        (tool_build_check_create, (SRC, DST)),
        (tool_build_escrow_create, (SRC, DST)),
        (tool_build_paychannel_fund, (SRC, "AB" * 32)),
        (tool_build_paychannel_create, (SRC, DST)),
    ],
)
def test_native_builders_reject_invalid_xrp_amounts_with_drops_guidance(fn, args, value):
    # XRP has no unit below a drop and no sign: decimals, negatives, exponents
    # and non-finite text are all outside the wire format.
    payload = capture_json(fn, *args, value, *(("86400", "ABCD") if fn is tool_build_paychannel_create else ()))
    assert payload["Error"] == "UsageError"
    assert "drops" in payload["Usage"].lower()
    assert "TransactionType" not in payload


@pytest.mark.parametrize("field", ["amount", "balance"])
@pytest.mark.parametrize("value", ["-100", "1.5", "nan"])
def test_paychannel_claim_rejects_invalid_drops(field, value):
    payload = capture_json(tool_build_paychannel_claim, SRC, "AB" * 32, **{field: value})
    assert payload["Error"] == "UsageError"
    assert "drops" in payload["Usage"].lower()
    assert "TransactionType" not in payload


@pytest.mark.parametrize("rate", ["abc", "", "1.5"])
def test_build_account_set_rejects_non_integer_transfer_rate(rate):
    # int() raised straight into the dispatcher, naming a Python builtin the
    # operator never supplied instead of the field that was wrong.
    payload = capture_json(tool_build_account_set, SRC, transfer_rate=rate)
    assert payload["Error"] == "InvalidTransferRate"
    assert "TransactionType" not in payload


def test_paychannel_fund_rejects_issued_amount():
    # Payment channels are XRP-only: an issued amount there is not a payload the
    # ledger can accept.
    payload = capture_json(tool_build_paychannel_fund, SRC, "AB" * 32, f"USD:{DST}:100")
    assert payload["Error"] == "UsageError"
    assert "TransactionType" not in payload


# --- TX-6: AccountDelete ---

def test_build_account_delete_includes_destination_tag():
    tx = capture_json(tool_build_account_delete, SRC, DST, dest_tag="12345")
    assert tx["TransactionType"] == "AccountDelete"
    assert tx["DestinationTag"] == 12345


def test_build_account_delete_rejects_invalid_addresses():
    for frm, to in ((("not-an-address"), DST), (SRC, "rNOTVALID")):
        payload = capture_json(tool_build_account_delete, frm, to)
        assert payload["Error"] == "UsageError"
        assert "TransactionType" not in payload


def test_build_account_delete_warns_before_emitting_payload(capsys):
    tool_build_account_delete(SRC, DST)
    warning = capsys.readouterr().err
    assert "DESTRUCTIVE" in warning.upper()
    assert "cannot" in warning.lower()


# --- TX-11: TransferRate clear shortcut ---

def test_build_account_set_accepts_transfer_rate_zero():
    tx = capture_json(tool_build_account_set, SRC, transfer_rate=0)
    assert tx["TransferRate"] == 0


@pytest.mark.parametrize("rate", [1, 999_999_999, 2_000_000_001, -1])
def test_build_account_set_rejects_invalid_nonzero_transfer_rate(rate):
    payload = capture_json(tool_build_account_set, SRC, transfer_rate=rate)
    assert payload["Error"] == "InvalidTransferRate"


# --- TX-19: clawback amount validation without float() ---

@pytest.mark.parametrize("value", ["nan", "NaN", "inf", "-inf", "1e400", "-100"])
def test_build_clawback_rejects_non_finite_and_negative_amounts(value):
    payload = capture_json(tool_build_clawback, SRC, DST, "USD", value)
    assert payload["Error"] == "UsageError"
    assert "TransactionType" not in payload


def test_build_clawback_normalizes_long_symbol_and_preserves_short_code():
    long_symbol = capture_json(tool_build_clawback, SRC, DST, "RLUSD", "100")
    assert long_symbol["Amount"]["currency"] == RLUSD_HEX
    short_code = capture_json(tool_build_clawback, SRC, DST, "usd", "100")
    assert short_code["Amount"]["currency"] == "usd"


# --- TX-4: trustline filter must match the on-ledger identifier ---

def test_trustlines_filter_matches_normalized_currency(monkeypatch):
    from scripts.tools import trustlines

    class FakeResponse:
        result = {"lines": [{"currency": RLUSD_HEX, "balance": "10"},
                            {"currency": "USD", "balance": "5"}]}

    monkeypatch.setattr(trustlines, "_request", lambda req: FakeResponse())
    report = capture_json(trustlines.tool_trustlines, SRC, "RLUSD")
    # A symbol filter that is not hexified can never match the on-ledger code.
    assert report["TrustLineCount"] == 1
    assert report["TrustLines"][0]["currency"] == RLUSD_HEX


# --- TX-10: no silently dropped CLI arguments ---

def test_dispatch_build_rejects_unpaired_trailing_argument(monkeypatch, capsys):
    def fake_builder(**kwargs):
        raise AssertionError("builder must not run with a dropped argument")

    monkeypatch.setattr(
        sys, "argv",
        ["xrpl_tools.py", "build-payment", "--from", SRC, "--to", DST,
         "--amount", "1000000", "--memo"],
    )
    _dispatch_build(3, fake_builder)
    payload = json.loads(capsys.readouterr().out)
    assert payload["Error"] == "UsageError"
    assert "--memo" in payload["Usage"]


def test_dispatch_build_rejects_token_that_is_not_a_flag(monkeypatch, capsys):
    def fake_builder(**kwargs):
        raise AssertionError("builder must not run with an unparsed argument")

    monkeypatch.setattr(
        sys, "argv",
        ["xrpl_tools.py", "build-payment", "--from", SRC, "1000000", "--to", DST],
    )
    _dispatch_build(3, fake_builder)
    payload = json.loads(capsys.readouterr().out)
    assert payload["Error"] == "UsageError"


# --- Independent protocol-semantics regressions ---

def test_parse_amount_arg_rejects_negative_issued_amount():
    with pytest.raises(ValueError, match="nonnegative"):
        parse_amount_arg(f"USD:{DST}:-1")


def test_parse_asset_normalized_rejects_invalid_issuer():
    with pytest.raises(ValueError, match="issuer"):
        parse_asset_normalized("USD:not-an-address")


def test_transaction_address_validator_rejects_xaddress():
    # Raw transaction AccountID fields take classic addresses. Accepting an
    # X-address here would silently discard its embedded destination tag.
    from xrpl.core.addresscodec import classic_address_to_xaddress
    xaddress = classic_address_to_xaddress(DST, 123, False)
    with pytest.raises(ValueError, match="classic"):
        validate_xrpl_address(xaddress)


def test_paychannel_create_rejects_issued_amount():
    payload = capture_json(
        tool_build_paychannel_create, SRC, DST, f"USD:{DST}:100", "86400", "ABCD")
    assert payload["Error"] == "UsageError"
    assert "drops" in payload["Usage"].lower()
    assert "TransactionType" not in payload


def test_paychannel_create_rejects_zero_amount():
    payload = capture_json(tool_build_paychannel_create, SRC, DST, "0", "86400", "ABCD")
    assert payload["Error"] == "UsageError"
    assert "positive" in payload["Usage"].lower()
    assert "TransactionType" not in payload


def test_token_escrow_requires_cancel_after():
    payload = capture_json(tool_build_escrow_create, SRC, DST, f"USD:{DST}:100")
    assert payload["Error"] == "UsageError"
    assert "cancel-after" in payload["Usage"].lower()
    assert "TransactionType" not in payload


# --- Independent reviewer blockers: protocol semantics beyond binary encoding ---

CONDITION = "A0258020E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855810100"
EMPTY_FULFILLMENT = "A0028000"
ABC_CONDITION = "A0258020BA7816BF8F01CFEA414140DE5DAE2223B00361A396177A9CB410FF61F20015AD810103"
ABC_FULFILLMENT = "A0058003616263"
MAX_XRP_DROPS = "100000000000000000"


def test_xrp_drops_enforces_wire_maximum():
    assert parse_amount_arg(MAX_XRP_DROPS) == MAX_XRP_DROPS
    with pytest.raises(ValueError, match="maximum"):
        parse_amount_arg("100000000000000001")


def test_standard_currency_code_must_use_permitted_ascii():
    with pytest.raises(ValueError, match="ASCII"):
        normalize_currency_code("€€€")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"finish_after": "800000000", "cancel_after": "900000000"},
        {"condition": CONDITION, "cancel_after": "900000000"},
        {"finish_after": "800000000", "condition": CONDITION,
         "cancel_after": "900000000"},
    ],
)
def test_token_escrow_accepts_official_expiring_combinations(kwargs):
    tx = capture_json(
        tool_build_escrow_create, SRC, DST, f"USD:{DST}:100", **kwargs)
    assert tx["TransactionType"] == "EscrowCreate"


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"finish_after": "800000000"},
        {"condition": CONDITION},
        {"cancel_after": "900000000"},
    ],
)
def test_token_escrow_rejects_non_expiring_or_incomplete_combinations(kwargs):
    payload = capture_json(
        tool_build_escrow_create, SRC, DST, f"USD:{DST}:100", **kwargs)
    assert payload["Error"] == "UsageError"
    assert "TransactionType" not in payload


@pytest.mark.parametrize("condition", ["AA", "A000", CONDITION + "00"])
def test_escrow_create_rejects_malformed_crypto_conditions(condition):
    payload = capture_json(
        tool_build_escrow_create, SRC, DST, "1000",
        condition=condition, cancel_after="900000000")
    assert payload["Error"] == "UsageError"
    assert "TransactionType" not in payload


@pytest.mark.parametrize(
    ("condition", "fulfillment"),
    [(CONDITION, EMPTY_FULFILLMENT), (ABC_CONDITION, ABC_FULFILLMENT)],
)
def test_escrow_finish_accepts_matching_preimage_condition(condition, fulfillment):
    tx = capture_json(tool_build_escrow_finish, SRC, DST, "1", condition, fulfillment)
    assert tx["TransactionType"] == "EscrowFinish"


@pytest.mark.parametrize(
    ("condition", "fulfillment", "sequence"),
    [
        ("AA", EMPTY_FULFILLMENT, "1"),
        (CONDITION, "AA", "1"),
        (CONDITION, ABC_FULFILLMENT, "1"),
        (CONDITION, None, "1"),
        (None, EMPTY_FULFILLMENT, "1"),
        (None, None, "-1"),
    ],
)
def test_escrow_finish_rejects_malformed_or_mismatched_conditions(
        condition, fulfillment, sequence):
    payload = capture_json(
        tool_build_escrow_finish, SRC, DST, sequence, condition, fulfillment)
    assert payload["Error"] == "UsageError"
    assert "TransactionType" not in payload


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"cancel_after": "900000000"},
        {"condition": CONDITION},
    ],
)
def test_xrp_escrow_rejects_invalid_field_combinations(kwargs):
    payload = capture_json(tool_build_escrow_create, SRC, DST, "1000", **kwargs)
    assert payload["Error"] == "UsageError"
    assert "TransactionType" not in payload


@pytest.mark.parametrize(
    "kwargs",
    [
        {"finish_after": "800000000"},
        {"finish_after": "800000000", "cancel_after": "900000000"},
        {"finish_after": "800000000", "condition": CONDITION},
        {"condition": CONDITION, "cancel_after": "900000000"},
    ],
)
def test_xrp_escrow_accepts_official_field_combinations(kwargs):
    tx = capture_json(tool_build_escrow_create, SRC, DST, "1000", **kwargs)
    assert tx["TransactionType"] == "EscrowCreate"


@pytest.mark.parametrize("bad", [f"USD:{DST}:1", f"03{'A' * 38}:{DST}:0"])
def test_amm_bid_rejects_non_lp_or_zero_bounds(bad):
    payload = capture_json(tool_build_amm_bid, SRC, "XRP", f"USD:{DST}", bid_min=bad)
    assert payload["Error"] == "UsageError"
    assert "TransactionType" not in payload


@pytest.mark.parametrize(
    ("bid_min", "bid_max"),
    [
        (f"{LP_TOKEN_CODE}:{DST}:20", f"{LP_TOKEN_CODE}:{DST}:10"),
        (f"{LP_TOKEN_CODE}:{DST}:10",
         f"{LP_TOKEN_CODE}:rMxCKbEDwqr76QuheSUMdEGf4B9xJ8m5De:20"),
    ],
)
def test_amm_bid_rejects_reversed_or_mismatched_bounds(bid_min, bid_max):
    payload = capture_json(
        tool_build_amm_bid, SRC, "XRP", f"USD:{DST}",
        bid_min=bid_min, bid_max=bid_max)
    assert payload["Error"] == "UsageError"
    assert "TransactionType" not in payload


@pytest.mark.parametrize(
    "auth_accounts",
    [
        SRC,
        "",
        ",,,",
        f"{DST},{DST}",
        f"{DST},rMxCKbEDwqr76QuheSUMdEGf4B9xJ8m5De,rLs1MzkFWCxTbuAHgjeTZK4fcCDDnf2KRv,rDsbeomae4FXwgQTJp9Rs64Qg9vDiTCdBv,rG1QQv2nh2gr7RCZ1P8YYcBUKCCN633jCn",
    ],
)
def test_amm_bid_rejects_invalid_auth_account_sets(auth_accounts):
    payload = capture_json(
        tool_build_amm_bid, SRC, "XRP", f"USD:{DST}", auth_accounts=auth_accounts)
    assert payload["Error"] == "UsageError"
    assert "TransactionType" not in payload


@pytest.mark.parametrize(
    ("fn", "args", "kwargs"),
    [
        (tool_build_amm_create, (SRC, "0", f"USD:{DST}:1"), {}),
        (tool_build_amm_create, (SRC, "1", f"USD:{DST}:0"), {}),
        (tool_build_amm_deposit, (SRC, "XRP", f"USD:{DST}"),
         {"amount1": "0", "amount2": f"USD:{DST}:1"}),
        (tool_build_amm_withdraw, (SRC, "XRP", f"USD:{DST}"),
         {"amount1": "0", "amount2": f"USD:{DST}:1"}),
    ],
)
def test_amm_builders_reject_zero_transaction_amounts(fn, args, kwargs):
    payload = capture_json(fn, *args, **kwargs)
    assert payload["Error"] == "UsageError"
    assert "positive" in payload["Usage"].lower()
    assert "TransactionType" not in payload


@pytest.mark.parametrize("fn", [tool_build_amm_deposit, tool_build_amm_withdraw])
def test_amm_liquidity_amounts_must_match_their_assets(fn):
    payload = capture_json(
        fn, SRC, "XRP", f"USD:{DST}", amount1=f"EUR:{DST}:1",
        mode="single-asset")
    assert payload["Error"] == "UsageError"
    assert "TransactionType" not in payload


@pytest.mark.parametrize("fn", [tool_build_amm_deposit, tool_build_amm_withdraw])
def test_amm_two_asset_mode_accepts_reversed_amount_order(fn):
    tx = capture_json(
        fn, SRC, "XRP", f"USD:{DST}",
        amount1=f"USD:{DST}:1", amount2="1", mode="two-asset")
    assert tx["Amount"]["currency"] == "USD"
    assert tx["Amount2"] == "1"


@pytest.mark.parametrize("fn", [tool_build_amm_deposit, tool_build_amm_withdraw])
def test_amm_single_asset_mode_accepts_either_pool_asset(fn):
    tx = capture_json(
        fn, SRC, "XRP", f"USD:{DST}",
        amount1=f"USD:{DST}:1", mode="single-asset")
    assert tx["Amount"]["currency"] == "USD"


@pytest.mark.parametrize(
    ("fn", "kwargs", "expected_fields"),
    [
        (tool_build_amm_deposit,
         {"amount1": "1", "amount2": f"USD:{DST}:1", "mode": "two-asset"},
         {"Amount", "Amount2"}),
        (tool_build_amm_deposit,
         {"amount1": "1", "mode": "single-asset"}, {"Amount"}),
        (tool_build_amm_deposit,
         {"lp_token_out": f"{LP_TOKEN_CODE}:{DST}:1", "mode": "lp-token"},
         {"LPTokenOut"}),
        (tool_build_amm_withdraw,
         {"amount1": "1", "amount2": f"USD:{DST}:1", "mode": "two-asset"},
         {"Amount", "Amount2"}),
        (tool_build_amm_withdraw,
         {"amount1": "1", "mode": "single-asset"}, {"Amount"}),
        (tool_build_amm_withdraw,
         {"lp_token_in": f"{LP_TOKEN_CODE}:{DST}:1", "mode": "lp-token"},
         {"LPTokenIn"}),
        (tool_build_amm_withdraw,
         {"mode": "withdraw-all"}, set()),
    ],
)
def test_amm_liquidity_modes_emit_exact_field_matrix(fn, kwargs, expected_fields):
    tx = capture_json(fn, SRC, "XRP", f"USD:{DST}", **kwargs)
    optional = {"Amount", "Amount2", "LPTokenOut", "LPTokenIn"}
    assert set(tx) & optional == expected_fields


@pytest.mark.parametrize(
    ("fn", "kwargs"),
    [
        (tool_build_amm_deposit, {"amount1": "1"}),
        (tool_build_amm_deposit, {"amount2": f"USD:{DST}:1"}),
        (tool_build_amm_deposit,
         {"amount1": "1", "amount2": f"USD:{DST}:1", "mode": "single-asset"}),
        (tool_build_amm_deposit, {"mode": "lp-token"}),
        (tool_build_amm_deposit,
         {"amount1": "1", "amount2": f"USD:{DST}:1", "mode": "unknown"}),
        (tool_build_amm_withdraw, {"amount1": "1"}),
        (tool_build_amm_withdraw,
         {"amount1": "1", "amount2": f"USD:{DST}:1", "mode": "single-asset"}),
        (tool_build_amm_withdraw, {"mode": "lp-token"}),
        (tool_build_amm_withdraw, {"amount1": "1", "mode": "withdraw-all"}),
        (tool_build_amm_withdraw,
         {"amount1": "1", "amount2": f"USD:{DST}:1", "mode": "unknown"}),
    ],
)
def test_amm_liquidity_modes_reject_invalid_field_matrix(fn, kwargs):
    payload = capture_json(fn, SRC, "XRP", f"USD:{DST}", **kwargs)
    assert payload["Error"] == "UsageError"
    assert "TransactionType" not in payload


@pytest.mark.parametrize(
    ("amount1", "amount2"),
    [("1", "2"), (f"USD:{DST}:1", f"USD:{DST}:2")],
)
def test_amm_create_rejects_duplicate_assets(amount1, amount2):
    payload = capture_json(tool_build_amm_create, SRC, amount1, amount2)
    assert payload["Error"] == "UsageError"
    assert "TransactionType" not in payload


@pytest.mark.parametrize(
    ("fn", "args"),
    [
        (tool_build_trustset, (SRC, "XRP", DST, "1")),
        (tool_build_clawback, (SRC, DST, "XRP", "1")),
    ],
)
def test_issued_currency_builders_reject_native_xrp_with_usage_error(fn, args):
    payload = capture_json(fn, *args)
    assert payload["Error"] == "UsageError"
    assert "TransactionType" not in payload


LOWER_XRP_HEX = "0000000000000000000000007872700000000000"


def test_lowercase_xrp_preserves_issued_currency_bytes():
    assert normalize_currency_code("xrp") == LOWER_XRP_HEX.upper()
    payment = capture_json(
        tool_build_payment, SRC, DST, "1", cur="xrp", iss=DST)
    trust = capture_json(tool_build_trustset, SRC, "xrp", DST, "1")
    claw = capture_json(tool_build_clawback, SRC, DST, "xrp", "1")
    assert payment["Amount"]["currency"] == LOWER_XRP_HEX.upper()
    assert trust["LimitAmount"]["currency"] == LOWER_XRP_HEX.upper()
    assert claw["Amount"]["currency"] == LOWER_XRP_HEX.upper()
    assert make_amount("xrp", DST, "1")["currency"] == LOWER_XRP_HEX.upper()
    from xrpl.core.binarycodec import decode, encode
    assert decode(encode(payment))["Amount"]["currency"] == "xrp"


def test_make_amount_rejects_ambiguous_native_and_issued_forms():
    with pytest.raises(ValueError, match="does not take an issuer"):
        make_amount("XRP", DST, "1")
    with pytest.raises(ValueError, match="requires an issuer"):
        make_amount("USD", None, "1")


MPT_ISSUANCE_ID = "05EECEBE97A7D635DE2393068691A015FED5A89AD203F5AA"


def test_mpt_authorize_emits_uint192_serializable_id():
    tx = capture_json(tool_build_mpt_authorize, SRC, MPT_ISSUANCE_ID)
    assert tx["MPTokenIssuanceID"] == MPT_ISSUANCE_ID
    from xrpl.core.binarycodec import encode_for_signing
    assert encode_for_signing(tx)


@pytest.mark.parametrize(
    ("issuance_id", "holder", "flags"),
    [
        ("0" * 47, None, None),
        ("0" * 49, None, None),
        ("G" * 48, None, None),
        (MPT_ISSUANCE_ID, "not-an-address", None),
        (MPT_ISSUANCE_ID, "", None),
        (MPT_ISSUANCE_ID, None, "2"),
    ],
)
def test_mpt_authorize_rejects_malformed_fields(issuance_id, holder, flags):
    payload = capture_json(
        tool_build_mpt_authorize, SRC, issuance_id, holder=holder, flags=flags)
    assert payload["Error"] == "UsageError"
    assert "TransactionType" not in payload


@pytest.mark.parametrize(
    "kwargs",
    [
        {"asset_scale": "256"},
        {"maximum_amount": "0"},
        {"maximum_amount": "9223372036854775808"},
        {"maximum_amount": "١٢٣"},
        {"transfer_fee": "50001"},
        {"flags": "1"},
    ],
)
def test_mpt_issuance_create_rejects_protocol_malformed_values(kwargs):
    payload = capture_json(tool_build_mpt_issuance_create, SRC, **kwargs)
    assert payload["Error"] == "UsageError"
    assert "TransactionType" not in payload


def test_mpt_issuance_transfer_fee_enables_required_transfer_flag():
    tx = capture_json(
        tool_build_mpt_issuance_create, SRC,
        asset_scale="6", maximum_amount="1000", transfer_fee="10")
    assert tx["Flags"] & 0x20
    from xrpl.core.binarycodec import encode_for_signing
    assert encode_for_signing(tx)


def test_mpt_maximum_amount_is_canonicalized_to_ascii_decimal():
    tx = capture_json(
        tool_build_mpt_issuance_create, SRC, maximum_amount="000123")
    assert tx["MaximumAmount"] == "123"
    from xrpl.core.binarycodec import encode_for_signing
    assert encode_for_signing(tx)


def test_dev_matrix_requires_complete_model_valid_serializable_builder_pass():
    from scripts.matrix_validation import builder_wire_error
    valid = capture_json(tool_build_payment, SRC, DST, "1")
    assert builder_wire_error("build-payment", json.dumps(valid)) is None

    def assert_matrix_error(payload, expected):
        error = builder_wire_error("build-payment", json.dumps(payload))
        assert error and expected in error

    assert_matrix_error({}, "missing TransactionType")
    assert_matrix_error({"Account": SRC}, "missing TransactionType")
    assert_matrix_error({"TransactionType": "Payment"}, "missing Account")
    assert_matrix_error(
        {"TransactionType": "Payment", "Account": SRC},
        "transaction model validation failed")
    malformed = dict(valid, Destination="not-an-address")
    error = builder_wire_error("build-payment", json.dumps(malformed))
    assert error and "binary signing serialization failed" in error
    assert builder_wire_error("build-payment", json.dumps({"Error": "UsageError"}))
    assert builder_wire_error("account", "not-json") is None


def test_dev_matrix_rejects_controlled_top_level_cli_errors():
    from scripts.matrix_validation import top_level_cli_error
    assert top_level_cli_error(json.dumps({"Error": "RuntimeError", "Message": "actNotFound"})) == "RuntimeError"
    assert top_level_cli_error(json.dumps({"HookCount": 0, "Hooks": []})) is None
    assert top_level_cli_error("not-json") is None


def test_dev_matrix_elapsed_duration_is_non_negative():
    from scripts.matrix_validation import elapsed_seconds
    assert elapsed_seconds(10.0, 11.234) == 1.23
    # Defensive clamp protects evidence if a non-monotonic caller regresses.
    assert elapsed_seconds(11.0, 10.0) == 0.0


def test_reserve_settings_use_validated_ledger_values(monkeypatch):
    class Response:
        result = {
            "info": {
                "validated_ledger": {
                    "reserve_base_xrp": "1.25",
                    "reserve_inc_xrp": "0.125",
                }
            }
        }

    monkeypatch.setattr(_shared, "_request", lambda request: Response())
    assert _shared.get_reserve_settings() == (Decimal("1.25"), Decimal("0.125"))


def test_reserve_settings_fail_closed_when_live_values_are_missing(monkeypatch):
    class Response:
        result = {"info": {"validated_ledger": {}}}

    monkeypatch.setattr(_shared, "_request", lambda request: Response())
    with pytest.raises(RuntimeError, match="unable to derive current reserve settings"):
        _shared.get_reserve_settings()


def test_reserve_settings_fail_closed_when_server_request_fails(monkeypatch):
    def fail_request(request):
        raise OSError("offline")

    monkeypatch.setattr(_shared, "_request", fail_request)
    with pytest.raises(RuntimeError, match="unable to derive current reserve settings"):
        _shared.get_reserve_settings()
