#!/usr/bin/env python3
"""Arweave storage tools: read-only cost estimation against public gateway APIs.

This module never uploads data and never handles Arweave wallet keys. It prices
permanent storage so agents can budget before using a bundler or wallet of
their own choosing.
"""
from decimal import Decimal
from ._shared import json_out, usage_out
import httpx, sys

GATEWAY = "https://arweave.net"
WINSTON_PER_AR = Decimal(10) ** 12

_SIZE_SUFFIXES = {
    "B": 1,
    "KB": 1024,
    "MB": 1024 ** 2,
    "GB": 1024 ** 3,
}


def _parse_size(arg: str) -> int:
    raw = arg.strip().upper().replace(" ", "")
    for suffix, mult in sorted(_SIZE_SUFFIXES.items(), key=lambda kv: -len(kv[0])):
        if raw.endswith(suffix):
            num = raw[: -len(suffix)]
            return int(Decimal(num) * mult)
    return int(raw)


def tool_arweave_cost(size_arg: str):
    try:
        size_bytes = _parse_size(size_arg)
    except Exception:
        json_out({"Error": "InvalidSize", "Message": f"Could not parse size '{size_arg}'. Use bytes or a KB/MB/GB suffix, e.g. 1MB."})
        return
    if size_bytes <= 0:
        json_out({"Error": "InvalidSize", "Message": "Size must be positive."})
        return
    try:
        price_resp = httpx.get(f"{GATEWAY}/price/{size_bytes}", timeout=15)
        price_resp.raise_for_status()
        winston = int(price_resp.text.strip())
    except Exception as e:
        json_out({"Error": "ArweavePriceUnavailable", "Message": str(e),
                  "Gateway": GATEWAY, "SizeBytes": size_bytes})
        return
    network = None
    try:
        info_resp = httpx.get(f"{GATEWAY}/info", timeout=15)
        info_resp.raise_for_status()
        info = info_resp.json()
        network = {"height": info.get("height"), "peers": info.get("peers"),
                   "network": info.get("network")}
    except Exception as e:
        network = {"unavailable": str(e)}
    json_out({
        "SizeBytes": size_bytes,
        "CostWinston": str(winston),
        "CostAR": str(Decimal(winston) / WINSTON_PER_AR),
        "Gateway": GATEWAY,
        "Network": network,
        "Note": "Read-only estimate from the public gateway price endpoint (base network fee, "
                "excludes bundler service margins). This tool never uploads data or touches keys.",
    })


COMMANDS = {
    "arweave-cost": lambda: tool_arweave_cost(sys.argv[2]) if len(sys.argv) >= 3 else usage_out(
        "arweave-cost", "arweave-cost SIZE  (bytes or with suffix, e.g. arweave-cost 1MB)"),
}
