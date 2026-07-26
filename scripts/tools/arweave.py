#!/usr/bin/env python3
"""Read-only Arweave base-network cost estimation."""
from datetime import datetime, timezone
from decimal import Decimal
import re
import sys

import httpx

from ._shared import json_out, usage_out

GATEWAY = "https://arweave.net"
WINSTON_PER_AR = Decimal(10) ** 12
MAX_SIZE_BYTES = 1024 ** 4  # 1 TiB safety ceiling per request
_SIZE_SUFFIXES = {"B": 1, "KB": 1024, "MB": 1024 ** 2, "GB": 1024 ** 3}


def _parse_size(arg: str) -> int:
    if not isinstance(arg, str):
        raise ValueError("invalid size")
    raw = arg.strip().upper().replace(" ", "")
    for suffix, multiplier in sorted(_SIZE_SUFFIXES.items(), key=lambda item: -len(item[0])):
        if raw.endswith(suffix):
            number = raw[:-len(suffix)]
            if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", number, re.ASCII):
                raise ValueError("invalid size")
            return int(Decimal(number) * multiplier)
    if not re.fullmatch(r"[0-9]+", raw, re.ASCII):
        raise ValueError("invalid size")
    return int(raw)


def tool_arweave_cost(size_arg: str):
    try:
        size_bytes = _parse_size(size_arg)
    except Exception:
        json_out({"Error": "InvalidSize", "Message": f"Could not parse size '{size_arg}'. Use ASCII bytes or KB/MB/GB, e.g. 1MB."})
        return
    if size_bytes <= 0:
        json_out({"Error": "InvalidSize", "Message": "Size must be positive."})
        return
    if size_bytes > MAX_SIZE_BYTES:
        json_out({"Error": "InvalidSize", "Message": "Size exceeds the 1 TiB per-request safety ceiling."})
        return
    try:
        response = httpx.get(f"{GATEWAY}/price/{size_bytes}", timeout=15)
        response.raise_for_status()
        raw_price = response.text.strip()
        if not re.fullmatch(r"[0-9]+", raw_price, re.ASCII):
            raise RuntimeError("gateway price was not an integer Winston amount")
        winston = int(raw_price)
    except Exception as exc:
        json_out({"Error": "ArweavePriceUnavailable", "Message": str(exc), "Gateway": GATEWAY, "SizeBytes": size_bytes})
        return
    try:
        response = httpx.get(f"{GATEWAY}/info", timeout=15)
        response.raise_for_status()
        info = response.json()
        if not isinstance(info, dict):
            raise RuntimeError("gateway info was not an object")
        if info.get("network") != "arweave.N.1":
            raise RuntimeError(f"unexpected Arweave network identity: {info.get('network')!r}")
        network = {"height": info.get("height"), "peers": info.get("peers"), "network": info.get("network")}
    except Exception as exc:
        json_out({"Error": "ArweaveNetworkUnavailable", "Message": str(exc), "Gateway": GATEWAY, "SizeBytes": size_bytes})
        return
    json_out({
        "SizeBytes": size_bytes,
        "CostWinston": str(winston),
        "CostAR": str(Decimal(winston) / WINSTON_PER_AR),
        "Gateway": GATEWAY,
        "FetchedAt": datetime.now(timezone.utc).isoformat(),
        "Network": network,
        "Capability": "base-network fee estimate only",
        "UploadPerformed": False,
        "Note": "Point-in-time public-gateway quote; excludes bundler/service margins and does not prove upload or retrieval.",
    })


COMMANDS = {
    "arweave-cost": lambda: tool_arweave_cost(sys.argv[2]) if len(sys.argv) >= 3 else usage_out(
        "arweave-cost", "arweave-cost SIZE  (ASCII bytes or suffix, e.g. 1MB)"
    ),
}
