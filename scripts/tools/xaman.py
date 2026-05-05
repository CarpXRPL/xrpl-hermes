#!/usr/bin/env python3
"""Xaman Platform API integration tool."""
from ._shared import (
    json_out, note_out,
)
import os, json as json_mod, sys, httpx

def tool_xaman_payload(tx_json_str: str):
    api_key = os.environ.get("XUMM_API_KEY")
    api_secret = os.environ.get("XUMM_API_SECRET")
    if not (api_key and api_secret):
        json_out({"Error": "MissingCredentials",
                  "Message": "Set XUMM_API_KEY and XUMM_API_SECRET. Free at https://apps.xumm.dev"})
        return
    try:
        tx_obj = json_mod.loads(tx_json_str)
        resp = httpx.post(
            "https://xumm.app/api/v1/platform/payload",
            headers={"X-API-Key": api_key, "X-API-Secret": api_secret,
                     "Content-Type": "application/json"},
            json={"txjson": tx_obj}, timeout=15,
        )
        data = resp.json()
        json_out({
            "PayloadUUID": data.get("uuid"),
            "SignURL": data.get("next", {}).get("always"),
            "QRPng": data.get("refs", {}).get("qr_png"),
            "WSStatus": data.get("refs", {}).get("websocket_status"),
            "Pushed": data.get("pushed"),
            "Raw": data,
        })
    except Exception as e:
        json_out({"Error": "XamanPayloadError", "Message": str(e)})

COMMANDS = {
    "xaman-payload": lambda: tool_xaman_payload(sys.argv[2]) if len(sys.argv) >= 3 else print("Usage: xaman-payload '{\"TransactionType\":...}'"),
}
