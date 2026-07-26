#!/usr/bin/env python3
"""Public-address validation tools. Key material is outside XRPL-Hermes."""
from ._shared import json_out

def tool_validate_address(addr: str):
    from xrpl.core.addresscodec import is_valid_classic_address, is_valid_xaddress
    json_out({"Address": addr, "ValidClassic": is_valid_classic_address(addr),
              "ValidX": is_valid_xaddress(addr)})

import sys

COMMANDS = {
    "validate-address": lambda: tool_validate_address(sys.argv[2]) if len(sys.argv) >= 3 else print("Usage: validate-address rADDR"),
}
