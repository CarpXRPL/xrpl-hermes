#!/usr/bin/env python3
"""Flare / price feed helper.

The old public Flare FTSO HTTP endpoints used by this project no longer return
feed data reliably. This command now uses CoinGecko's free simple price API as a
public fallback and labels the source honestly. It is a price helper, not a
proof that the value came from an on-chain FTSO contract.
"""
import sys
import httpx
from ._shared import json_out, note_out

COINGECKO_IDS = {
    "XRP": "ripple",
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "FLR": "flare-networks",
    "SGB": "songbird",
    "USDC": "usd-coin",
    "USDT": "tether",
    "RLUSD": "ripple-usd",
}


def tool_flare_price(*symbols: str):
    requested = [s.upper() for s in (symbols or ("XRP", "FLR"))]
    ids = {sym: COINGECKO_IDS.get(sym) for sym in requested}
    missing = [sym for sym, coin_id in ids.items() if not coin_id]
    query_ids = ",".join(sorted({coin_id for coin_id in ids.values() if coin_id}))

    result = {sym: None for sym in requested}
    source = "CoinGecko simple price API fallback"
    if query_ids:
        url = "https://api.coingecko.com/api/v3/simple/price"
        try:
            resp = httpx.get(url, params={"ids": query_ids, "vs_currencies": "usd"}, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            reverse = {coin_id: sym for sym, coin_id in ids.items() if coin_id}
            for coin_id, values in data.items():
                sym = reverse.get(coin_id)
                if sym:
                    result[sym] = values.get("usd")
        except Exception as e:
            json_out({
                "Error": "PriceFetchFailed",
                "Message": str(e),
                "Source": source,
                "PricesUSD": result,
                "MissingSymbols": missing,
                "Note": "This helper no longer claims direct FTSO HTTP data when public Flare endpoints are unavailable.",
            })
            return

    if missing:
        note_out(f"# Unknown price symbol(s): {', '.join(missing)}. Add a CoinGecko ID mapping before relying on them.")
    note_out("# Price source: CoinGecko fallback, not direct on-chain FTSO proof.")
    json_out({
        "Source": source,
        "PricesUSD": result,
        "MissingSymbols": missing,
        "Note": "Use this for quick market context only. For production oracle logic, query verified Flare FTSO/on-chain sources directly.",
    })


COMMANDS = {
    "flare-price": lambda: tool_flare_price(*sys.argv[2:]),
}
