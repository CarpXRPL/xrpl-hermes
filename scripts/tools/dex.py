#!/usr/bin/env python3
"""DEX tools: orderbook queries, offer creation."""
from ._shared import (
    json_out, note_out, json_tx_out, parse_amount_arg, ENDPOINTS,
    _dispatch_build, OfferCreate,
)

def tool_book_offers(taker_gets: str, taker_pays: str):
    import httpx, json
    def parse_book_side(arg: str):
        parts = arg.split(":", 1)
        return (parts[0], parts[1] if len(parts) == 2 else None)
    gets_cur, gets_iss = parse_book_side(taker_gets)
    pays_cur, pays_iss = parse_book_side(taker_pays)
    if gets_cur.upper() == "XRP":
        gets_param = {"currency": "XRP"}
    else:
        gets_param = {"currency": gets_cur}
        if gets_iss: gets_param["issuer"] = gets_iss
    if pays_cur.upper() == "XRP":
        pays_param = {"currency": "XRP"}
    else:
        pays_param = {"currency": pays_cur}
        if pays_iss: pays_param["issuer"] = pays_iss
    payload = {"method": "book_offers", "params": [{
        "taker_gets": gets_param, "taker_pays": pays_param,
        "limit": 10, "ledger_index": "current",
    }]}
    data = {}
    for ep in ENDPOINTS:
        try:
            resp = httpx.post(ep, json=payload, timeout=10)
            data = resp.json()
            if "result" in data: break
        except Exception:
            continue
    offers = data.get("result", {}).get("offers", [])
    json_out({"TakerGets": taker_gets, "TakerPays": taker_pays,
              "OfferCount": len(offers), "Offers": offers[:10],
              "Raw": data.get("result", data)})

def tool_build_offer(frm: str, taker_gets: str = None, taker_pays: str = None,
                     sell: str = None, buy: str = None):
    taker_gets = taker_gets or sell
    taker_pays = taker_pays or buy
    if not taker_gets or not taker_pays:
        print("Usage: build-offer --from rADDR --sell XRP:AMOUNT --buy CUR:ISS:AMOUNT")
        return
    gets = parse_amount_arg(taker_gets)
    pays = parse_amount_arg(taker_pays)
    tx = OfferCreate(account=frm, taker_gets=gets, taker_pays=pays)
    note_out("# OfferCreate TX JSON - signer-ready JSON")
    json_tx_out(tx)

COMMANDS = {
    "book-offers": lambda: tool_book_offers(__import__('sys').argv[2], __import__('sys').argv[3]) if len(__import__('sys').argv) >= 4 else print("Usage: book-offers TAKER_GETS TAKER_PAYS"),
    "build-offer": lambda: _dispatch_build(3, tool_build_offer),
}
