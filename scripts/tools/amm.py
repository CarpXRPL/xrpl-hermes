#!/usr/bin/env python3
"""AMM tools: live pool lookup, pool creation, deposits, withdrawals, fee voting, auction bidding."""
from ._shared import (
    json_out, note_out, json_tx_out, usage_out, IssuedCurrencyAmount,
    _parse_asset, _parse_amount_for_amm, _dispatch_build, _request,
    parse_asset_normalized,
    AMMCreate, AMMDeposit, AMMWithdraw, AMMVote, AMMBid,
)

def tool_amm_info(asset1: str, asset2: str):
    from xrpl.models.requests import AMMInfo
    try:
        a1 = parse_asset_normalized(asset1)
        a2 = parse_asset_normalized(asset2)
    except ValueError as e:
        json_out({"Error": "InvalidAsset", "Message": str(e)})
        return
    try:
        resp = _request(AMMInfo(asset=a1, asset2=a2))
    except Exception as e:
        json_out({"Error": "AMMInfoError", "Message": str(e), "Asset1": asset1, "Asset2": asset2})
        return
    result = resp.result
    amm = result.get("amm")
    if not resp.is_successful() or not amm:
        json_out({
            "Asset1": asset1, "Asset2": asset2, "AMMExists": False,
            "Error": result.get("error"),
            "Message": result.get("error_message") or "No AMM pool found for this pair",
        })
        return
    json_out({
        "Asset1": asset1, "Asset2": asset2, "AMMExists": True,
        "Account": amm.get("account"),
        "Amount": amm.get("amount"),
        "Amount2": amm.get("amount2"),
        "TradingFee": amm.get("trading_fee"),
        "LPToken": amm.get("lp_token"),
        "VoteSlots": len(amm.get("vote_slots", [])),
        "AuctionSlot": amm.get("auction_slot"),
        "LedgerIndex": result.get("ledger_index") or result.get("ledger_current_index"),
    })

def _cli_amm_info():
    import sys
    if len(sys.argv) < 4:
        usage_out("amm-info", "amm-info ASSET1 ASSET2  (e.g. amm-info XRP USD:rISSUER)")
        return
    tool_amm_info(sys.argv[2], sys.argv[3])

def tool_build_amm_create(frm: str, amount1: str, amount2: str, fee: int = 600):
    amt1 = _parse_amount_for_amm(amount1)
    amt2 = _parse_amount_for_amm(amount2)
    tx = AMMCreate(account=frm, amount=amt1, amount2=amt2, trading_fee=fee)
    note_out("# AMMCreate TX JSON - signer-ready JSON")
    json_tx_out(tx)

def tool_build_amm_deposit(frm: str, asset1: str, asset2: str,
                            amount1: str = None, amount2: str = None,
                            lp_token_out: str = None, mode: str = "two-asset",
                            amount: str = None):
    _FLAGS = {"two-asset": 0x00100000, "single-asset": 0x00080000, "lp-token": 0x00010000}
    flags = _FLAGS.get(mode, 0x00100000)
    kwargs = dict(account=frm, asset=_parse_asset(asset1), asset2=_parse_asset(asset2), flags=flags)
    if amount and not amount1: amount1 = amount
    if amount1: kwargs["amount"] = _parse_amount_for_amm(amount1)
    if amount2: kwargs["amount2"] = _parse_amount_for_amm(amount2)
    if lp_token_out:
        parts = lp_token_out.split(":", 2)
        if len(parts) == 3:
            kwargs["lp_token_out"] = IssuedCurrencyAmount(currency=parts[0], issuer=parts[1], value=parts[2])
    tx = AMMDeposit(**kwargs)
    note_out("# AMMDeposit TX JSON - signer-ready JSON")
    json_tx_out(tx)

def tool_build_amm_withdraw(frm: str, asset1: str, asset2: str,
                             amount1: str = None, amount2: str = None,
                             lp_token_in: str = None, mode: str = "two-asset",
                             lp_amount: str = None):
    _FLAGS = {"two-asset": 0x00100000, "single-asset": 0x00080000,
              "lp-token": 0x00010000, "withdraw-all": 0x00020000}
    flags = _FLAGS.get(mode, 0x00100000)
    kwargs = dict(account=frm, asset=_parse_asset(asset1), asset2=_parse_asset(asset2), flags=flags)
    if lp_amount and not lp_token_in: lp_token_in = lp_amount
    if amount1: kwargs["amount"] = _parse_amount_for_amm(amount1)
    if amount2: kwargs["amount2"] = _parse_amount_for_amm(amount2)
    if lp_token_in:
        parts = lp_token_in.split(":", 2)
        if len(parts) == 3:
            kwargs["lp_token_in"] = IssuedCurrencyAmount(currency=parts[0], issuer=parts[1], value=parts[2])
    tx = AMMWithdraw(**kwargs)
    note_out("# AMMWithdraw TX JSON - signer-ready JSON")
    json_tx_out(tx)

def tool_build_amm_vote(frm: str, asset1: str, asset2: str, trading_fee: str):
    tx = AMMVote(account=frm, asset=_parse_asset(asset1), asset2=_parse_asset(asset2),
                 trading_fee=int(trading_fee))
    note_out("# AMMVote TX JSON - signer-ready JSON")
    json_tx_out(tx)

def tool_build_amm_bid(frm: str, asset1: str, asset2: str,
                        bid_min: str = None, bid_max: str = None,
                        auth_accounts: str = None):
    kwargs = dict(account=frm, asset=_parse_asset(asset1), asset2=_parse_asset(asset2))
    if bid_min:
        parts = bid_min.split(":", 2)
        if len(parts) == 3:
            kwargs["bid_min"] = IssuedCurrencyAmount(currency=parts[0], issuer=parts[1], value=parts[2])
    if bid_max:
        parts = bid_max.split(":", 2)
        if len(parts) == 3:
            kwargs["bid_max"] = IssuedCurrencyAmount(currency=parts[0], issuer=parts[1], value=parts[2])
    if auth_accounts:
        kwargs["auth_accounts"] = [{"account": a.strip()} for a in auth_accounts.split(",") if a.strip()]
    tx = AMMBid(**kwargs)
    note_out("# AMMBid TX JSON - signer-ready JSON")
    json_tx_out(tx)

COMMANDS = {
    "amm-info": _cli_amm_info,
    "build-amm-create": lambda: _dispatch_build(3, tool_build_amm_create),
    "build-amm-deposit": lambda: _dispatch_build(3, tool_build_amm_deposit),
    "build-amm-withdraw": lambda: _dispatch_build(3, tool_build_amm_withdraw),
    "build-amm-vote": lambda: _dispatch_build(4, tool_build_amm_vote),
    "build-amm-bid": lambda: _dispatch_build(3, tool_build_amm_bid),
}
