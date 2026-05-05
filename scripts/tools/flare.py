#!/usr/bin/env python3
"""Flare FTSO price feed tool."""
from ._shared import (
    json_out,
)
import httpx, sys

def tool_flare_price(*symbols: str):
    urls = [
        "https://api.flare.network/ftso/v2/feeds",
        "https://flare-api.flare.network/ftso/v2/feeds",
    ]
    feeds = {}
    for url in urls:
        try:
            resp = httpx.get(url, timeout=10)
            data = resp.json()
            for f in data:
                feed_name = f.get("feed", "").upper()
                if feed_name: feeds[feed_name] = float(f.get("value", 0))
            break
        except Exception: continue
    result = {}
    for sym in symbols:
        s = sym.upper()
        result[s] = feeds.get(s)
    json_out({"Prices": result, "FeedCount": len(feeds)})

COMMANDS = {
    "flare-price": lambda: tool_flare_price(*sys.argv[2:]),
}
