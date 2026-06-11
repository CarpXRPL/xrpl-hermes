#!/usr/bin/env python3
"""Token intelligence: read-only issued-token report built from live public ledger data.

Gathers issuer account state, recent issuer transactions, a trustline/holder
sample, the DEX order book against XRP, and AMM pool state. Every datapoint is
fetched live; anything that cannot be fetched is reported in missing_data —
nothing is invented.
"""
from decimal import Decimal, InvalidOperation
from ._shared import (
    _request, json_out, usage_out, normalize_currency_code, drops_to_xrp,
    AccountInfo, AccountLines, AccountTx, BookOffers,
    XRPCurrency, IssuedCurrency,
)

_ISSUER_FLAG_BITS = {
    0x00800000: "lsfDefaultRipple",
    0x01000000: "lsfDepositAuth",
    0x00100000: "lsfDisableMaster",
    0x00080000: "lsfDisallowXRP",
    0x00400000: "lsfGlobalFreeze",
    0x00200000: "lsfNoFreeze",
    0x00040000: "lsfRequireAuth",
    0x00020000: "lsfRequireDestTag",
    0x80000000: "lsfAllowTrustLineClawback",
}


def _decode_domain(domain_hex: str):
    if not domain_hex:
        return None
    try:
        return bytes.fromhex(domain_hex).decode()
    except Exception:
        return domain_hex


def _fetch_issuer_account(issuer: str) -> dict:
    resp = _request(AccountInfo(account=issuer, ledger_index="validated"))
    if not resp.is_successful():
        raise RuntimeError(resp.result.get("error_message") or resp.result.get("error") or "account_info failed")
    data = resp.result.get("account_data", {})
    flags = data.get("Flags", 0)
    flag_names = [name for bit, name in _ISSUER_FLAG_BITS.items() if flags & bit]
    rate = data.get("TransferRate")
    transfer_fee_percent = round((rate - 1_000_000_000) / 10_000_000, 4) if rate else 0.0
    return {
        "balance_xrp": str(drops_to_xrp(str(data.get("Balance", 0)))),
        "owner_count": data.get("OwnerCount", 0),
        "sequence": data.get("Sequence", 0),
        "domain": _decode_domain(data.get("Domain", "")),
        "flags": flags,
        "flag_names": flag_names,
        "transfer_rate": rate,
        "transfer_fee_percent": transfer_fee_percent,
        "tick_size": data.get("TickSize"),
        "regular_key_set": "RegularKey" in data,
    }


def _fetch_issuer_transactions(issuer: str, limit: int) -> dict:
    resp = _request(AccountTx(account=issuer, limit=int(limit),
                              ledger_index_min=-1, ledger_index_max=-1))
    if not resp.is_successful():
        raise RuntimeError(resp.result.get("error_message") or resp.result.get("error") or "account_tx failed")
    txs = resp.result.get("transactions", [])
    summary = [{
        "hash": t.get("hash") or (t.get("tx") or t.get("tx_json") or {}).get("hash"),
        "type": (t.get("tx") or t.get("tx_json") or {}).get("TransactionType"),
        "result": t.get("meta", {}).get("TransactionResult"),
        "ledger_index": t.get("ledger_index"),
    } for t in txs]
    return {"sampled": len(summary), "transactions": summary}


def _fetch_trustline_sample(issuer: str, currency_hex: str, limit: int) -> dict:
    resp = _request(AccountLines(account=issuer, ledger_index="validated",
                                 limit=min(int(limit), 400)))
    if not resp.is_successful():
        raise RuntimeError(resp.result.get("error_message") or resp.result.get("error") or "account_lines failed")
    lines = resp.result.get("lines", [])
    matching = [l for l in lines if l.get("currency", "").upper() == currency_hex.upper()]
    outstanding = Decimal(0)
    holders_with_balance = 0
    for l in matching:
        try:
            bal = Decimal(l.get("balance", "0"))
        except InvalidOperation:
            continue
        # From the issuer's perspective a negative balance means tokens issued.
        if bal < 0:
            outstanding += -bal
            holders_with_balance += 1
    return {
        "lines_sampled": len(lines),
        "matching_currency_lines": len(matching),
        "holders_with_balance_in_sample": holders_with_balance,
        "outstanding_in_sample": str(outstanding),
        "sample_complete": "marker" not in resp.result,
        "frozen_lines_in_sample": sum(1 for l in matching if l.get("freeze") or l.get("freeze_peer")),
    }


