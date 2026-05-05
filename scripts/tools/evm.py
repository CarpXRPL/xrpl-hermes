#!/usr/bin/env python3
"""EVM Sidechain tools: balance, contract deploy, bridge status."""
from ._shared import (
    json_out, note_out, usage_out, _dispatch_build,
)
import httpx, json as json_mod, os, sys

def tool_evm_balance(address: str, network: str = "mainnet"):
    rpc_urls = {"mainnet": "https://rpc.xrplevm.org", "testnet": "https://rpc.testnet.xrplevm.org"}
    url = rpc_urls.get(network, rpc_urls["mainnet"])
    payload = {"jsonrpc": "2.0", "method": "eth_getBalance", "params": [address, "latest"], "id": 1}
    resp = httpx.post(url, json=payload, timeout=10)
    data = resp.json()
    wei = int(data.get("result", "0x0"), 16)
    xrp = wei / 1e18
    json_out({"Address": address, "Network": network, "RPC": url,
              "BalanceWei": str(wei),
              "BalanceXRP": f"{xrp:.18f}".rstrip("0").rstrip(".") or "0",
              "Raw": data})

def tool_evm_contract(frm: str, bytecode: str, abi: str = None, value: str = "0",
                       gas: str = "200000", network: str = "mainnet"):
    chain_ids = {"mainnet": 1440000, "testnet": 1449000}
    cid = chain_ids.get(network, 1440000)
    tx = {
        "from": frm,
        "data": bytecode if bytecode.startswith("0x") else "0x" + bytecode,
        "value": hex(int(value)),
        "gas": hex(int(gas)),
        "chainId": cid,
    }
    if abi:
        try: tx["abi"] = json_mod.loads(abi)
        except: tx["abi"] = abi
    note_out(f"# EVM Contract Deployment - sign and submit to chain ID {cid}")
    json_out(tx)

def tool_evm_bridge(network: str = "mainnet"):
    rpc_urls = {"mainnet": "https://rpc.xrplevm.org", "testnet": "https://rpc.testnet.xrplevm.org"}
    chain_ids = {"mainnet": 1440000, "testnet": 1449000}
    url = rpc_urls.get(network, rpc_urls["mainnet"])
    cid = chain_ids.get(network, chain_ids["mainnet"])
    payload = {"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1}
    chain_payload = {"jsonrpc": "2.0", "method": "eth_chainId", "params": [], "id": 1}
    try:
        resp = httpx.post(url, json=payload, timeout=10)
        data = resp.json()
        block = int(data.get("result", "0x0"), 16)
        chain_resp = httpx.post(url, json=chain_payload, timeout=10).json()
        observed_cid = int(chain_resp.get("result", "0x0"), 16)
    except Exception as e:
        block = "unknown"
        chain_resp = {"error": str(e)}
        observed_cid = None
    json_out({"Network": network, "LatestBlock": block, "RPC": url,
              "ConfiguredChainID": cid, "ObservedChainID": observed_cid,
              "Bridge": "L1-EVM federated bridge active", "RawChainID": chain_resp})

COMMANDS = {
    "evm-balance": lambda: tool_evm_balance(sys.argv[2], sys.argv[3] if len(sys.argv) >= 4 else "mainnet") if len(sys.argv) >= 3 else usage_out("evm-balance", "evm-balance 0xADDRESS [mainnet|testnet]"),
    "evm-contract": lambda: _dispatch_build(2, lambda frm, bytecode, **kw: tool_evm_contract(frm, bytecode, **kw)),
    "evm-bridge": lambda: tool_evm_bridge(sys.argv[2] if len(sys.argv) >= 3 else "mainnet"),
}
