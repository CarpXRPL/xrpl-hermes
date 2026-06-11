#!/usr/bin/env python3
"""Xahau Hooks tools: live hook inspection and HookOn bitmask calculation."""
from ._shared import (
    json_out, usage_out,
)
import httpx, sys

# Xahau transaction-type IDs for HookOn bit positions.
# Source: Xahau HookOn docs (xahau.network/docs/hooks/concepts/hookon-field)
# and the linked HookOn calculator. Bits are active-low (0 = hook fires),
# except ttHOOK_SET (22), which is active-high (1 = hook fires on SetHook).
HOOKON_TT = {
    "Payment": 0,
    "EscrowCreate": 1,
    "EscrowFinish": 2,
    "AccountSet": 3,
    "EscrowCancel": 4,
    "SetRegularKey": 5,
    "OfferCreate": 7,
    "OfferCancel": 8,
    "TicketCreate": 10,
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
    "Clawback": 30,
    "URITokenMint": 45,
    "URITokenBurn": 46,
    "URITokenBuy": 47,
    "URITokenCreateSellOffer": 48,
    "URITokenCancelSellOffer": 49,
    "Cron": 92,
    "CronSet": 93,
    "SetRemarks": 94,
    "Remit": 95,
    "Import": 97,
    "ClaimReward": 98,
    "Invoke": 99,
}

_TT_HOOK_SET = 22
_ALL_ONES_256 = (1 << 256) - 1

# Accept ttPAYMENT / PAYCHAN_CREATE / payment etc. alongside canonical names.
_TT_ALIASES = {
    "REGULAR_KEY_SET": "SetRegularKey",
    "HOOK_SET": "SetHook",
    "REMARKS_SET": "SetRemarks",
    "PAYCHAN_CREATE": "PaymentChannelCreate",
    "PAYCHAN_FUND": "PaymentChannelFund",
    "PAYCHAN_CLAIM": "PaymentChannelClaim",
}


def _normalize_tt(token: str):
    """Resolve a transaction-type name or numeric ID to (canonical_name, tt_id)."""
    raw = token.strip()
    if raw.isdigit():
        tt = int(raw)
        for name, num in HOOKON_TT.items():
            if num == tt:
                return name, num
        if 0 <= tt < 256:
            return f"tt{tt}", tt
        raise ValueError(f"transaction type ID {tt} out of range 0-255")
    cleaned = raw[2:] if raw.startswith("tt") else raw
    cleaned = _TT_ALIASES.get(cleaned.upper().replace("-", "_"), cleaned)
    folded = cleaned.replace("_", "").replace("-", "").lower()
    for name, num in HOOKON_TT.items():
        if name.lower() == folded:
            return name, num
    known = ", ".join(sorted(HOOKON_TT))
    raise ValueError(f"unknown transaction type '{token}'. Known: {known}")


def compute_hookon(tt_ids) -> int:
    """Compute a Xahau HookOn value that fires on exactly the given tt IDs.

    Bits are active-low except bit 22 (ttHOOK_SET), which is active-high, so
    the all-ones baseline must have bit 22 cleared to stay 'fires on nothing'.
    """
    mask = _ALL_ONES_256 & ~(1 << _TT_HOOK_SET)
    for tt in tt_ids:
        if tt == _TT_HOOK_SET:
            mask |= 1 << _TT_HOOK_SET
        else:
            mask &= ~(1 << tt)
    return mask


def tool_hooks_info(address: str):
    payload = {"method": "account_objects", "params": [{"account": address, "ledger_index": "validated", "type": "hook", "limit": 20}]}
    try:
        resp = httpx.post("https://xahau.network", json=payload, timeout=15)
        data = resp.json()
        hooks = data.get("result", {}).get("account_objects", [])
        json_out({"Account": address, "HookCount": len(hooks), "Hooks": hooks, "Raw": data.get("result", data)})
    except Exception as e:
        json_out({"Error": "HooksInfoError", "Message": str(e), "Account": address})


def tool_hooks_bitmask(*tokens: str):
    if not tokens:
        usage_out("hooks-bitmask",
                  "hooks-bitmask TXTYPE [TXTYPE ...]  (e.g. hooks-bitmask Payment URITokenMint, "
                  "names like Payment/ttPAYMENT/Invoke or numeric tt IDs)")
        return
    try:
        resolved = [_normalize_tt(t) for t in tokens]
    except ValueError as e:
        json_out({"Error": "UnknownTransactionType", "Message": str(e)})
        return
    mask = compute_hookon([tt for _, tt in resolved])
    json_out({
        "TriggersOn": [{"type": name, "tt": tt} for name, tt in resolved],
        "FiresOnSetHook": any(tt == _TT_HOOK_SET for _, tt in resolved),
        "HookOn": f"0x{mask:064X}",
        "Semantics": "HookOn bits are active-low (0 = hook fires for that tt), except bit 22 "
                     "(ttHOOK_SET) which is active-high. Put this value in the HookOn field of "
                     "each Hook object in a SetHook transaction on Xahau.",
        "Source": "https://xahau.network/docs/hooks/concepts/hookon-field",
    })


COMMANDS = {
    "hooks-info": lambda: tool_hooks_info(sys.argv[2]) if len(sys.argv) >= 3 else print("Usage: hooks-info rADDRESS"),
    "hooks-bitmask": lambda: tool_hooks_bitmask(*sys.argv[2:]),
}
