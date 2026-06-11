#!/usr/bin/env python3
"""Flare price feeds.

flare-ftso reads FTSOv2 feeds directly from the Flare C-chain via eth_call —
real on-chain oracle values. flare-price remains a CoinGecko convenience
fallback and labels its source honestly.
"""
import sys
from datetime import datetime, timezone
import httpx
from ._shared import json_out, note_out, usage_out

FLARE_RPC = "https://flare-api.flare.network/ext/C/rpc"
# FlareContractRegistry has the same address on all Flare networks (dev.flare.network).
FLARE_CONTRACT_REGISTRY = "0xaD67FE66660Fb8dFE9d6b1b4240d8650e30F6019"
# keccak4("getContractAddressByName(string)") / keccak4("getFeedById(bytes21)")
_SEL_GET_CONTRACT_BY_NAME = "0x82760fca"
_SEL_GET_FEED_BY_ID = "0x93e9f806"


def _eth_call(to: str, data: str) -> str:
    payload = {"jsonrpc": "2.0", "method": "eth_call",
               "params": [{"to": to, "data": data}, "latest"], "id": 1}
    resp = httpx.post(FLARE_RPC, json=payload, timeout=15)
    resp.raise_for_status()
    body = resp.json()
    if "error" in body:
        raise RuntimeError(body["error"].get("message", "eth_call failed"))
    return body.get("result", "0x")


def _resolve_ftso_v2() -> str:
    name = b"FtsoV2"
    data = (_SEL_GET_CONTRACT_BY_NAME
            + (32).to_bytes(32, "big").hex()
            + len(name).to_bytes(32, "big").hex()
            + name.hex().ljust(64, "0"))
    result = _eth_call(FLARE_CONTRACT_REGISTRY, data)
    addr = "0x" + result[-40:]
    if int(addr, 16) == 0:
        raise RuntimeError("ContractRegistry returned zero address for FtsoV2")
    return addr


def _feed_id(pair: str) -> str:
    """FTSOv2 feed ID: category byte 0x01 (crypto) + ASCII pair name, 21 bytes."""
    name = pair.encode("ascii")
    if len(name) > 20:
        raise ValueError(f"feed name '{pair}' longer than 20 bytes")
    return "01" + name.hex().ljust(40, "0")


def _read_feed(ftso_addr: str, pair: str) -> dict:
    data = _SEL_GET_FEED_BY_ID + _feed_id(pair).ljust(64, "0")
    result = _eth_call(ftso_addr, data)
    h = result[2:]
    if len(h) < 192:
        raise RuntimeError(f"unexpected eth_call result: {result}")
    value = int(h[0:64], 16)
    decimals = int(h[64:128], 16)
    if decimals >= 2 ** 255:  # int8 sign-extended to 256 bits
        decimals -= 2 ** 256
    timestamp = int(h[128:192], 16)
    return {
        "value": value,
        "decimals": decimals,
        "price": value / (10 ** decimals),
        "timestamp": timestamp,
        "timestamp_iso": datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat(),
    }


def tool_flare_ftso(*pairs: str):
    requested = [p.upper() for p in (pairs or ("FLR/USD", "XRP/USD"))]
    bad = [p for p in requested if "/" not in p]
    if bad:
        usage_out("flare-ftso", "flare-ftso [PAIR ...]  (e.g. flare-ftso XRP/USD BTC/USD; default FLR/USD XRP/USD)")
        return
    try:
        ftso_addr = _resolve_ftso_v2()
    except Exception as e:
        json_out({"Error": "FtsoV2Unavailable", "Message": str(e),
                  "RPC": FLARE_RPC, "ContractRegistry": FLARE_CONTRACT_REGISTRY})
        return
    feeds, missing = {}, []
    for pair in requested:
        try:
            feeds[pair] = _read_feed(ftso_addr, pair)
        except Exception as e:
            missing.append({"pair": pair, "reason": str(e)})
    json_out({
        "Source": "Flare FTSOv2 on-chain (eth_call)",
        "RPC": FLARE_RPC,
        "FtsoV2": ftso_addr,
        "Feeds": feeds,
        "MissingFeeds": missing,
        "Note": "Values read live from the FtsoV2 contract resolved via the FlareContractRegistry. "
                "A missing feed usually means no FTSOv2 feed exists for that pair name.",
    })

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
    "flare-ftso": lambda: tool_flare_ftso(*sys.argv[2:]),
    "flare-price": lambda: tool_flare_price(*sys.argv[2:]),
}
