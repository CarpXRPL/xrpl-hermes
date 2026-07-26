#!/usr/bin/env python3
"""Xaman Platform API payload handoff with strict preflight checks."""
from datetime import datetime, timezone
import json as json_mod
import os
import sys
from urllib.parse import urlparse
from uuid import UUID

import httpx

from ._shared import (
    json_out, usage_out, validate_positive_drops_amount,
    validate_positive_issued_value, validate_xrpl_address,
)
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.transactions import Payment, Transaction


_XAHAU_ONLY_TYPES = {
    "SetHook", "Invoke", "Remit", "Import",
    "URITokenMint", "URITokenBurn", "URITokenCreateSellOffer",
    "URITokenBuy", "URITokenCancelSellOffer",
}
_FORBIDDEN_KEYS = {
    "seed", "secret", "privatekey", "private_key", "mnemonic",
    "masterseed", "master_seed", "passphrase",
}
_VALIDATION_ACCOUNT = "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh"
_ALT_VALIDATION_ACCOUNT = "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe"


def _contains_forbidden_key(value) -> str | None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).replace("-", "_").lower()
            if normalized in _FORBIDDEN_KEYS:
                return str(key)
            found = _contains_forbidden_key(child)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _contains_forbidden_key(child)
            if found:
                return found
    return None


def _validate_transaction(value) -> dict:
    if not isinstance(value, dict):
        raise ValueError("transaction JSON must be an object")
    forbidden = _contains_forbidden_key(value)
    if forbidden:
        raise ValueError(f"transaction JSON contains forbidden key-material field: {forbidden}")
    tx_type = value.get("TransactionType")
    if not isinstance(tx_type, str) or not tx_type.strip():
        raise ValueError("TransactionType is required")
    if tx_type in _XAHAU_ONLY_TYPES or value.get("NetworkID") not in (None, 0):
        raise ValueError("Xahau and non-XRPL network payloads are not certified by xaman-payload")
    if "TxnSignature" in value or value.get("SigningPubKey"):
        raise ValueError("xaman-payload accepts unsigned transaction JSON only")
    if tx_type != "Payment":
        raise ValueError("xaman-payload currently certifies Payment intents only")
    missing = sorted(field for field in ("Destination", "Amount") if field not in value)
    if missing:
        raise ValueError(f"Payment payload is missing required intent field(s): {', '.join(missing)}")
    validate_xrpl_address(value["Destination"], "Destination")
    if value.get("Account") is not None:
        validate_xrpl_address(value["Account"], "Account")
    amount = value["Amount"]
    if isinstance(amount, str):
        validate_positive_drops_amount(amount, "Amount")
    elif isinstance(amount, dict):
        parsed = IssuedCurrencyAmount.from_dict(amount)
        validate_xrpl_address(parsed.issuer, "Amount issuer")
        validate_positive_issued_value(str(parsed.value), "Amount")
    else:
        raise ValueError("Payment Amount must be drops text or an issued-currency object")
    # Model validation catches malformed optional Payment fields. Xaman may fill
    # Account, so use a fixed public placeholder only for local validation.
    candidate = dict(value)
    if "Account" not in candidate:
        candidate["Account"] = (
            _ALT_VALIDATION_ACCOUNT
            if value["Destination"] == _VALIDATION_ACCOUNT
            else _VALIDATION_ACCOUNT
        )
    model = Transaction.from_xrpl(candidate)
    if not isinstance(model, Payment):
        raise ValueError("transaction model did not resolve to Payment")
    return value


def _validate_response(data) -> tuple[str, str]:
    if not isinstance(data, dict):
        raise RuntimeError("Xaman response was not a JSON object")
    if data.get("error"):
        raise RuntimeError(f"Xaman API error: {data['error']}")
    uuid = data.get("uuid")
    try:
        UUID(str(uuid))
    except (TypeError, ValueError, AttributeError) as exc:
        raise RuntimeError("Xaman response omitted a valid payload UUID") from exc
    sign_url = data.get("next", {}).get("always") if isinstance(data.get("next"), dict) else None
    parsed = urlparse(sign_url or "")
    if parsed.scheme != "https" or not parsed.hostname or not (
        parsed.hostname == "xumm.app" or parsed.hostname.endswith(".xumm.app")
    ):
        raise RuntimeError("Xaman response omitted a trusted HTTPS signing URL")
    return str(uuid), str(sign_url)


def tool_xaman_payload(tx_json_str: str):
    """Create a real external Xaman signing request after local validation."""
    try:
        tx_obj = _validate_transaction(json_mod.loads(tx_json_str))
    except Exception as exc:
        json_out({
            "Error": "XamanPayloadError",
            "Message": str(exc),
            "ExternalSideEffectCreated": False,
        })
        return
    api_key = os.environ.get("XUMM_API_KEY")
    api_secret = os.environ.get("XUMM_API_SECRET")
    if not (api_key and api_secret):
        json_out({
            "Error": "MissingCredentials",
            "Message": "Set XUMM_API_KEY and XUMM_API_SECRET from the Xaman developer console.",
            "ExternalSideEffectCreated": False,
        })
        return
    try:
        response = httpx.post(
            "https://xumm.app/api/v1/platform/payload",
            headers={
                "X-API-Key": api_key,
                "X-API-Secret": api_secret,
                "Content-Type": "application/json",
            },
            json={"txjson": tx_obj},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        payload_uuid, sign_url = _validate_response(data)
        refs = data.get("refs") if isinstance(data.get("refs"), dict) else {}
        json_out({
            "PayloadUUID": payload_uuid,
            "SignURL": sign_url,
            "QRPng": refs.get("qr_png"),
            "WSStatus": refs.get("websocket_status"),
            "Pushed": data.get("pushed"),
            "ExternalSideEffectCreated": True,
            "Provider": "Xaman Platform API",
            "CreatedAt": datetime.now(timezone.utc).isoformat(),
            "Warning": "Wallet completion is provisional; verify the final validated XRPL transaction independently.",
        })
    except Exception as exc:
        json_out({
            "Error": "XamanPayloadError",
            "Message": str(exc),
            "ExternalSideEffectCreated": False,
        })


COMMANDS = {
    "xaman-payload": lambda: tool_xaman_payload(sys.argv[2]) if len(sys.argv) >= 3 else usage_out(
        "xaman-payload", 'xaman-payload \'{"TransactionType":"Payment",...}\''
    ),
}
