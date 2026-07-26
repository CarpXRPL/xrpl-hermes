#!/usr/bin/env python3
"""Read-only Xahau network tools and deterministic HookOn calculation.

No function in this module signs or submits a transaction.
"""
from datetime import datetime, timezone
import re
import sys
from typing import Any

import httpx
from xrpl.core.addresscodec import is_valid_classic_address

from ._shared import json_out, usage_out

# Official public JSON-RPC endpoints and network IDs. The live server_info result
# is checked on every hooks-info request so an endpoint cannot be silently
# mislabeled.
XAHAU_NETWORKS = {
    "mainnet": {"endpoint": "https://xahau.network", "network_id": 21337},
    "testnet": {"endpoint": "https://xahau-test.net", "network_id": 21338},
}

# Xahau transaction-type IDs for HookOn bit positions.
# Protocol source (reviewed 2026-07-25):
# https://github.com/Xahau/xahaud/blob/bb244ef7729503a0317bcff0f8fdaa93ca5cb7d2/include/xrpl/protocol/detail/transactions.macro
HOOKON_TT = {
    "Payment": 0,
    "EscrowCreate": 1,
    "EscrowFinish": 2,
    "AccountSet": 3,
    "EscrowCancel": 4,
    "SetRegularKey": 5,
    "NicknameSet": 6,
    "OfferCreate": 7,
    "OfferCancel": 8,
    "Contract": 9,
    "TicketCreate": 10,
    "SpinalTap": 11,
    "SignerListSet": 12,
    "PaymentChannelCreate": 13,
    "PaymentChannelFund": 14,
    "PaymentChannelClaim": 15,
    "CheckCreate": 16,
    "CheckCash": 17,
    "CheckCancel": 18,
    "DepositPreauth": 19,
    "TrustSet": 20,
    "AccountDelete": 21,
    "SetHook": 22,
    "NFTokenMint": 25,
    "NFTokenBurn": 26,
    "NFTokenCreateOffer": 27,
    "NFTokenCancelOffer": 28,
    "NFTokenAcceptOffer": 29,
    "Clawback": 30,
    "AMMClawback": 31,
    "AMMCreate": 35,
    "AMMDeposit": 36,
    "AMMWithdraw": 37,
    "AMMVote": 38,
    "AMMBid": 39,
    "AMMDelete": 40,
    "URITokenMint": 45,
    "URITokenBurn": 46,
    "URITokenBuy": 47,
    "URITokenCreateSellOffer": 48,
    "URITokenCancelSellOffer": 49,
    "XChainCreateClaimID": 50,
    "XChainCommit": 51,
    "XChainClaim": 52,
    "XChainAccountCreateCommit": 53,
    "XChainAddClaimAttestation": 54,
    "XChainAddAccountCreateAttestation": 55,
    "XChainModifyBridge": 56,
    "XChainCreateBridge": 57,
    "DIDSet": 58,
    "DIDDelete": 59,
    "OracleSet": 60,
    "OracleDelete": 61,
    "LedgerStateFix": 62,
    "MPTokenIssuanceCreate": 63,
    "MPTokenIssuanceDestroy": 64,
    "MPTokenIssuanceSet": 65,
    "MPTokenAuthorize": 66,
    "CredentialCreate": 67,
    "CredentialAccept": 68,
    "CredentialDelete": 69,
    "NFTokenModify": 70,
    "PermissionedDomainSet": 71,
    "PermissionedDomainDelete": 72,
    "Cron": 92,
    "CronSet": 93,
    "SetRemarks": 94,
    "Remit": 95,
    "GenesisMint": 96,
    "Import": 97,
    "ClaimReward": 98,
    "Invoke": 99,
    "EnableAmendment": 100,
    "SetFee": 101,
    "UNLModify": 102,
    "EmitFailure": 103,
    "UNLReport": 104,
}

_TT_HOOK_SET = 22
_ALL_ONES_256 = (1 << 256) - 1
_ASCII_UINT = re.compile(r"[0-9]+")

# Accept ttPAYMENT / PAYCHAN_CREATE / payment etc. alongside canonical names.
_TT_ALIASES = {
    "REGULAR_KEY_SET": "SetRegularKey",
    "HOOK_SET": "SetHook",
    "REMARKS_SET": "SetRemarks",
    "PAYCHAN_CREATE": "PaymentChannelCreate",
    "PAYCHAN_FUND": "PaymentChannelFund",
    "PAYCHAN_CLAIM": "PaymentChannelClaim",
}


def _network_config(network: str) -> dict[str, Any]:
    name = (network or "").strip().lower()
    if name not in XAHAU_NETWORKS:
        raise ValueError("network must be exactly 'mainnet' or 'testnet'")
    return {"name": name, **XAHAU_NETWORKS[name]}


def _normalize_tt(token: str):
    """Resolve a transaction-type name or ASCII numeric ID."""
    raw = token.strip()
    if _ASCII_UINT.fullmatch(raw):
        tt = int(raw)
        for name, num in HOOKON_TT.items():
            if num == tt:
                return name, num
        if 0 <= tt < 256:
            return f"tt{tt}", tt
        raise ValueError(f"transaction type ID {tt} out of range 0-255")
    if not raw:
        raise ValueError("transaction type must not be empty")
    cleaned = raw[2:] if raw[:2].lower() == "tt" else raw
    cleaned = _TT_ALIASES.get(cleaned.upper().replace("-", "_"), cleaned)
    folded = cleaned.replace("_", "").replace("-", "").lower()
    for name, num in HOOKON_TT.items():
        if name.lower() == folded:
            return name, num
    known = ", ".join(sorted(HOOKON_TT))
    raise ValueError(f"unknown transaction type '{token}'. Known: {known}")