def _book_side(taker_gets, taker_pays) -> dict:
    resp = _request(BookOffers(taker_gets=taker_gets, taker_pays=taker_pays,
                               limit=10, ledger_index="validated"))
    if not resp.is_successful():
        raise RuntimeError(resp.result.get("error_message") or resp.result.get("error") or "book_offers failed")
    offers = resp.result.get("offers", [])
    return {"offer_count": len(offers), "top_offer": offers[0] if offers else None}


def _fetch_orderbook_vs_xrp(token: IssuedCurrency) -> dict:
    xrp = XRPCurrency()
    sell_side = _book_side(token, xrp)   # offers selling the token for XRP
    buy_side = _book_side(xrp, token)    # offers buying the token with XRP
    return {
        "sell_offers": sell_side["offer_count"],
        "buy_offers": buy_side["offer_count"],
        "top_sell_offer": sell_side["top_offer"],
        "top_buy_offer": buy_side["top_offer"],
    }


def _fetch_amm_vs_xrp(token: IssuedCurrency) -> dict:
    from xrpl.models.requests import AMMInfo
    resp = _request(AMMInfo(asset=token, asset2=XRPCurrency()))
    result = resp.result
    amm = result.get("amm")
    if not resp.is_successful() or not amm:
        if result.get("error") == "actNotFound":
            return {"amm_exists": False}
        raise RuntimeError(result.get("error_message") or result.get("error") or "amm_info failed")
    return {
        "amm_exists": True,
        "account": amm.get("account"),
        "amount": amm.get("amount"),
        "amount2": amm.get("amount2"),
        "trading_fee": amm.get("trading_fee"),
    }


def _derive_risk_flags(datapoints: dict) -> list:
    flags = []
    issuer = datapoints.get("issuer_account")
    if issuer:
        names = issuer["flag_names"]
        if "lsfGlobalFreeze" in names:
            flags.append("global-freeze: issuer has GlobalFreeze set — all trustline transfers are frozen")
        if "lsfDisableMaster" not in names:
            flags.append("master-key-active: issuer master key is not disabled — weaker issuer key hygiene")
        if "lsfAllowTrustLineClawback" in names:
            flags.append("clawback-enabled: issuer can claw back holder balances")
        if "lsfDefaultRipple" not in names:
            flags.append("default-ripple-off: token may not ripple between holders (unusual for an issuer)")
        if "lsfRequireAuth" in names:
            flags.append("require-auth: issuer must authorize each trustline (common for regulated tokens)")
        if "lsfNoFreeze" not in names and "lsfGlobalFreeze" not in names:
            flags.append("freeze-possible: issuer has not set NoFreeze and can freeze individual trustlines")
        if issuer["transfer_fee_percent"]:
            flags.append(f"transfer-fee: {issuer['transfer_fee_percent']}% fee on holder-to-holder transfers")
        if not issuer["domain"]:
            flags.append("no-domain: issuer has no on-ledger domain (no xrp-ledger.toml verification possible)")
    book = datapoints.get("dex_orderbook_vs_xrp")
    amm = datapoints.get("amm_pool_vs_xrp")
    if book and amm and book["sell_offers"] == 0 and book["buy_offers"] == 0 and not amm.get("amm_exists"):
        flags.append("no-xrp-liquidity: no DEX offers and no AMM pool against XRP found")
    trust = datapoints.get("trustline_sample")
    if trust and trust["frozen_lines_in_sample"]:
        flags.append(f"frozen-lines: {trust['frozen_lines_in_sample']} frozen trustline(s) in sample")
    return flags


