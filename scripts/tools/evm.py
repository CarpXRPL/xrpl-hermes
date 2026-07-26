#!/usr/bin/env python3
"""Experimental/read-only XRPL EVM Sidechain helpers.

These tools do not sign or broadcast EVM transactions and do not certify a
bridge route.
"""
from decimal import Decimal
import json as json_mod
import re
import sys
from typing import Any

import httpx

from ._shared import json_out, usage_out, _dispatch_build


EVM_NETWORKS = {
    "mainnet": {"rpc": "https://rpc.xrplevm.org", "chain_id": 1440000},
    "testnet": {"rpc": "https://rpc.testnet.xrplevm.org", "chain_id": 1449000},
}
_EVM_ADDRESS_RE = re.compile(r"0x[0-9A-Fa-f]{40}\Z", re.ASCII)
_HEX_RE = re.compile(r"[0-9A-Fa-f]+\Z", re.ASCII)
_DECIMAL_RE = re.compile(r"[0-9]+\Z", re.ASCII)


def _network(network: str) -> dict[str, Any]:
    if network not in EVM_NETWORKS:
        raise ValueError("network must be mainnet or testnet")
    return EVM_NETWORKS[network]


def _address(address: str, field: str = "address") -> str:
    if not isinstance(address, str) or not _EVM_ADDRESS_RE.fullmatch(address):
        raise ValueError(f"{field} must be a 0x-prefixed 20-byte EVM address")
    return address


def _rpc(url: str, method: str, params: list[Any], timeout: float = 15) -> Any:
    response = httpx.post(
        url,
        json={"jsonrpc": "2.0", "method": method, "params": params, "id": 1},
        timeout=timeout,
    )
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise RuntimeError("EVM JSON-RPC response was not an object")
    if data.get("error"):
        error = data["error"]
        if isinstance(error, dict):
            message = error.get("message") or str(error)
            code = error.get("code")
            raise RuntimeError(f"EVM JSON-RPC error {code}: {message}")
        raise RuntimeError(f"EVM JSON-RPC error: {error}")
    if "result" not in data:
        raise RuntimeError("EVM JSON-RPC response omitted result")
    return data["result"]


def _quantity(value: Any, field: str) -> int:
    if not isinstance(value, str) or not re.fullmatch(r"0x[0-9A-Fa-f]+", value, re.ASCII):
        raise RuntimeError(f"{field} was not an EVM hex quantity")
    return int(value, 16)


def tool_evm_balance(address: str, network: str = "mainnet"):
    try:
        cfg = _network(network)
        checked = _address(address)
        raw = _rpc(cfg["rpc"], "eth_getBalance", [checked, "latest"])
        wei = _quantity(raw, "eth_getBalance result")
        observed_chain_id = _quantity(_rpc(cfg["rpc"], "eth_chainId", []), "eth_chainId result")
        if observed_chain_id != cfg["chain_id"]:
            raise RuntimeError(
                f"observed chain ID {observed_chain_id} does not match configured {cfg['chain_id']}"
            )
        xrp = Decimal(wei) / Decimal(10**18)
        json_out({
            "Address": checked,
            "Network": network,
            "ObservedChainID": observed_chain_id,
            "RPC": cfg["rpc"],
            "BalanceWei": str(wei),
            "BalanceXRP": format(xrp, "f"),
            "Status": "experimental-read-only",
            "FetchedFrom": "live EVM JSON-RPC",
        })
    except Exception as exc:
        json_out({
            "Error": type(exc).__name__,
            "Message": str(exc),
            "Network": network,
            "Address": address,
        })


def tool_evm_contract(
    frm: str,
    bytecode: str,
    abi: str | None = None,
    value: str = "0",
    gas: str = "200000",
    network: str = "mainnet",
):
    """Build an explicitly experimental unsigned deployment intent."""
    try:
        cfg = _network(network)
        sender = _address(frm, "from")
        if abi is not None:
            # ABI is developer metadata, not an eth_sendTransaction field. The
            # former tool incorrectly inserted it into the transaction object.
            raise ValueError("--abi is not accepted; append constructor args to bytecode with a verified ABI encoder")
        if not isinstance(bytecode, str):
            raise ValueError("bytecode must be hexadecimal text")
        code = bytecode[2:] if bytecode.startswith("0x") else bytecode
        if not code or len(code) % 2 or not _HEX_RE.fullmatch(code):
            raise ValueError("bytecode must be non-empty, even-length hexadecimal")
        if not isinstance(value, str) or not _DECIMAL_RE.fullmatch(value):
            raise ValueError("value must be an ASCII decimal wei amount")
        if not isinstance(gas, str) or not _DECIMAL_RE.fullmatch(gas):
            raise ValueError("gas must be an ASCII decimal gas limit")
        gas_int = int(gas)
        if gas_int < 53_000:
            raise ValueError("gas is below the 53,000 minimum intrinsic gas for contract creation")
        tx = {
            "from": sender,
            "data": "0x" + code,
            "value": hex(int(value)),
            "gas": hex(gas_int),
            "chainId": cfg["chain_id"],
        }
        json_out({
            "Status": "experimental-build-only",
            "Network": network,
            "ConfiguredChainID": cfg["chain_id"],
            "UnsignedTransaction": tx,
            "Warning": (
                "Not serialization-, simulation-, gas-, or deployment-certified. "
                "Verify chain ID live, estimate/simulate with a current EVM toolchain, "
                "and let the user's wallet sign."
            ),
        })
    except Exception as exc:
        json_out({"Error": type(exc).__name__, "Message": str(exc), "Network": network})


def tool_evm_bridge(network: str = "mainnet"):
    """Verify configured EVM network identity; do not claim bridge readiness."""
    try:
        cfg = _network(network)
        observed = _quantity(_rpc(cfg["rpc"], "eth_chainId", []), "eth_chainId result")
        block = _quantity(_rpc(cfg["rpc"], "eth_blockNumber", []), "eth_blockNumber result")
        if observed != cfg["chain_id"]:
            raise RuntimeError(
                f"observed chain ID {observed} does not match configured {cfg['chain_id']}"
            )
        json_out({
            "Network": network,
            "LatestBlock": block,
            "RPC": cfg["rpc"],
            "ConfiguredChainID": cfg["chain_id"],
            "ObservedChainID": observed,
            "Capability": "EVM network identity/status only",
            "BridgeCertified": False,
            "Message": (
                "This command does not verify gateway contracts, supported assets, "
                "minimums, fees, pause state, or a transfer route."
            ),
            "Status": "experimental-read-only",
        })
    except Exception as exc:
        json_out({"Error": type(exc).__name__, "Message": str(exc), "Network": network})


COMMANDS = {
    "evm-balance": lambda: tool_evm_balance(
        sys.argv[2], sys.argv[3] if len(sys.argv) >= 4 else "mainnet"
    ) if len(sys.argv) >= 3 else usage_out("evm-balance", "evm-balance 0xADDRESS [mainnet|testnet]"),
    "evm-contract": lambda: _dispatch_build(
        2, lambda frm, bytecode, **kw: tool_evm_contract(frm, bytecode, **kw)
    ),
    "evm-bridge": lambda: tool_evm_bridge(sys.argv[2] if len(sys.argv) >= 3 else "mainnet"),
}