def compute_hookon(tt_ids) -> int:
    """Compute a HookOn value that fires on exactly the given type IDs.

    HookOn is active-low except ttHOOK_SET bit 22, which is active-high.
    """
    mask = _ALL_ONES_256 & ~(1 << _TT_HOOK_SET)
    for tt in tt_ids:
        if not isinstance(tt, int) or isinstance(tt, bool) or not 0 <= tt < 256:
            raise ValueError("transaction type IDs must be integers in range 0-255")
        if tt == _TT_HOOK_SET:
            mask |= 1 << _TT_HOOK_SET
        else:
            mask &= ~(1 << tt)
    return mask


def _rpc(endpoint: str, method: str, params: dict[str, Any]) -> dict[str, Any]:
    response = httpx.post(endpoint, json={"method": method, "params": [params]}, timeout=20)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("Xahau RPC returned a non-object JSON payload")
    result = payload.get("result")
    if not isinstance(result, dict):
        raise RuntimeError("Xahau RPC response is missing a result object")
    if result.get("status") == "error" or result.get("error"):
        code = result.get("error") or "rpcError"
        message = result.get("error_message") or "Xahau RPC request failed"
        raise RuntimeError(f"{code}: {message}")
    return result


def _live_network_metadata(config: dict[str, Any]) -> dict[str, Any]:
    result = _rpc(config["endpoint"], "server_info", {})
    info = result.get("info", {})
    actual_id = info.get("network_id")
    if actual_id != config["network_id"]:
        raise RuntimeError(
            f"endpoint network mismatch: expected {config['network_id']}, received {actual_id}"
        )
    return {
        "Network": config["name"],
        "NetworkID": actual_id,
        "Endpoint": config["endpoint"],
        "ServerVersion": info.get("build_version"),
        "FetchedAt": datetime.now(timezone.utc).isoformat(),
    }


def tool_hooks_info(address: str, network: str = "mainnet"):
    try:
        config = _network_config(network)
        if not is_valid_classic_address(address):
            raise ValueError("account must be a valid classic r-address; X-addresses are not accepted")
        metadata = _live_network_metadata(config)
        result = _rpc(
            config["endpoint"],
            "account_objects",
            {"account": address, "ledger_index": "validated", "type": "hook", "limit": 20},
        )
        chain = []
        for ledger_object in result.get("account_objects", []):
            if ledger_object.get("LedgerEntryType") != "Hook":
                continue
            for slot, wrapper in enumerate(ledger_object.get("Hooks", [])):
                hook = wrapper.get("Hook", {}) if isinstance(wrapper, dict) else {}
                if hook.get("HookHash"):
                    chain.append({"Slot": slot, **hook})
        json_out({
            "Account": address,
            "HookCount": len(chain),
            "Hooks": chain,
            "LedgerIndex": result.get("ledger_index"),
            "LedgerHash": result.get("ledger_hash"),
            "Validated": result.get("validated") is True,
            **metadata,
        })
    except Exception as exc:
        json_out({
            "Error": exc.__class__.__name__,
            "Message": str(exc),
            "Account": address,
            "Network": network,
        })


def tool_hooks_bitmask(*tokens: str):
    if not tokens:
        usage_out(
            "hooks-bitmask",
            "hooks-bitmask TXTYPE [TXTYPE ...] (names such as Payment/ttPAYMENT/Invoke or ASCII numeric IDs)",
        )
        return
    try:
        resolved = [_normalize_tt(token) for token in tokens]
        ids = [tt for _, tt in resolved]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate transaction types are not allowed")
        mask = compute_hookon(ids)
    except ValueError as exc:
        json_out({"Error": "InvalidTransactionType", "Message": str(exc)})
        return
    json_out({
        "TriggersOn": [{"type": name, "tt": tt} for name, tt in resolved],
        "FiresOnSetHook": _TT_HOOK_SET in ids,
        # HookOn is a Hash256 field: exactly 64 hex characters, no 0x prefix.
        "HookOn": f"{mask:064X}",
        "Semantics": (
            "HookOn is active-low (0 = fire) except bit 22 (ttHOOK_SET), which is active-high. "
            "The value is exactly 64 hexadecimal characters for a SetHook Hook object."
        ),
        "Source": "https://xahau.network/docs/hooks/concepts/hookon-field",
        "ProtocolSource": (
            "https://github.com/Xahau/xahaud/blob/"
            "bb244ef7729503a0317bcff0f8fdaa93ca5cb7d2/include/xrpl/protocol/detail/transactions.macro"
        ),
        "ReviewedAt": "2026-07-25",
    })


COMMANDS = {
    "hooks-info": lambda: tool_hooks_info(
        sys.argv[2], sys.argv[3] if len(sys.argv) >= 4 else "mainnet"
    ) if len(sys.argv) >= 3 else usage_out("hooks-info", "hooks-info rADDRESS [mainnet|testnet]"),
    "hooks-bitmask": lambda: tool_hooks_bitmask(*sys.argv[2:]),
}