def _summarize(currency: str, issuer: str, datapoints: dict, risk_flags: list, missing: list) -> str:
    parts = []
    acct = datapoints.get("issuer_account")
    if acct:
        domain = f"domain {acct['domain']}" if acct["domain"] else "no domain set"
        parts.append(f"{currency} is issued by {issuer} ({domain}).")
        if acct["transfer_fee_percent"]:
            parts.append(f"Transfers between holders pay a {acct['transfer_fee_percent']}% fee.")
    trust = datapoints.get("trustline_sample")
    if trust:
        scope = "all" if trust["sample_complete"] else f"a sample of {trust['lines_sampled']}"
        parts.append(f"Across {scope} issuer trustlines, {trust['holders_with_balance_in_sample']} "
                     f"hold a balance ({trust['outstanding_in_sample']} {currency} outstanding in sample).")
    book = datapoints.get("dex_orderbook_vs_xrp")
    if book:
        parts.append(f"DEX book vs XRP: {book['sell_offers']} sell / {book['buy_offers']} buy offers (top 10 each side).")
    amm = datapoints.get("amm_pool_vs_xrp")
    if amm:
        parts.append("An XRP AMM pool exists." if amm.get("amm_exists") else "No XRP AMM pool exists.")
    txs = datapoints.get("issuer_recent_transactions")
    if txs:
        parts.append(f"Issuer shows {txs['sampled']} recent transaction(s) sampled.")
    parts.append(f"{len(risk_flags)} risk signal(s) flagged." if risk_flags else "No risk signals flagged.")
    if missing:
        parts.append(f"{len(missing)} datapoint(s) could not be fetched — see missing_data.")
    return " ".join(parts)


def build_token_intel_report(currency: str, issuer: str,
                             tx_limit: int = 10, trustline_limit: int = 200) -> dict:
    report = {
        "input": {"currency": currency, "issuer": issuer,
                  "tx_limit": int(tx_limit), "trustline_limit": int(trustline_limit)},
        "normalized_currency": None,
        "sources": [],
        "datapoints": {},
        "risk_flags": [],
        "confidence": "none",
        "missing_data": [],
        "plain_english_summary": "",
    }
    try:
        norm = normalize_currency_code(currency)
    except ValueError as e:
        report["missing_data"].append({"datapoint": "normalized_currency", "reason": str(e)})
        report["plain_english_summary"] = f"Could not normalize currency '{currency}': {e}"
        return report
    if norm == "XRP":
        report["missing_data"].append({"datapoint": "all", "reason": "XRP is the native asset; token-intel covers issued tokens"})
        report["plain_english_summary"] = "XRP is the native asset and has no issuer — token-intel covers issued tokens."
        return report
    report["normalized_currency"] = norm
    token = IssuedCurrency(currency=norm, issuer=issuer)

    gatherers = [
        ("issuer_account", "account_info", lambda: _fetch_issuer_account(issuer)),
        ("issuer_recent_transactions", "account_tx", lambda: _fetch_issuer_transactions(issuer, tx_limit)),
        ("trustline_sample", "account_lines", lambda: _fetch_trustline_sample(issuer, norm, trustline_limit)),
        ("dex_orderbook_vs_xrp", "book_offers", lambda: _fetch_orderbook_vs_xrp(token)),
        ("amm_pool_vs_xrp", "amm_info", lambda: _fetch_amm_vs_xrp(token)),
    ]
    for key, method, fn in gatherers:
        try:
            report["datapoints"][key] = fn()
            report["sources"].append({"datapoint": key, "method": method, "network": "XRPL mainnet (public JSON-RPC)"})
        except Exception as e:
            report["missing_data"].append({"datapoint": key, "reason": str(e)})

    report["risk_flags"] = _derive_risk_flags(report["datapoints"])
    fetched = len(report["datapoints"])
    report["confidence"] = "high" if fetched >= 5 else "medium" if fetched >= 3 else "low" if fetched >= 1 else "none"
    report["plain_english_summary"] = _summarize(
        currency, issuer, report["datapoints"], report["risk_flags"], report["missing_data"])
    return report


def tool_token_intel(currency: str, issuer: str, tx_limit: int = 10, trustline_limit: int = 200):
    json_out(build_token_intel_report(currency, issuer, tx_limit, trustline_limit))


def _cli_token_intel():
    import sys
    argv = sys.argv
    if len(argv) < 4:
        usage_out("token-intel", "token-intel CURRENCY rISSUER [TX_LIMIT] [TRUSTLINE_LIMIT]")
        return
    tx_limit = int(argv[4]) if len(argv) >= 5 else 10
    trustline_limit = int(argv[5]) if len(argv) >= 6 else 200
    tool_token_intel(argv[2], argv[3], tx_limit, trustline_limit)


COMMANDS = {
    "token-intel": _cli_token_intel,
}
