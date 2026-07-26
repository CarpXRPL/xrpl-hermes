#!/usr/bin/env python3
"""Streaming tools. Requires websockets (bundled with xrpl-py >= 2.5)."""
import asyncio, json, signal, sys
from xrpl.asyncio.clients import AsyncWebsocketClient
from xrpl.models.requests import Subscribe
from scripts.tools._shared import normalize_currency_code, validate_xrpl_address

WSS_ENDPOINTS = ["wss://xrplcluster.com", "wss://s1.ripple.com", "wss://s2.ripple.com"]


def _parse_asset(value: str) -> dict:
    value = value.strip()
    if value == "XRP":
        return {"currency": "XRP"}
    try:
        currency, issuer = value.split(":", 1)
    except ValueError as exc:
        raise ValueError(f"issued asset must use CODE:rISSUER, got {value!r}") from exc
    if not currency or not issuer:
        raise ValueError(f"issued asset must use CODE:rISSUER, got {value!r}")
    if currency == "XRP":
        raise ValueError("native XRP must not include an issuer")
    return {
        "currency": normalize_currency_code(currency),
        "issuer": validate_xrpl_address(issuer, "book issuer"),
    }


def _parse_books(value: str) -> list[dict]:
    books = []
    for item in (part.strip() for part in value.split(";")):
        if not item:
            continue
        try:
            taker_gets, taker_pays = item.split("/", 1)
        except ValueError as exc:
            raise ValueError(f"book must use ASSET/ASSET, got {item!r}") from exc
        books.append({
            "taker_gets": _parse_asset(taker_gets),
            "taker_pays": _parse_asset(taker_pays),
            "snapshot": True,
            "both": True,
        })
    return books

async def _stream(streams, accounts, books, duration):
    for ep in WSS_ENDPOINTS:
        try:
            async with AsyncWebsocketClient(ep) as client:
                req = Subscribe(
                    streams=streams or None,
                    accounts=accounts or None,
                    books=books or None,
                )
                await client.send(req)
                stop = asyncio.Event()
                if duration > 0:
                    asyncio.get_event_loop().call_later(duration, stop.set)
                signal.signal(signal.SIGINT, lambda *_: stop.set())
                async for msg in client:
                    print(json.dumps(msg), flush=True)
                    if stop.is_set():
                        return
            return
        except Exception:
            continue

def tool_subscribe(streams="ledger", accounts="", books="", duration="0", count=None):
    s = [x for x in streams.split(",") if x]
    a = [x for x in accounts.split(",") if x]
    try:
        b = _parse_books(books)
    except ValueError as exc:
        print(json.dumps({"Error": "InvalidBooks", "Message": str(exc)}))
        return
    # --count N is an alias for duration when interpreted as max messages;
    # for simplicity treat it the same as duration seconds if duration not set.
    if count is not None and (duration in (None, "", "0")):
        duration = count
    asyncio.run(_stream(s, a, b, int(duration or 0)))

_VALID_KWARGS = {"streams", "accounts", "books", "duration", "count"}

def _dispatch_subscribe():
    kwargs = {}
    i = 2
    while i < len(sys.argv):
        tok = sys.argv[i]
        if tok.startswith("--") and i + 1 < len(sys.argv):
            k = tok.lstrip("-").replace("-", "_")
            if k in _VALID_KWARGS:
                kwargs[k] = sys.argv[i + 1]
            i += 2
        elif "=" in tok:
            k, v = tok.split("=", 1)
            k = k.replace("-", "_")
            if k in _VALID_KWARGS:
                kwargs[k] = v
            i += 1
        else:
            i += 1
    tool_subscribe(**kwargs)

COMMANDS = {"subscribe": _dispatch_subscribe}
