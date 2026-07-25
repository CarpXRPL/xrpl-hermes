#!/usr/bin/env python3
"""AMM tools: live pool lookup, pool creation, deposits, withdrawals, fee voting, auction bidding."""
from decimal import Decimal
from typing import cast
from ._shared import (
    json_out, note_out, json_tx_out, usage_out, XRPCurrency, IssuedCurrency,
    IssuedCurrencyAmount,
    _parse_amount_for_amm, _dispatch_build, _request,
    parse_asset_normalized, parse_amount_arg, validate_positive_amount,
    validate_xrpl_address,
    AuthAccount, AMMCreate, AMMDeposit, AMMWithdraw, AMMVote, AMMBid,
)

_ASSET_USAGE = "assets are 'XRP' or 'CUR:ISSUER'; amounts are integer drops or CUR:ISSUER:VALUE"

def _amount_issue(amount):
    if isinstance(amount, str):
        return ("XRP",)
    return ("ISSUED", amount.currency, amount.issuer)

def _asset_issue(asset):
    if isinstance(asset, XRPCurrency):
        return ("XRP",)
    return ("ISSUED", asset.currency, asset.issuer)

def _validate_liquidity_amounts(amount1, amount2, asset, asset2, mode):
    """Validate amount issues against the pool as a set, as rippled does."""
    pool_issues = {_asset_issue(asset), _asset_issue(asset2)}
    if mode == "two-asset":
        amount_issues = {_amount_issue(amount1), _amount_issue(amount2)}
        if len(amount_issues) != 2 or amount_issues != pool_issues:
            raise ValueError("amount1 and amount2 must collectively match the two AMM assets")
    elif mode == "single-asset" and _amount_issue(amount1) not in pool_issues:
        raise ValueError("amount1 must match either AMM asset")

def _validate_amm_asset_pair(asset, asset2):
    if _asset_issue(asset) == _asset_issue(asset2):
        raise ValueError("asset1 and asset2 must be different AMM assets")
    for value in (asset, asset2):
        if (isinstance(value, IssuedCurrency) and len(value.currency) == 40
                and value.currency.startswith("03")):
            raise ValueError("AMM LP tokens cannot be used as pool assets")

def _lp_token_amount(arg: str, field: str):
    """LP tokens are always an issued amount, never drops.

    A malformed --bid-min used to be dropped silently, turning a bounded auction
    bid into an unbounded one.
    """
    amount = parse_amount_arg(arg)
    if not isinstance(amount, IssuedCurrencyAmount):
        raise ValueError(f"{field} must be an LP token amount 'CUR:ISSUER:VALUE' (got '{arg}')")
    validate_positive_amount(amount, field)
    currency = amount.currency
    if (len(currency) != 40 or not currency.startswith("03")
            or any(c not in "0123456789ABCDEF" for c in currency)):
        raise ValueError(
            f"{field} must use the AMM LP-token 40-hex currency beginning with 03"
        )
    return amount

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
    try:
        amt1 = validate_positive_amount(_parse_amount_for_amm(amount1), "amount1")
        amt2 = validate_positive_amount(_parse_amount_for_amm(amount2), "amount2")
        if _amount_issue(amt1) == _amount_issue(amt2):
            raise ValueError("amount1 and amount2 must be different AMM assets")
        for value in (amt1, amt2):
            if (isinstance(value, IssuedCurrencyAmount) and len(value.currency) == 40
                    and value.currency.startswith("03")):
                raise ValueError("AMM LP tokens cannot be used to create a pool")
        fee_value = int(fee)
        if not 0 <= fee_value <= 1000:
            raise ValueError("trading fee must be an integer from 0 through 1000")
    except (ValueError, TypeError) as exc:
        usage_out("build-amm-create", f"build-amm-create --from rSRC --amount1 A --amount2 B: {exc}")
        return
    tx = AMMCreate(account=frm, amount=amt1, amount2=amt2, trading_fee=fee_value)
    note_out("# AMMCreate TX JSON - signer-ready JSON")
    json_tx_out(tx)

