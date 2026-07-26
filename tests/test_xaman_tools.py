"""Safety and response validation tests for Xaman payload handoff."""
import json

import pytest

from scripts.tools import xaman


def test_xaman_transaction_validation_rejects_incomplete_payment():
    with pytest.raises(ValueError, match="Destination, Amount|Amount, Destination"):
        xaman._validate_transaction({"TransactionType": "Payment"})


def test_xaman_transaction_validation_rejects_key_material_recursively():
    with pytest.raises(ValueError, match="forbidden"):
        xaman._validate_transaction({
            "TransactionType": "Payment",
            "Destination": "rDestination",
            "Amount": "1",
            "Memos": [{"secret": "sNever"}],
        })


def test_xaman_transaction_validation_rejects_xahau_and_signed_payloads():
    with pytest.raises(ValueError, match="Xahau"):
        xaman._validate_transaction({"TransactionType": "SetHook", "Hooks": []})
    with pytest.raises(ValueError, match="Xahau"):
        xaman._validate_transaction({"TransactionType": "Payment", "Destination": "rD", "Amount": "1", "NetworkID": 21337})
    with pytest.raises(ValueError, match="unsigned"):
        xaman._validate_transaction({"TransactionType": "AccountSet", "SetFlag": 8, "TxnSignature": "AB"})


def test_xaman_transaction_validation_accepts_complete_unsigned_payment():
    tx = {"TransactionType": "Payment", "Destination": "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe", "Amount": "1"}
    assert xaman._validate_transaction(tx) is tx


def test_xaman_transaction_validation_rejects_unvalidated_type_and_bad_payment():
    with pytest.raises(ValueError, match="Payment intents only"):
        xaman._validate_transaction({"TransactionType": "AccountSet", "SetFlag": 8})
    with pytest.raises(ValueError, match="Destination"):
        xaman._validate_transaction({"TransactionType": "Payment", "Destination": "rBad", "Amount": "1"})
    with pytest.raises(ValueError, match="positive"):
        xaman._validate_transaction({"TransactionType": "Payment", "Destination": "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe", "Amount": "0"})


def test_xaman_response_requires_uuid_and_trusted_url():
    uuid = "12345678-1234-5678-1234-567812345678"
    assert xaman._validate_response({"uuid": uuid, "next": {"always": "https://xumm.app/sign/abc"}}) == (
        uuid,
        "https://xumm.app/sign/abc",
    )
    with pytest.raises(RuntimeError, match="UUID"):
        xaman._validate_response({"next": {"always": "https://xumm.app/sign/abc"}})
    with pytest.raises(RuntimeError, match="trusted"):
        xaman._validate_response({"uuid": uuid, "next": {"always": "https://evil.example/sign/abc"}})


def test_xaman_tool_does_not_create_side_effect_without_credentials(monkeypatch, capsys):
    monkeypatch.delenv("XUMM_API_KEY", raising=False)
    monkeypatch.delenv("XUMM_API_SECRET", raising=False)
    monkeypatch.setattr(xaman.httpx, "post", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("API called")))
    xaman.tool_xaman_payload('{"TransactionType":"Payment","Destination":"rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe","Amount":"1"}')
    out = json.loads(capsys.readouterr().out)
    assert out["Error"] == "MissingCredentials"
    assert out["ExternalSideEffectCreated"] is False


def test_xaman_tool_rejects_invalid_intent_before_credentials(monkeypatch, capsys):
    monkeypatch.delenv("XUMM_API_KEY", raising=False)
    monkeypatch.delenv("XUMM_API_SECRET", raising=False)
    xaman.tool_xaman_payload('{"TransactionType":"AccountSet","SetFlag":8}')
    out = json.loads(capsys.readouterr().out)
    assert out["Error"] == "XamanPayloadError"
    assert "Payment intents only" in out["Message"]
    assert out["ExternalSideEffectCreated"] is False


def test_xaman_tool_rejects_malformed_response(monkeypatch, capsys):
    monkeypatch.setenv("XUMM_API_KEY", "key")
    monkeypatch.setenv("XUMM_API_SECRET", "secret")

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"error": {"code": 400, "message": "bad payload"}}

    monkeypatch.setattr(xaman.httpx, "post", lambda *args, **kwargs: Response())
    xaman.tool_xaman_payload('{"TransactionType":"Payment","Destination":"rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe","Amount":"1"}')
    out = json.loads(capsys.readouterr().out)
    assert out["Error"] == "XamanPayloadError"
    assert out["ExternalSideEffectCreated"] is False


def test_xaman_tool_reports_created_payload_without_echoing_raw(monkeypatch, capsys):
    monkeypatch.setenv("XUMM_API_KEY", "key")
    monkeypatch.setenv("XUMM_API_SECRET", "secret")

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "uuid": "12345678-1234-5678-1234-567812345678",
                "next": {"always": "https://xumm.app/sign/abc"},
                "refs": {"qr_png": "https://xumm.app/qr/abc", "websocket_status": "wss://xumm.app/sign/abc"},
                "pushed": True,
            }

    monkeypatch.setattr(xaman.httpx, "post", lambda *args, **kwargs: Response())
    xaman.tool_xaman_payload('{"TransactionType":"Payment","Destination":"rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe","Amount":"1"}')
    out = json.loads(capsys.readouterr().out)
    assert out["ExternalSideEffectCreated"] is True
    assert out["PayloadUUID"] == "12345678-1234-5678-1234-567812345678"
    assert "Raw" not in out
