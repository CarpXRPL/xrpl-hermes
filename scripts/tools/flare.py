#!/usr/bin/env python3
"""Narrow Flare FTSOv2 reads plus labeled CoinGecko context."""
from datetime import datetime, timezone
import sys

import httpx

from ._shared import json_out, usage_out

FLARE_RPC = "https://flare-api.flare.network/ext/C/rpc"
FLARE_CHAIN_ID = 14
FLARE_CONTRACT_REGISTRY = "0xaD67FE66660Fb8dFE9d6b1b4240d8650e30F6019"
_SEL_GET_CONTRACT_BY_NAME = "0x82760fca"
_SEL_GET_FEED_BY_ID = "0x93e9f806"
MAX_FEED_AGE_SECONDS = 300
COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"


def _rpc(method: str, params: list):
    response = httpx.post(
        FLARE_RPC,
        json={"jsonrpc": "2.0", "method": method, "params": params, "id": 1},
        timeout=15,
    )
    response.raise_for_status()
    body = response.json()
    if not isinstance(body, dict):
        raise RuntimeError("Flare JSON-RPC response was not an object")
    if body.get("error"):
        error = body["error"]
        message = error.get("message") if isinstance(error, dict) else str(error)
        raise RuntimeError(message or "Flare JSON-RPC call failed")
    if "result" not in body:
        raise RuntimeError("Flare JSON-RPC response omitted result")
    return body["result"]


def _eth_call(to: str, data: str) -> str:
    result = _rpc("eth_call", [{"to": to, "data": data}, "latest"])
    if not isinstance(result, str) or not result.startswith("0x"):
        raise RuntimeError("eth_call result was not hexadecimal")
    return result


def _chain_id() -> int:
    result = _rpc("eth_chainId", [])
    if not isinstance(result, str) or not result.startswith("0x"):
        raise RuntimeError("eth_chainId result was not hexadecimal")
    return int(result, 16)


def _resolve_ftso_v2() -> str:
    name = b"FtsoV2"
    data = (
        _SEL_GET_CONTRACT_BY_NAME
        + (32).to_bytes(32, "big").hex()
        + len(name).to_bytes(32, "big").hex()
        + name.hex().ljust(64, "0")
    )
    result = _eth_call(FLARE_CONTRACT_REGISTRY, data)
    if len(result) < 42:
        raise RuntimeError("ContractRegistry returned a short address result")
    address = "0x" + result[-40:]
    if int(address, 16) == 0:
        raise RuntimeError("ContractRegistry returned zero address for FtsoV2")
    return address


def _feed_id(pair: str) -> str:
    name = pair.encode("ascii")
    if len(name) > 20:
        raise ValueError(f"feed name '{pair}' longer than 20 bytes")
    return "01" + name.hex().ljust(40, "0")


def _read_feed(ftso_addr: str, pair: str) -> dict:
    data = _SEL_GET_FEED_BY_ID + _feed_id(pair).ljust(64, "0")
    result = _eth_call(ftso_addr, data)
    encoded = result[2:]
    if len(encoded) < 192:
        raise RuntimeError(f"unexpected eth_call result: {result}")
    value = int(encoded[0:64], 16)
    decimals = int(encoded[64:128], 16)
    if decimals >= 2 ** 255:
        decimals -= 2 ** 256
    if decimals < -18 or decimals > 18:
        raise RuntimeError(f"feed decimals out of accepted range: {decimals}")
    timestamp = int(encoded[128:192], 16)
    return {
        "value": value,
        "decimals": decimals,
        "price": value / (10 ** decimals),
        "timestamp": timestamp,
        "timestamp_iso": datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat(),
    }


def tool_flare_ftso(*pairs: str):
    requested = [pair.upper() for pair in (pairs or ("FLR/USD", "XRP/USD"))]
    if any("/" not in pair for pair in requested):
        usage_out("flare-ftso", "flare-ftso [PAIR ...]  (e.g. XRP/USD BTC/USD)")
        return
    fetched_at = datetime.now(timezone.utc)
    try:
        observed_chain_id = _chain_id()
        if observed_chain_id != FLARE_CHAIN_ID:
            raise RuntimeError(f"observed chain ID {observed_chain_id} does not match Flare Mainnet {FLARE_CHAIN_ID}")
        ftso_address = _resolve_ftso_v2()
    except Exception as exc:
        json_out({
            "Error": "FtsoV2Unavailable",
            "Message": str(exc),
            "RPC": FLARE_RPC,
            "ContractRegistry": FLARE_CONTRACT_REGISTRY,
            "FetchedAt": fetched_at.isoformat(),
        })
        return
    feeds, missing = {}, []
    now_epoch = int(fetched_at.timestamp())
    for pair in requested:
        try:
            feed = _read_feed(ftso_address, pair)
            age = now_epoch - feed["timestamp"]
            feed["age_seconds"] = max(0, age)
            feed["future_timestamp"] = age < -60
            feed["stale"] = age > MAX_FEED_AGE_SECONDS or age < -60
            feeds[pair] = feed
        except Exception as exc:
            missing.append({"pair": pair, "reason": str(exc)})
    json_out({
        "Source": "Flare FTSOv2 on-chain eth_call",
        "RPC": FLARE_RPC,
        "ObservedChainID": observed_chain_id,
        "ExpectedChainID": FLARE_CHAIN_ID,
        "ContractRegistry": FLARE_CONTRACT_REGISTRY,
        "FtsoV2": ftso_address,
        "FetchedAt": fetched_at.isoformat(),
        "MaxFeedAgeSeconds": MAX_FEED_AGE_SECONDS,
        "Feeds": feeds,
        "MissingFeeds": missing,
        "Status": "narrow-on-chain-read",
    })


COINGECKO_IDS = {
    "XRP": "ripple", "BTC": "bitcoin", "ETH": "ethereum",
    "FLR": "flare-networks", "SGB": "songbird", "USDC": "usd-coin",
    "USDT": "tether", "RLUSD": "ripple-usd",
}


def tool_flare_price(*symbols: str):
    requested = [symbol.upper() for symbol in (symbols or ("XRP", "FLR"))]
    ids = {symbol: COINGECKO_IDS.get(symbol) for symbol in requested}
    missing = [symbol for symbol, coin_id in ids.items() if not coin_id]
    query_ids = ",".join(sorted({coin_id for coin_id in ids.values() if coin_id}))
    prices = {symbol: None for symbol in requested}
    fetched_at = datetime.now(timezone.utc).isoformat()
    if query_ids:
        try:
            response = httpx.get(COINGECKO_URL, params={"ids": query_ids, "vs_currencies": "usd"}, timeout=15)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                raise RuntimeError("CoinGecko response was not an object")
            reverse = {coin_id: symbol for symbol, coin_id in ids.items() if coin_id}
            for coin_id, values in data.items():
                symbol = reverse.get(coin_id)
                if symbol and isinstance(values, dict):
                    prices[symbol] = values.get("usd")
        except Exception as exc:
            json_out({
                "Error": "PriceFetchFailed", "Message": str(exc),
                "Source": COINGECKO_URL, "FetchedAt": fetched_at,
                "PricesUSD": prices, "MissingSymbols": missing,
                "Capability": "market context only; not oracle proof",
            })
            return
    json_out({
        "Source": COINGECKO_URL,
        "FetchedAt": fetched_at,
        "PricesUSD": prices,
        "MissingSymbols": missing,
        "Capability": "market context only; not oracle proof",
    })


COMMANDS = {
    "flare-ftso": lambda: tool_flare_ftso(*sys.argv[2:]),
    "flare-price": lambda: tool_flare_price(*sys.argv[2:]),
}
