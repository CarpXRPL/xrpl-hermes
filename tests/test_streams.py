import json
import pytest

from scripts import xrpl_streams
from scripts.tools._shared import normalize_currency_code

ISSUER = "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe"


def test_parse_books_xrp_and_issued_asset():
    assert xrpl_streams._parse_books(f"XRP/USD:{ISSUER}") == [{
        "taker_gets": {"currency": "XRP"},
        "taker_pays": {"currency": "USD", "issuer": ISSUER},
        "snapshot": True,
        "both": True,
    }]


def test_parse_multiple_books():
    result = xrpl_streams._parse_books(f"XRP/USD:{ISSUER};EUR:{ISSUER}/XRP")
    assert len(result) == 2
    assert result[1]["taker_gets"] == {"currency": "EUR", "issuer": ISSUER}
    assert result[1]["taker_pays"] == {"currency": "XRP"}


def test_issued_currency_uses_canonical_case_sensitive_normalization():
    result = xrpl_streams._parse_books(f"AbC:{ISSUER}/xrp:{ISSUER}")
    assert result[0]["taker_gets"]["currency"] == "AbC"
    assert result[0]["taker_pays"]["currency"] == normalize_currency_code("xrp")


def test_lowercase_xrp_without_issuer_is_rejected():
    with pytest.raises(ValueError, match="CODE:rISSUER"):
        xrpl_streams._parse_books("xrp/USD:rIssuer")


def test_invalid_issuer_is_rejected():
    with pytest.raises(ValueError, match="book issuer"):
        xrpl_streams._parse_books("XRP/USD:rIssuer")


def test_native_xrp_with_issuer_is_rejected():
    with pytest.raises(ValueError, match="must not include an issuer"):
        xrpl_streams._parse_books(f"XRP:{ISSUER}/USD:{ISSUER}")


def test_invalid_book_is_rejected_before_network(monkeypatch, capsys):
    monkeypatch.setattr(xrpl_streams.asyncio, "run", lambda *_: (_ for _ in ()).throw(
        AssertionError("network loop should not start")
    ))
    xrpl_streams.tool_subscribe(books="invalid")
    result = json.loads(capsys.readouterr().out)
    assert result["Error"] == "InvalidBooks"