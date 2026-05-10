#!/usr/bin/env python3
"""Streaming tools. Requires websockets (bundled with xrpl-py >= 2.5)."""
import asyncio, json, signal, sys
from xrpl.asyncio.clients import AsyncWebsocketClient
from xrpl.models.requests import Subscribe

WSS_ENDPOINTS = ["wss://xrplcluster.com", "wss://s1.ripple.com", "wss://s2.ripple.com"]

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
    b = []
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
