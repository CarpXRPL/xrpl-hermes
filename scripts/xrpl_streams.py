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

def tool_subscribe(streams="ledger", accounts="", books="", duration="0"):
    s = [x for x in streams.split(",") if x]
    a = [x for x in accounts.split(",") if x]
    b = []
    asyncio.run(_stream(s, a, b, int(duration)))

def _dispatch_subscribe():
    kwargs = {}
    for i in range(2, len(sys.argv) - 1, 2):
        k = sys.argv[i].lstrip("--").replace("-", "_")
        kwargs[k] = sys.argv[i + 1]
    tool_subscribe(**kwargs)

COMMANDS = {"subscribe": _dispatch_subscribe}