def tool_build_amm_deposit(frm: str, asset1: str, asset2: str,
                            amount1: str = None, amount2: str = None,
                            lp_token_out: str = None, mode: str = "two-asset",
                            amount: str = None):
    flags_by_mode = {
        "two-asset": 0x00100000,
        "single-asset": 0x00080000,
        "lp-token": 0x00010000,
    }
    try:
        if mode not in flags_by_mode:
            raise ValueError(f"unknown mode '{mode}'; use two-asset, single-asset, or lp-token")
        if amount is not None:
            if amount1 is not None:
                raise ValueError("use only one of --amount and --amount1")
            amount1 = amount
        if mode == "two-asset":
            if amount1 is None or amount2 is None or lp_token_out is not None:
                raise ValueError("two-asset mode requires --amount1 and --amount2 only")
        elif mode == "single-asset":
            if amount1 is None or amount2 is not None or lp_token_out is not None:
                raise ValueError("single-asset mode requires --amount1 only")
        elif amount1 is not None or amount2 is not None or lp_token_out is None:
            raise ValueError("lp-token mode requires --lp-token-out only")

        asset = parse_asset_normalized(asset1)
        asset2_obj = parse_asset_normalized(asset2)
        _validate_amm_asset_pair(asset, asset2_obj)
        kwargs = dict(
            account=frm, asset=asset, asset2=asset2_obj,
            flags=flags_by_mode[mode],
        )
        parsed1 = (validate_positive_amount(_parse_amount_for_amm(amount1), "amount1")
                   if amount1 is not None else None)
        parsed2 = (validate_positive_amount(_parse_amount_for_amm(amount2), "amount2")
                   if amount2 is not None else None)
        if mode in ("two-asset", "single-asset"):
            _validate_liquidity_amounts(parsed1, parsed2, asset, asset2_obj, mode)
        if parsed1 is not None:
            kwargs["amount"] = parsed1
        if parsed2 is not None:
            kwargs["amount2"] = parsed2
        if lp_token_out is not None:
            kwargs["lp_token_out"] = _lp_token_amount(lp_token_out, "--lp-token-out")
    except (ValueError, TypeError) as exc:
        usage_out("build-amm-deposit", f"build-amm-deposit: {_ASSET_USAGE}. {exc}")
        return
    tx = AMMDeposit(**kwargs)
    if mode == "lp-token":
        note_out(
            "# Verify LPTokenOut exactly matches the LPToken from amm-info for this pool; "
            "offline shape validation cannot prove that link."
        )
    note_out("# AMMDeposit TX JSON - signer-ready JSON")
    json_tx_out(tx)

def tool_build_amm_withdraw(frm: str, asset1: str, asset2: str,
                             amount1: str = None, amount2: str = None,
                             lp_token_in: str = None, mode: str = "two-asset",
                             lp_amount: str = None):
    flags_by_mode = {
        "two-asset": 0x00100000,
        "single-asset": 0x00080000,
        "lp-token": 0x00010000,
        "withdraw-all": 0x00020000,
    }
    try:
        if mode not in flags_by_mode:
            raise ValueError(
                f"unknown mode '{mode}'; use two-asset, single-asset, lp-token, or withdraw-all"
            )
        if lp_amount is not None:
            if lp_token_in is not None:
                raise ValueError("use only one of --lp-amount and --lp-token-in")
            lp_token_in = lp_amount
        if mode == "two-asset":
            if amount1 is None or amount2 is None or lp_token_in is not None:
                raise ValueError("two-asset mode requires --amount1 and --amount2 only")
        elif mode == "single-asset":
            if amount1 is None or amount2 is not None or lp_token_in is not None:
                raise ValueError("single-asset mode requires --amount1 only")
        elif mode == "lp-token":
            if amount1 is not None or amount2 is not None or lp_token_in is None:
                raise ValueError("lp-token mode requires --lp-token-in only")
        elif amount1 is not None or amount2 is not None or lp_token_in is not None:
            raise ValueError("withdraw-all mode does not accept amount fields")

        asset = parse_asset_normalized(asset1)
        asset2_obj = parse_asset_normalized(asset2)
        _validate_amm_asset_pair(asset, asset2_obj)
        kwargs = dict(
            account=frm, asset=asset, asset2=asset2_obj,
            flags=flags_by_mode[mode],
        )
        parsed1 = (validate_positive_amount(_parse_amount_for_amm(amount1), "amount1")
                   if amount1 is not None else None)
        parsed2 = (validate_positive_amount(_parse_amount_for_amm(amount2), "amount2")
                   if amount2 is not None else None)
        if mode in ("two-asset", "single-asset"):
            _validate_liquidity_amounts(parsed1, parsed2, asset, asset2_obj, mode)
        if parsed1 is not None:
            kwargs["amount"] = parsed1
        if parsed2 is not None:
            kwargs["amount2"] = parsed2
        if lp_token_in is not None:
            kwargs["lp_token_in"] = _lp_token_amount(lp_token_in, "--lp-token-in")
    except (ValueError, TypeError) as exc:
        usage_out("build-amm-withdraw", f"build-amm-withdraw: {_ASSET_USAGE}. {exc}")
        return
    tx = AMMWithdraw(**kwargs)
    if mode == "lp-token":
        note_out(
            "# Verify LPTokenIn exactly matches the LPToken from amm-info for this pool; "
            "offline shape validation cannot prove that link."
        )
    note_out("# AMMWithdraw TX JSON - signer-ready JSON")
    json_tx_out(tx)

