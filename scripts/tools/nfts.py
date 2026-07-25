#!/usr/bin/env python3
"""NFT tools: info, offers (sell/buy), mint, create-offer, accept-offer, cancel-offer, burn."""
from ._shared import (
    _request, json_out, note_out, json_tx_out, parse_amount_arg, usage_out, ENDPOINTS,
    IssuedCurrencyAmount, _dispatch_build, NFTInfo, NFTSellOffers, NFTBuyOffers,
    NFTokenMint, NFTokenCreateOffer, NFTokenAcceptOffer, NFTokenCancelOffer, NFTokenBurn,
    JsonRpcClient,
)

def tool_nft_info(nft_id: str):
    last_error = None
    result = {}
    for ep in ENDPOINTS:
        try:
            result = JsonRpcClient(ep).request(NFTInfo(nft_id=nft_id)).result
        except Exception as e:
            last_error = e
            continue
        if result.get("error") == "unknownCmd":
            last_error = result.get("error_message", "Unknown method")
            continue
        break
    else:
        json_out({"Error": "NFTInfoError", "Message": str(last_error), "NFTokenID": nft_id})
        return
    if result.get("error"):
        json_out({"Error": result.get("error"), "Message": result.get("error_message", "no message"),
                  "NFTokenID": nft_id})
        return
    json_out(result)

def tool_nft_offers(nft_id: str, side: str = "sell"):
    req = NFTSellOffers(nft_id=nft_id) if side == "sell" else NFTBuyOffers(nft_id=nft_id)
    try:
        resp = _request(req)
        json_out({"NFTokenID": nft_id, "Side": side,
                  "OfferCount": len(resp.result.get("offers", [])),
                  "Offers": resp.result.get("offers", [])})
    except Exception as e:
        json_out({"Error": "NFTOffersError", "Message": str(e), "NFTokenID": nft_id})

_URI_USAGE = (
    "build-nft-mint --from rSRC --taxon N [--uri TEXT | --uri-hex HEX]. "
    "--uri is always UTF-8 hex-encoded for you; pass --uri-hex only for a value "
    "that is already hex. The two are mutually exclusive."
)

def _encode_nft_uri(uri: str, uri_hex: str):
    """Resolve the URI under an explicit contract.

    Guessing "even-length and hex-looking means pre-encoded" turned the text
    'cafe' into a literal URI of 'cafe'. NFT URIs are immutable for the token's
    life, so the guess is permanent: the caller declares the encoding instead.
    """
    if uri and uri_hex:
        raise ValueError("--uri and --uri-hex are mutually exclusive: pass exactly one.")
    if uri_hex is not None:
        if not uri_hex or len(uri_hex) % 2 or not all(c in "0123456789abcdefABCDEF" for c in uri_hex):
            raise ValueError(f"--uri-hex '{uri_hex}' is not an even-length hex string.")
        return uri_hex.upper()
    if not uri:
        return None
    return uri.encode("utf-8").hex().upper()

def tool_build_nft_mint(frm: str, taxon: int = 0, uri: str = "",
                        transfer_fee: int = 0, flags: int = 8,
                        issuer: str = None, uri_hex: str = None):
    try:
        uri = _encode_nft_uri(uri, uri_hex)
    except ValueError as exc:
        usage_out("build-nft-mint", f"{_URI_USAGE} {exc}")
        return
    tx = NFTokenMint(account=frm, nftoken_taxon=taxon,
                     uri=uri if uri else None,
                     transfer_fee=transfer_fee, flags=flags,
                     issuer=issuer if issuer else None)
    note_out("# NFTokenMint TX JSON - signer-ready JSON")
    json_tx_out(tx)

def tool_build_nft_create_offer(frm: str, nftoken_id: str, amount: str,
                                 flags: int = 1, destination: str = None,
                                 expiration: int = None, owner: str = None):
    try:
        amt = parse_amount_arg(amount)
    except ValueError as exc:
        usage_out("build-nft-create-offer",
                  "build-nft-create-offer --from rSRC --nftoken-id ID --amount DROPS "
                  f"| CUR:ISSUER:VALUE. {exc}")
        return
    kwargs = dict(account=frm, nftoken_id=nftoken_id, amount=amt, flags=int(flags))
    if destination: kwargs["destination"] = destination
    if expiration: kwargs["expiration"] = int(expiration)
    if owner: kwargs["owner"] = owner
    tx = NFTokenCreateOffer(**kwargs)
    note_out("# NFTokenCreateOffer TX JSON - signer-ready JSON")
    json_tx_out(tx)

def tool_build_nft_accept_offer(frm: str, sell_offer: str = None, buy_offer: str = None,
                                 broker_fee: str = None):
    kwargs = dict(account=frm)
    if sell_offer: kwargs["nftoken_sell_offer"] = sell_offer
    if buy_offer: kwargs["nftoken_buy_offer"] = buy_offer
    if broker_fee:
        try:
            kwargs["nftoken_broker_fee"] = parse_amount_arg(broker_fee)
        except ValueError as exc:
            usage_out("build-nft-accept-offer",
                      f"--broker-fee takes DROPS or CUR:ISSUER:VALUE. {exc}")
            return
    tx = NFTokenAcceptOffer(**kwargs)
    note_out("# NFTokenAcceptOffer TX JSON - signer-ready JSON")
    json_tx_out(tx)

def tool_build_nft_cancel_offer(frm: str, offers: str):
    ids = [o.strip() for o in offers.split(",") if o.strip()]
    tx = NFTokenCancelOffer(account=frm, nftoken_offers=ids)
    note_out("# NFTokenCancelOffer TX JSON")
    json_tx_out(tx)

def tool_build_nft_burn(frm: str, nftoken_id: str, owner: str = None):
    kwargs = dict(account=frm, nftoken_id=nftoken_id)
    if owner: kwargs["owner"] = owner
    tx = NFTokenBurn(**kwargs)
    note_out("# NFTokenBurn TX JSON")
    json_tx_out(tx)

COMMANDS = {
    "nft-info": lambda: tool_nft_info(__import__('sys').argv[2]) if len(__import__('sys').argv) >= 3 else print("Usage: nft-info NFT_ID"),
    "nft-offers": lambda: tool_nft_offers(__import__('sys').argv[2], __import__('sys').argv[3] if len(__import__('sys').argv) >= 4 else "sell") if len(__import__('sys').argv) >= 3 else print("Usage: nft-offers NFT_ID [sell|buy]"),
    "build-nft-mint": lambda: _dispatch_build(3, tool_build_nft_mint),
    "build-nft-create-offer": lambda: _dispatch_build(3, tool_build_nft_create_offer),
    "build-nft-accept-offer": lambda: _dispatch_build(1, tool_build_nft_accept_offer),
    "build-nft-cancel-offer": lambda: _dispatch_build(2, tool_build_nft_cancel_offer),
    "build-nft-burn": lambda: _dispatch_build(2, tool_build_nft_burn),
}