def tool_build_amm_vote(frm: str, asset1: str, asset2: str, trading_fee: str):
    try:
        asset = parse_asset_normalized(asset1)
        asset2_obj = parse_asset_normalized(asset2)
        _validate_amm_asset_pair(asset, asset2_obj)
        fee_value = int(trading_fee)
        if not 0 <= fee_value <= 1000:
            raise ValueError("trading fee must be an integer from 0 through 1000")
    except (ValueError, TypeError) as exc:
        usage_out("build-amm-vote", f"build-amm-vote: {_ASSET_USAGE}. {exc}")
        return
    tx = AMMVote(account=frm, asset=asset, asset2=asset2_obj, trading_fee=fee_value)
    note_out("# AMMVote TX JSON - signer-ready JSON")
    json_tx_out(tx)

def tool_build_amm_bid(frm: str, asset1: str, asset2: str,
                        bid_min: str = None, bid_max: str = None,
                        auth_accounts: str = None):
    try:
        sender = validate_xrpl_address(frm, "source account")
        asset = parse_asset_normalized(asset1)
        asset2_obj = parse_asset_normalized(asset2)
        _validate_amm_asset_pair(asset, asset2_obj)
        kwargs = dict(account=sender, asset=asset, asset2=asset2_obj)
        if bid_min:
            kwargs["bid_min"] = _lp_token_amount(bid_min, "--bid-min")
        if bid_max:
            kwargs["bid_max"] = _lp_token_amount(bid_max, "--bid-max")
        if bid_min and bid_max:
            lower = cast(IssuedCurrencyAmount, kwargs["bid_min"])
            upper = cast(IssuedCurrencyAmount, kwargs["bid_max"])
            if lower.currency != upper.currency or lower.issuer != upper.issuer:
                raise ValueError("--bid-min and --bid-max must use the same LP token")
            if Decimal(lower.value) > Decimal(upper.value):
                raise ValueError("--bid-min cannot exceed --bid-max")
        if auth_accounts is not None:
            accounts = [a.strip() for a in auth_accounts.split(",") if a.strip()]
            if not accounts:
                raise ValueError("--auth-accounts was supplied but contained no accounts")
            if len(accounts) > 4:
                raise ValueError("--auth-accounts permits at most 4 additional accounts")
            validated = [validate_xrpl_address(a, "auth account") for a in accounts]
            if sender in validated:
                raise ValueError("--auth-accounts cannot include the transaction sender")
            if len(set(validated)) != len(validated):
                raise ValueError("--auth-accounts cannot contain duplicates")
            kwargs["auth_accounts"] = [AuthAccount(account=a) for a in validated]
    except ValueError as exc:
        usage_out("build-amm-bid",
                  "build-amm-bid --from rSRC --asset1 A --asset2 B "
                  "[--bid-min CUR:ISSUER:VALUE] [--bid-max CUR:ISSUER:VALUE] "
                  f"[--auth-accounts rA,rB]. {exc}")
        return
    tx = AMMBid(**kwargs)
    if bid_min or bid_max:
        note_out(
            "# Verify BidMin/BidMax currency and issuer exactly match the LPToken from "
            "amm-info for this Asset/Asset2 pair; offline shape validation cannot prove that link."
        )
    note_out("# AMMBid unsigned transaction candidate - review before wallet signing")
    json_tx_out(tx)

COMMANDS = {
    "amm-info": _cli_amm_info,
    "build-amm-create": lambda: _dispatch_build(3, tool_build_amm_create),
    "build-amm-deposit": lambda: _dispatch_build(3, tool_build_amm_deposit),
    "build-amm-withdraw": lambda: _dispatch_build(3, tool_build_amm_withdraw),
    "build-amm-vote": lambda: _dispatch_build(4, tool_build_amm_vote),
    "build-amm-bid": lambda: _dispatch_build(3, tool_build_amm_bid),
}
