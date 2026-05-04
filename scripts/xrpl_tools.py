#!/usr/bin/env python3
"""
XRPL-Hermes Tool Suite — Full XRPL MCP-Style Tools for Hermes
Maps to all XRPL-Hermes tool categories through terminal.

Usage:
  python3 xrpl_tools.py account rADDRESS
  python3 xrpl_tools.py balance rADDRESS
  python3 xrpl_tools.py trustlines rADDRESS [CURRENCY]
  python3 xrpl_tools.py account_objects rADDRESS [type]
  python3 xrpl_tools.py build-payment --from rADDR --to rADDR --amount DROPS
  python3 xrpl_tools.py build-trustset --from rADDR --currency CUR --issuer rISSUER --value AMOUNT
  python3 xrpl_tools.py build-offer --from rADDR --sell AMOUNT --buy CUR:ISSUER:AMOUNT
  python3 xrpl_tools.py build-nft-mint --from rADDR --taxon N --transfer-fee 5000 --uri ipfs://...
  python3 xrpl_tools.py build-amm-create --from rADDR --amount1 XRP:AMOUNT --amount2 CUR:ISSUER:AMOUNT --fee 600
  python3 xrpl_tools.py build-escrow-create --from rADDR --to rADDR --amount DROPS [--condition HEX] [--cancel-after EPOCH] [--finish-after EPOCH]
  python3 xrpl_tools.py build-escrow-finish --from rADDR --owner rADDR --offer-sequence N [--condition HEX] [--fulfillment HEX]
  python3 xrpl_tools.py build-escrow-cancel --from rADDR --owner rADDR --offer-sequence N
  python3 xrpl_tools.py build-check-create --from rADDR --to rADDR --amount DROPS [--invoice-id HEX] [--expiry EPOCH]
  python3 xrpl_tools.py build-check-cash --from rADDR --check-id HEX [--amount DROPS] [--deliver-min DROPS]
  python3 xrpl_tools.py build-check-cancel --from rADDR --check-id HEX
  python3 xrpl_tools.py build-paychannel-create --from rADDR --to rADDR --amount DROPS --settle-delay N --public-key HEX [--cancel-after EPOCH]
  python3 xrpl_tools.py build-paychannel-fund --from rADDR --channel-id HEX --amount DROPS
  python3 xrpl_tools.py build-paychannel-claim --from rADDR --channel-id HEX [--amount DROPS] [--balance DROPS] [--signature HEX] [--public-key HEX]
  python3 xrpl_tools.py build-set-regular-key --from rADDR [--regular-key rADDR]
  python3 xrpl_tools.py build-account-delete --from rADDR --to rADDR
  python3 xrpl_tools.py build-deposit-preauth --from rADDR --authorize rADDR
  python3 xrpl_tools.py build-deposit-preauth --from rADDR --unauthorize rADDR
  python3 xrpl_tools.py decode TX_BLOB
  python3 xrpl_tools.py tx-info TX_HASH
  python3 xrpl_tools.py ledger [INDEX]
  python3 xrpl_tools.py server-info
  python3 xrpl_tools.py nft-info NFT_ID
  python3 xrpl_tools.py book-offers CUR:ISSUER CUR:ISSUER
  python3 xrpl_tools.py path-find rSENDER rDEST AMOUNT CUR:ISSUER
  python3 xrpl_tools.py evm-balance 0xADDRESS [mainnet|testnet]
  python3 xrpl_tools.py evm-contract --from 0xADDR --bytecode HEX
  python3 xrpl_tools.py evm-bridge [mainnet|testnet]
  python3 xrpl_tools.py hooks-bitmask HOOK [HOOK ...]
  python3 xrpl_tools.py hooks-info rADDRESS
  python3 xrpl_tools.py flare-price SYMBOL [SYMBOL ...]
  python3 xrpl_tools.py build-clawback --from rISSUER --destination rHOLDER --currency USD --issuer rISSUER --amount 100 [--memo TEXT]
  python3 xrpl_tools.py build-amm-deposit --from rADDR --asset1 XRP --asset2 USD:rISSUER --amount1 XRP:1000000 --amount2 USD:rISSUER:100 [--mode two-asset]
  python3 xrpl_tools.py build-amm-withdraw --from rADDR --asset1 XRP --asset2 USD:rISSUER --amount1 XRP:500000 [--mode single-asset]
  python3 xrpl_tools.py build-amm-vote --from rADDR --asset1 XRP --asset2 USD:rISSUER --trading-fee 500
  python3 xrpl_tools.py build-amm-bid --from rADDR --asset1 XRP --asset2 USD:rISSUER [--bid-min LPT:rAMMPOOL:10]
  python3 xrpl_tools.py build-signer-list-set --from rADDR --quorum 2 --signers rADDR1:1,rADDR2:1,rADDR3:1
  python3 xrpl_tools.py build-mpt-issuance-create --from rADDR [--asset-scale 2] [--maximum-amount 1000000] [--transfer-fee 500]
  python3 xrpl_tools.py build-mpt-authorize --from rADDR --mpt-issuance-id HEX [--holder rADDR]
  python3 xrpl_tools.py build-set-oracle --from rADDR --oracle-doc-id N --provider HEX --asset-class HEX --last-update-time EPOCH [--price-data XRP/USD:123456:6]
  python3 xrpl_tools.py build-credential-create --from rISSUER --subject rHOLDER --credential-type HEX [--uri HEX] [--expiration EPOCH]
  python3 xrpl_tools.py build-credential-accept --from rHOLDER --issuer rISSUER --credential-type HEX
  python3 xrpl_tools.py build-credential-delete --from rADDR --credential-type HEX [--subject rADDR] [--issuer rADDR]
  python3 xrpl_tools.py build-cross-currency-payment --from rADDR --to rADDR --deliver USD:rISSUER:100 --send-max XRP:2000000
  python3 xrpl_tools.py build-batch --from rADDR --inner-txs '[{...},{...}]'
"""

import json, sys, os, hashlib
from typing import Optional, Dict, Any, List
from urllib.parse import quote
from datetime import datetime, timezone
from decimal import Decimal

# --- xrpl-py imports (with helpful error) ---
try:
    import xrpl
    from xrpl.models.requests import AccountInfo, AccountLines, AccountObjects, AccountTx, \
        BookOffers, NFTInfo, LedgerEntry, ServerInfo, Ledger, ServerState, RipplePathFind, Tx
    from xrpl.clients import JsonRpcClient
    from xrpl.utils import drops_to_xrp, xrp_to_drops
    from xrpl.models.transactions import Payment, TrustSet, OfferCreate, NFTokenMint, \
        NFTokenCreateOffer, AMMCreate, AMMDeposit, AMMWithdraw, AMMVote, AMMBid, \
        AccountSet, SignerListSet, EscrowCreate, \
        EscrowFinish, EscrowCancel, CheckCreate, CheckCancel, CheckCash, TicketCreate, \
        DepositPreauth, PaymentChannelCreate, PaymentChannelFund, PaymentChannelClaim, \
        SetRegularKey, AccountDelete, Clawback, OracleSet, \
        MPTokenIssuanceCreate, MPTokenAuthorize, \
        CredentialCreate, CredentialAccept, CredentialDelete, Batch
    from xrpl.models.transactions.signer_list_set import SignerEntry
    from xrpl.models.transactions.oracle_set import PriceData
    from xrpl.models.currencies import XRP as XRPCurrency, IssuedCurrency
    from xrpl.models.amounts import IssuedCurrencyAmount
except ImportError as e:
    print(f'ERROR: xrpl-py missing ({e}). Run: uv pip install xrpl-py')
    sys.exit(1)

# --- Endpoint Selection ---
# XRPL_PRIVATE_RPC env → user-configured private node (choice, not auto-detect)
# Otherwise → free public endpoints with auto-failover
_PRIVATE_RPC = os.environ.get("XRPL_PRIVATE_RPC", "").strip()
_FREE_ENDPOINTS = [
    "https://xrplcluster.com",
    "https://s1.ripple.com:51234",
    "https://s2.ripple.com:51234",
]

ENDPOINTS = [_PRIVATE_RPC] + _FREE_ENDPOINTS if _PRIVATE_RPC else _FREE_ENDPOINTS

def get_client() -> JsonRpcClient:
    for ep in ENDPOINTS:
        try:
            c = JsonRpcClient(ep)
            c.request(ServerInfo())
            return c
        except Exception:
            continue
    return JsonRpcClient(ENDPOINTS[0])

_CLIENT: Optional[JsonRpcClient] = None
_ENDPOINT_IDX = 0
_USING_PRIVATE = bool(_PRIVATE_RPC)

def _get_client() -> JsonRpcClient:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = get_client()
    return _CLIENT

def _request(req):
    global _CLIENT, _ENDPOINT_IDX
    client = _get_client()
    try:
        return client.request(req)
    except Exception as e:
        _ENDPOINT_IDX = (_ENDPOINT_IDX + 1) % len(ENDPOINTS)
        try:
            _CLIENT = JsonRpcClient(ENDPOINTS[_ENDPOINT_IDX])
            return _CLIENT.request(req)
        except Exception as e2:
            raise Exception(f"All endpoints failed: {e2}") from e2

# --- Helpers ---

def fmt_xrp(drops_val) -> str:
    return f"{drops_to_xrp(str(drops_val)):,.6f} XRP"

def short(addr: str) -> str:
    return f"{addr[:8]}...{addr[-6:]}"

def parse_currency_arg(arg: str) -> tuple:
    """Parse 'XRP:1000000' or 'TOKEN:rISSUER:100' into (currency, issuer, value)"""
    parts = arg.split(":", 2)
    if len(parts) == 1:
        return parts[0], None, None
    elif len(parts) == 2:
        return parts[0], None, parts[1]
    else:
        return parts[0], parts[1], parts[2]

def make_amount(currency: str, issuer: Optional[str], value: str) -> dict:
    """Build XRP or token amount dict for transaction building."""
    if currency.upper() == "XRP" and not issuer:
        return value if value is not None else currency  # drops as string
    return {
        "currency": currency,
        "issuer": issuer,
        "value": value
    }

def json_out(obj):
    """Print JSON and return it."""
    print(json.dumps(obj, indent=2, default=str))

def usage_out(command: str, usage: str):
    """Emit script-friendly usage errors without traceback noise."""
    json_out({
        "Error": "UsageError",
        "Command": command,
        "Usage": usage,
    })

def note_out(message: str):
    """Print human notes to stderr. Suppress with XRPL_TOOLS_QUIET=1 for scriptable output."""
    if not os.environ.get("XRPL_TOOLS_QUIET"):
        print(message, file=sys.stderr)

def tx_to_xrpl_json(tx):
    """Return signer-ready XRPL JSON with canonical field names."""
    return tx.to_xrpl() if hasattr(tx, "to_xrpl") else tx.to_dict()

def json_tx_out(tx):
    json_out(tx_to_xrpl_json(tx))

def ripple_time_to_iso(value) -> str:
    if value in (None, "", "?"):
        return "?"
    try:
        return datetime.fromtimestamp(int(value) + 946684800, tz=timezone.utc).isoformat()
    except Exception:
        return str(value)

def get_reserve_settings() -> tuple[Decimal, Decimal]:
    try:
        info = _request(ServerInfo()).result.get("info", {})
        ledger = info.get("validated_ledger", {})
        return Decimal(str(ledger.get("reserve_base_xrp", 1))), Decimal(str(ledger.get("reserve_inc_xrp", 0.2)))
    except Exception:
        return Decimal("1"), Decimal("0.2")

def _parse_value_slash_asset(arg: str):
    """Parse 'VALUE/CUR:ISSUER' into (currency, issuer, value), if applicable."""
    if "/" not in arg:
        return None
    value, asset = arg.split("/", 1)
    if ":" not in asset:
        return None
    currency, issuer = asset.split(":", 1)
    return currency, issuer, value

def _is_numeric_text(arg: str) -> bool:
    return bool(arg) and arg.replace(".", "", 1).isdigit()

def parse_amount_arg(arg: str):
    """Parse drops, XRP:DROPS, CUR:ISSUER:VALUE, or VALUE/CUR:ISSUER."""
    slash = _parse_value_slash_asset(arg)
    if slash:
        cur, iss, val = slash
        return IssuedCurrencyAmount(currency=cur.upper(), issuer=iss, value=val)
    if _is_numeric_text(arg):
        return arg
    parts = arg.split(":", 2)
    if parts[0].upper() == "XRP":
        return parts[1] if len(parts) >= 2 else arg
    if len(parts) == 3:
        return IssuedCurrencyAmount(currency=parts[0].upper(), issuer=parts[1], value=parts[2])
    return arg

def _parse_asset(arg: str):
    """Parse 'XRP', 'XRP:DROPS', 'CUR:ISSUER', or 'CUR:ISSUER:VALUE' as an AMM asset."""
    if _is_numeric_text(arg):
        return XRPCurrency()
    slash = _parse_value_slash_asset(arg)
    if slash:
        currency, issuer, _value = slash
        return IssuedCurrency(currency=currency.upper(), issuer=issuer)
    parts = arg.split(":", 2)
    if parts[0].upper() == "XRP":
        return XRPCurrency()
    if len(parts) >= 2:
        return IssuedCurrency(currency=parts[0].upper(), issuer=parts[1])
    raise ValueError(f"Invalid asset '{arg}'. Use 'XRP' or 'CUR:ISSUER'")

def _parse_amount_for_amm(arg: str):
    """Parse 'XRP:DROPS' or 'CUR:ISSUER:VALUE' into drops str or IssuedCurrencyAmount."""
    parsed = parse_amount_arg(arg)
    if not isinstance(parsed, str) or _is_numeric_text(parsed):
        return parsed
    parts = arg.split(":", 2)
    if parts[0].upper() == "XRP":
        return parts[1] if len(parts) >= 2 else arg
    if len(parts) == 3:
        return IssuedCurrencyAmount(currency=parts[0].upper(), issuer=parts[1], value=parts[2])
    raise ValueError(f"Invalid amount '{arg}'. Use 'XRP:DROPS' or 'CUR:ISSUER:VALUE'")

# --- TOOL 1: Account Info ---
def tool_account(address: str):
    try:
        resp = _request(AccountInfo(account=address, ledger_index="validated"))
    except Exception as e:
        json_out({"Error": "AccountInfoError", "Message": str(e), "Account": address})
        return
    data = resp.result.get("account_data", {})
    bal = int(data.get("Balance", 0))
    flags = data.get("Flags", 0)
    seq = data.get("Sequence", 0)
    owner = data.get("OwnerCount", 0)
    domain_raw = data.get("Domain", "")
    domain = ""
    if domain_raw:
        try: domain = bytes.fromhex(domain_raw).decode()
        except: domain = domain_raw
    reserve_base, reserve_inc = get_reserve_settings()
    reserved = reserve_base + reserve_inc * Decimal(owner)
    spendable = drops_to_xrp(str(bal)) - reserved
    flag_descriptions = []
    if flags & 0x00800000: flag_descriptions.append("lsfDefaultRipple")
    if flags & 0x01000000: flag_descriptions.append("lsfDepositAuth")
    if flags & 0x00100000: flag_descriptions.append("lsfDisableMasterKey")
    if flags & 0x00080000: flag_descriptions.append("lsfDisallowXRP")
    if flags & 0x00400000: flag_descriptions.append("lsfGlobalFreeze")
    if flags & 0x00200000: flag_descriptions.append("lsfNoFreeze")
    if flags & 0x00040000: flag_descriptions.append("lsfRequireAuth")
    if flags & 0x00020000: flag_descriptions.append("lsfRequireDestTag")
    if flags & 0x80000000: flag_descriptions.append("lsfAllowTrustLineClawback")
    json_out({
        "Account": address,
        "BalanceDrops": str(bal),
        "BalanceXRP": str(drops_to_xrp(str(bal))),
        "ReserveXRP": str(reserved),
        "OwnerCount": owner,
        "SpendableXRP": str(spendable),
        "Sequence": seq,
        "Domain": domain or None,
        "Flags": flags,
        "FlagDescriptions": flag_descriptions,
    })

# --- TOOL 2: Trustlines ---
def tool_trustlines(address: str, currency: Optional[str] = None):
    all_lines = []
    marker = None
    while True:
        try:
            resp = _request(AccountLines(account=address, ledger_index="validated", marker=marker))
        except Exception as e:
            json_out({"Error": "AccountLinesError", "Message": str(e), "Account": address})
            return
        data = resp.result
        all_lines.extend(data.get("lines", []))
        marker = data.get("marker")
        if not marker:
            break
    if currency:
        filtered = [l for l in all_lines if l.get("currency", "").upper() == currency.upper()]
        if not filtered:
            json_out({"Account": address, "Currency": currency.upper(), "TrustLines": []})
            return
        all_lines = filtered
    json_out({
        "Account": address,
        "Currency": currency.upper() if currency else None,
        "TrustLineCount": len(all_lines),
        "TrustLines": all_lines,
    })

# --- TOOL 3: Transaction Building ---
def tool_build_payment(frm: str, to: str, amount: str, cur: Optional[str] = None,
                       iss: Optional[str] = None, tag: Optional[int] = None, memo: Optional[str] = None):
    if cur and cur.upper() != "XRP" and iss:
        amt = IssuedCurrencyAmount(currency=cur, issuer=iss, value=amount)
    else:
        amt = amount
    tx = Payment(account=frm, destination=to, amount=amt,
                 destination_tag=tag if tag else None)
    note_out("# Payment TX JSON - signer-ready JSON - paste into Xaman Developer tab")
    tx_json = tx_to_xrpl_json(tx)
    json_out(tx_json)
    note_out("# Xaman deep-link requires the Xaman Platform API (not implemented here).")
    note_out("# To sign: paste the JSON above into Xaman Developer > Sign Transaction")

def tool_build_trustset(frm: str, currency: str, issuer: str, value: str = "1000000000"):
    cur = IssuedCurrencyAmount(currency=currency, issuer=issuer, value=value)
    tx = TrustSet(account=frm, limit_amount=cur)
    note_out("# TrustSet TX JSON - signer-ready JSON - paste into Xaman Developer tab")
    json_tx_out(tx)

def tool_build_offer(frm: str, taker_gets: str = None, taker_pays: str = None,
                     sell: str = None, buy: str = None):
    """Build OfferCreate. Accepts --taker_gets/--taker_pays or --sell/--buy aliases.
    Format: 'XRP:AMOUNT' or 'CUR:ISSUER:AMOUNT'"""
    taker_gets = taker_gets or sell
    taker_pays = taker_pays or buy
    if not taker_gets or not taker_pays:
        print("Usage: build-offer --from rADDR --sell XRP:AMOUNT --buy CUR:ISS:AMOUNT")
        print("  or:  build-offer --from rADDR --taker_gets XRP:AMOUNT --taker_pays CUR:ISS:AMOUNT")
        return
    gets = parse_amount_arg(taker_gets)
    pays = parse_amount_arg(taker_pays)
    tx = OfferCreate(account=frm, taker_gets=gets, taker_pays=pays)
    note_out("# OfferCreate TX JSON - signer-ready JSON - paste into Xaman Developer tab")
    json_tx_out(tx)

def tool_build_nft_mint(frm: str, taxon: int = 0, uri: str = "",
                         transfer_fee: int = 0, flags: int = 8,
                         issuer: Optional[str] = None):
    # Auto-hex-encode URI if it looks like a plain string (http/ipfs/non-hex)
    if uri:
        hex_chars = set('0123456789abcdefABCDEF')
        is_already_hex = all(c in hex_chars for c in uri) and len(uri) % 2 == 0
        if not is_already_hex:
            uri = uri.encode().hex().upper()
    tx = NFTokenMint(
        account=frm,
        nftoken_taxon=taxon,
        uri=uri if uri else None,
        transfer_fee=transfer_fee,
        flags=flags,
        issuer=issuer if issuer else None,
    )
    note_out("# NFTokenMint TX JSON - signer-ready JSON - paste into Xaman Developer tab")
    json_tx_out(tx)

def tool_build_amm_create(frm: str, amount1: str, amount2: str, fee: int = 600):
    """amount1/amount2 format: 'XRP:AMOUNT' or 'CUR:ISSUER:AMOUNT'"""
    amt1 = parse_amount_arg(amount1)
    amt2 = parse_amount_arg(amount2)
    tx = AMMCreate(account=frm, amount=amt1, amount2=amt2, trading_fee=fee)
    note_out("# AMMCreate TX JSON - signer-ready JSON - paste into Xaman Developer tab")
    json_tx_out(tx)

# --- TOOL 4: Decode Transaction ---
def tool_decode(blob: str):
    from xrpl.core.binarycodec import decode
    try:
        decoded = decode(blob)
        json_out(decoded)
    except Exception as e:
        json_out({
            "Error": "DecodeError",
            "Message": str(e),
            "Blob": blob,
        })

# --- TOOL 5: Transaction Info ---
def tool_tx_info(tx_hash: str):
    try:
        resp = _request(Tx(transaction=tx_hash))
    except Exception as e:
        json_out({"Error": "TxError", "Message": str(e), "Transaction": tx_hash})
        return
    data = resp.result
    tx_json = data.get("tx_json", data)
    status = data.get("meta", {}).get("TransactionResult", "?")
    tx_type = tx_json.get("TransactionType", "?")
    account = tx_json.get("Account", "?")
    dest = tx_json.get("Destination", "")
    fee = tx_json.get("Fee", "0")
    date_value = data.get("close_time_iso") or tx_json.get("date") or data.get("date")
    json_out({
        "Hash": tx_hash,
        "TransactionType": tx_type,
        "Status": status,
        "Account": account,
        "Destination": dest or None,
        "FeeDrops": fee,
        "FeeXRP": str(drops_to_xrp(str(fee))),
        "LedgerIndex": data.get("ledger_index"),
        "Date": ripple_time_to_iso(date_value),
        "Raw": data,
    })

# --- TOOL 6: Ledger Info ---
def tool_ledger(index: Optional[int] = None):
    try:
        resp = _request(Ledger(ledger_index=index if index else "validated", transactions=False))
    except Exception as e:
        json_out({"Error": "LedgerError", "Message": str(e), "LedgerIndex": index})
        return
    data = resp.result.get("ledger", {})
    json_out({
        "LedgerIndex": data.get("ledger_index"),
        "LedgerHash": data.get("ledger_hash"),
        "CloseTimeHuman": data.get("close_time_human"),
        "TotalCoinsDrops": data.get("total_coins"),
        "TotalCoinsXRP": str(drops_to_xrp(str(data.get("total_coins", "0")))),
        "TransactionCount": data.get("transaction_count", 0),
        "CloseFlags": data.get("close_flags", 0),
    })

# --- TOOL 7: Server Info ---
def tool_server_info():
    try:
        resp = _request(ServerInfo())
    except Exception as e:
        json_out({"Error": "ServerInfoError", "Message": str(e)})
        return
    info = resp.result.get("info", {})
    validated = info.get("validated_ledger", {})
    json_out({
        "BuildVersion": info.get("build_version"),
        "Uptime": info.get("uptime", 0),
        "CompleteLedgers": info.get("complete_ledgers"),
        "ValidatedLedger": validated,
        "ServerState": info.get("server_state"),
        "Info": info,
    })

# --- TOOL 8: Book Offers ---
def tool_book_offers(taker_gets: str, taker_pays: str):
    """Format: 'XRP' or 'CUR:ISSUER'. Uses raw HTTP to avoid xrpl-py currency validation."""
    import httpx

    def parse_book_side(arg: str):
        """Parse 'XRP' or 'CUR:ISSUER' for book_offers."""
        parts = arg.split(":", 1)
        return (parts[0], parts[1] if len(parts) == 2 else None)

    gets_cur, gets_iss = parse_book_side(taker_gets)
    pays_cur, pays_iss = parse_book_side(taker_pays)

    # Build params as the rippled API expects them
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

    # Use raw JSON-RPC with failover
    import json
    payload = {
        "method": "book_offers",
        "params": [{
            "taker_gets": gets_param,
            "taker_pays": pays_param,
            "limit": 10,
            "ledger_index": "current"
        }]
    }
    data = {}
    for ep in ENDPOINTS:
        try:
            resp = httpx.post(ep, json=payload, timeout=10)
            data = resp.json()
            if "result" in data:
                break
        except Exception:
            continue
    offers = data.get("result", {}).get("offers", [])
    json_out({
        "TakerGets": taker_gets,
        "TakerPays": taker_pays,
        "OfferCount": len(offers),
        "Offers": offers[:10],
        "Raw": data.get("result", data),
    })

# --- TOOL 9: Path Find ---
def tool_path_find(src: str, dest: str, amount: str, cur: str, iss: Optional[str] = None):
    dest_amt = make_amount(cur, iss, amount)
    try:
        resp = _request(RipplePathFind(source_account=src, destination_account=dest,
                                       destination_amount=dest_amt))
        alts = resp.result.get("alternatives", [])
        json_out({
            "SourceAccount": src,
            "DestinationAccount": dest,
            "DestinationAmount": dest_amt,
            "PathCount": len(alts),
            "Alternatives": alts,
        })
    except Exception as e:
        json_out({"Error": "PathFindError", "Message": str(e)})

# --- (removed dead tool_xaman_url — see build-payment for the honest sign message) ---

# --- Main Dispatch ---
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1].lower()

    dispatcher = {
        "account": lambda: tool_account(sys.argv[2]) if len(sys.argv) >= 3 else print("Usage: account rADDRESS"),
        "balance": lambda: tool_account(sys.argv[2]) if len(sys.argv) >= 3 else print("Usage: balance rADDRESS"),
        "trustlines": lambda: tool_trustlines(sys.argv[2], sys.argv[3] if len(sys.argv) >= 4 else None) if len(sys.argv) >= 3 else usage_out("trustlines", "trustlines rADDRESS [CURRENCY]"),
        "account_objects": lambda: tool_account_objects(sys.argv[2], sys.argv[3] if len(sys.argv) >= 4 else None) if len(sys.argv) >= 3 else print("Usage: account_objects rADDRESS [type]"),
        "build-payment": lambda: _dispatch_build(3, tool_build_payment),
        "build-trustset": lambda: _dispatch_build(2, tool_build_trustset),
        "build-offer": lambda: _dispatch_build(3, tool_build_offer),
        "build-nft-mint": lambda: _dispatch_build(3, tool_build_nft_mint),
        "build-amm-create": lambda: _dispatch_build(4, tool_build_amm_create),
        "build-escrow-create": lambda: _dispatch_build(3, tool_build_escrow_create),
        "build-escrow-finish": lambda: _dispatch_build(3, tool_build_escrow_finish),
        "build-escrow-cancel": lambda: _dispatch_build(3, tool_build_escrow_cancel),
        "build-check-create": lambda: _dispatch_build(3, tool_build_check_create),
        "build-check-cash": lambda: _dispatch_build(2, tool_build_check_cash),
        "build-check-cancel": lambda: _dispatch_build(2, tool_build_check_cancel),
        "build-paychannel-create": lambda: _dispatch_build(5, tool_build_paychannel_create),
        "build-paychannel-fund": lambda: _dispatch_build(3, tool_build_paychannel_fund),
        "build-paychannel-claim": lambda: _dispatch_build(2, tool_build_paychannel_claim),
        "build-set-regular-key": lambda: _dispatch_build(1, tool_build_set_regular_key),
        "build-account-delete": lambda: _dispatch_build(2, tool_build_account_delete),
        "build-deposit-preauth": lambda: _dispatch_build(2, tool_build_deposit_preauth),
        "decode": lambda: tool_decode(sys.argv[2]) if len(sys.argv) >= 3 else print("Usage: decode TX_BLOB"),
        "tx-info": lambda: tool_tx_info(sys.argv[2]) if len(sys.argv) >= 3 else print("Usage: tx-info TX_HASH"),
        "ledger": lambda: tool_ledger(int(sys.argv[2]) if len(sys.argv) >= 3 and sys.argv[2].isdigit() else None),
        "server-info": lambda: tool_server_info(),
        "nft-info": lambda: tool_nft_info(sys.argv[2]) if len(sys.argv) >= 3 else print("Usage: nft-info NFT_ID"),
        "book-offers": lambda: tool_book_offers(sys.argv[2], sys.argv[3]) if len(sys.argv) >= 4 else print("Usage: book-offers TAKER_GETS TAKER_PAYS"),
        "path-find": lambda: _dispatch_path_find(),
        "evm-balance": lambda: tool_evm_balance(sys.argv[2], sys.argv[3] if len(sys.argv) >= 4 else "mainnet") if len(sys.argv) >= 3 else usage_out("evm-balance", "evm-balance 0xADDRESS [mainnet|testnet]"),
        "evm-contract": lambda: _dispatch_build(2, tool_evm_contract),
        "evm-bridge": lambda: tool_evm_bridge(sys.argv[2] if len(sys.argv) >= 3 else "mainnet"),
        "hooks-bitmask": lambda: tool_hooks_bitmask(*sys.argv[2:]),
        "hooks-info": lambda: tool_hooks_info(sys.argv[2]) if len(sys.argv) >= 3 else print("Usage: hooks-info rADDRESS"),
        "flare-price": lambda: tool_flare_price(*sys.argv[2:]),
        "build-clawback": lambda: _dispatch_build(4, tool_build_clawback),
        "build-amm-deposit": lambda: _dispatch_build(3, tool_build_amm_deposit),
        "build-amm-withdraw": lambda: _dispatch_build(3, tool_build_amm_withdraw),
        "build-amm-vote": lambda: _dispatch_build(4, tool_build_amm_vote),
        "build-amm-bid": lambda: _dispatch_build(3, tool_build_amm_bid),
        "build-signer-list-set": lambda: _dispatch_build(2, tool_build_signer_list_set),
        "build-mpt-issuance-create": lambda: _dispatch_build(1, tool_build_mpt_issuance_create),
        "build-mpt-authorize": lambda: _dispatch_build(2, tool_build_mpt_authorize),
        "build-set-oracle": lambda: _dispatch_build(5, tool_build_set_oracle),
        "build-credential-create": lambda: _dispatch_build(3, tool_build_credential_create),
        "build-credential-accept": lambda: _dispatch_build(3, tool_build_credential_accept),
        "build-credential-delete": lambda: _dispatch_build(2, tool_build_credential_delete),
        "build-cross-currency-payment": lambda: _dispatch_build(4, tool_build_cross_currency_payment),
        "build-batch": lambda: _dispatch_build(2, tool_build_batch),
    }

    fn = dispatcher.get(cmd)
    if fn:
        fn()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)

def _parse_build_kwargs(keys: list) -> dict:
    kwargs = {}
    for i in range(2, len(sys.argv) - 1, 2):
        k = sys.argv[i].lstrip("--").replace("-", "_")
        v = sys.argv[i + 1]
        if k in keys:
            kwargs[k] = v
    return kwargs

def _dispatch_build(min_pairs: int, fn):
    """Dispatch a build command by parsing --key value pairs from argv."""
    kwargs = {}
    for i in range(2, len(sys.argv) - 1, 2):
        k = sys.argv[i].lstrip("--").replace("-", "_")
        v = sys.argv[i + 1]
        if k in ('taxon', 'transfer_fee', 'flags', 'fee'):
            try: v = int(v)
            except: pass
        elif v.replace('.','',1).lstrip('-').isdigit() and '.' in v:
            try: v = float(v)
            except: pass
        kwargs[k] = v
    if len(kwargs) < min_pairs:
        print(f"Need at least {min_pairs} arguments for {sys.argv[1]}")
        return
    # Map 'from' -> 'frm' for Python keyword compatibility
    if 'from' in kwargs:
        kwargs['frm'] = kwargs.pop('from')
    try:
        fn(**kwargs)
    except Exception as e:
        json_out({
            "Error": e.__class__.__name__,
            "Message": str(e),
            "Command": sys.argv[1],
        })

def _dispatch_path_find():
    if len(sys.argv) < 6:
        print("Usage: path-find rSENDER rDEST AMOUNT CUR:ISSUER")
        return
    src, dest, amount = sys.argv[2], sys.argv[3], sys.argv[4]
    cur_parts = sys.argv[5].split(":", 1)
    cur = cur_parts[0]
    iss = cur_parts[1] if len(cur_parts) > 1 else None
    tool_path_find(src, dest, amount, cur, iss)

def tool_nft_info(nft_id: str):
    from xrpl.models.requests import NFTInfo
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
        json_out({
            "Error": result.get("error"),
            "Message": result.get("error_message", "no message"),
            "NFTokenID": nft_id,
        })
        return
    json_out(result)

# --- TOOL 11: EVM Sidechain Balance ---
def tool_evm_balance(address: str, network: str = "mainnet"):
    """Query XRP balance on EVM sidechain. Address must be 0x-prefixed Ethereum address."""
    import httpx
    rpc_urls = {"mainnet": "https://rpc.xrplevm.org", "testnet": "https://rpc.testnet.xrplevm.org"}
    url = rpc_urls.get(network, rpc_urls["mainnet"])
    payload = {"jsonrpc": "2.0", "method": "eth_getBalance", "params": [address, "latest"], "id": 1}
    resp = httpx.post(url, json=payload, timeout=10)
    data = resp.json()
    wei = int(data.get("result", "0x0"), 16)
    xrp = wei / 1e18
    json_out({
        "Address": address,
        "Network": network,
        "RPC": url,
        "BalanceWei": str(wei),
        "BalanceXRP": f"{xrp:.18f}".rstrip("0").rstrip(".") or "0",
        "Raw": data,
    })

# --- TOOL 12: EVM Contract Deploy ---
def tool_evm_contract(frm: str, bytecode: str, abi: str = None, value: str = "0", gas: str = "200000"):
    tx = {
        "from": frm,
        "data": bytecode if bytecode.startswith("0x") else "0x" + bytecode,
        "value": hex(int(value)),
        "gas": hex(int(gas)),
        "chainId": 1440000,
    }
    if abi:
        try: tx["abi"] = json.loads(abi)
        except: tx["abi"] = abi
    note_out("# EVM Contract Deployment - sign and submit to https://rpc.xrplevm.org")
    json_out(tx)

# --- TOOL 13: EVM Bridge Check ---
def tool_evm_bridge(network: str = "mainnet"):
    import httpx
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
    json_out({
        "Network": network,
        "LatestBlock": block,
        "RPC": url,
        "ConfiguredChainID": cid,
        "ObservedChainID": observed_cid,
        "Bridge": "L1-EVM federated bridge active",
        "RawChainID": chain_resp,
    })

# --- TOOL 14: Hooks Bitmask (BROKEN — Xahau HookOn uses tx-type ID bitmap, not named events)
# This tool is placeholder. Real implementation requires the full Xahau HookOn bitmap spec from xrpld.
# See: https://xrpl-hooks.readthedocs.io/
HOOK_BITS = {}  # Will be populated once real mapping is determined

def tool_hooks_bitmask(*hook_names: str):
    """⚠️ Currently BROKEN — Xahau HookOn is a 256-bit bitmap indexed by tx-type ID, not named events.
    This tool produces incorrect values. Do not use for production hook deployments."""
    json_out({
        "Error": "UnsupportedTool",
        "Command": "hooks-bitmask",
        "HookNames": list(hook_names),
        "Message": "hooks-bitmask is disabled because Xahau HookOn uses a 256-bit bitmap indexed by transaction-type ID, not named events.",
    })

# --- TOOL 15: Hooks Account Info ---
def tool_hooks_info(address: str):
    import httpx
    payload = {"method": "account_objects", "params": [{"account": address, "ledger_index": "validated", "type": "hook", "limit": 20}]}
    try:
        resp = httpx.post("https://xahau.network", json=payload, timeout=15)
        data = resp.json()
        hooks = data.get("result", {}).get("account_objects", [])
        json_out({
            "Account": address,
            "HookCount": len(hooks),
            "Hooks": hooks,
            "Raw": data.get("result", data),
        })
    except Exception as e:
        json_out({"Error": "HooksInfoError", "Message": str(e), "Account": address})

# --- TOOL 16: Flare Price Feeds ---
def tool_flare_price(*symbols: str):
    import httpx
    urls = [
        "https://api.flare.network/ftso/v2/feeds",
        "https://flare-api.flare.network/ftso/v2/feeds",
    ]
    feeds = {}
    for url in urls:
        try:
            resp = httpx.get(url, timeout=10)
            data = resp.json()
            for f in data:
                feed_name = f.get("feed", "").upper()
                if feed_name:
                    feeds[feed_name] = float(f.get("value", 0))
            break
        except Exception:
            continue
    result = {}
    for sym in symbols:
        s = sym.upper()
        if s in feeds:
            result[s] = feeds[s]
        else:
            result[s] = None
    json_out({"Prices": result, "FeedCount": len(feeds)})

# --- TOOL 17: Escrow Create ---
def tool_build_escrow_create(frm: str, to: str, amount: str, condition: str = None,
                              cancel_after: str = None, finish_after: str = None):
    kwargs = dict(account=frm, destination=to, amount=amount)
    if condition:
        kwargs["condition"] = condition
    if cancel_after:
        kwargs["cancel_after"] = int(cancel_after)
    if finish_after:
        kwargs["finish_after"] = int(finish_after)
    tx = EscrowCreate(**kwargs)
    note_out("# EscrowCreate TX JSON - signer-ready JSON - paste into Xaman Developer tab")
    json_tx_out(tx)

# --- Escrow Finish ---
def tool_build_escrow_finish(frm: str, owner: str, offer_sequence: str,
                              condition: str = None, fulfillment: str = None):
    kwargs = dict(account=frm, owner=owner, offer_sequence=int(offer_sequence))
    if condition:
        kwargs["condition"] = condition
    if fulfillment:
        kwargs["fulfillment"] = fulfillment
    tx = EscrowFinish(**kwargs)
    note_out("# EscrowFinish TX JSON - signer-ready JSON - paste into Xaman Developer tab")
    json_tx_out(tx)

# --- Escrow Cancel ---
def tool_build_escrow_cancel(frm: str, owner: str, offer_sequence: str):
    tx = EscrowCancel(account=frm, owner=owner, offer_sequence=int(offer_sequence))
    note_out("# EscrowCancel TX JSON - signer-ready JSON - paste into Xaman Developer tab")
    json_tx_out(tx)

# --- Check Create ---
def tool_build_check_create(frm: str, to: str, amount: str, invoice_id: str = None,
                             expiry: str = None):
    parts = amount.split(":", 2)
    if len(parts) == 3:
        send_max = {"currency": parts[0], "issuer": parts[1], "value": parts[2]}
    else:
        send_max = amount
    kwargs = dict(account=frm, destination=to, send_max=send_max)
    if invoice_id:
        kwargs["invoice_id"] = invoice_id
    if expiry:
        kwargs["expiration"] = int(expiry)
    tx = CheckCreate(**kwargs)
    note_out("# CheckCreate TX JSON - signer-ready JSON - paste into Xaman Developer tab")
    json_tx_out(tx)

# --- Check Cash ---
def tool_build_check_cash(frm: str, check_id: str, amount: str = None,
                           deliver_min: str = None):
    if not amount and not deliver_min:
        print("CheckCash requires --amount OR --deliver-min")
        return
    kwargs = dict(account=frm, check_id=check_id)
    if amount:
        kwargs["amount"] = amount
    if deliver_min:
        kwargs["deliver_min"] = deliver_min
    tx = CheckCash(**kwargs)
    note_out("# CheckCash TX JSON - signer-ready JSON - paste into Xaman Developer tab")
    json_tx_out(tx)

# --- Check Cancel ---
def tool_build_check_cancel(frm: str, check_id: str):
    tx = CheckCancel(account=frm, check_id=check_id)
    note_out("# CheckCancel TX JSON - signer-ready JSON - paste into Xaman Developer tab")
    json_tx_out(tx)

# --- Payment Channel Create ---
def tool_build_paychannel_create(frm: str, to: str, amount: str, settle_delay: str,
                                  public_key: str, cancel_after: str = None):
    kwargs = dict(
        account=frm,
        destination=to,
        amount=amount,
        settle_delay=int(settle_delay),
        public_key=public_key,
    )
    if cancel_after:
        kwargs["cancel_after"] = int(cancel_after)
    tx = PaymentChannelCreate(**kwargs)
    note_out("# PaymentChannelCreate TX JSON - signer-ready JSON - paste into Xaman Developer tab")
    json_tx_out(tx)

# --- TOOL 18: Payment Channel Fund ---
def tool_build_paychannel_fund(frm: str, channel_id: str, amount: str):
    tx = PaymentChannelFund(account=frm, channel=channel_id, amount=amount)
    note_out("# PaymentChannelFund TX JSON - signer-ready JSON - paste into Xaman Developer tab")
    json_tx_out(tx)

# --- TOOL 19: Payment Channel Claim ---
def tool_build_paychannel_claim(frm: str, channel_id: str, amount: str = None,
                                 balance: str = None, signature: str = None,
                                 public_key: str = None):
    kwargs = dict(account=frm, channel=channel_id)
    if amount:
        kwargs["amount"] = amount
    if balance:
        kwargs["balance"] = balance
    if signature:
        kwargs["signature"] = signature
    if public_key:
        kwargs["public_key"] = public_key
    tx = PaymentChannelClaim(**kwargs)
    note_out("# PaymentChannelClaim TX JSON - signer-ready JSON - paste into Xaman Developer tab")
    json_tx_out(tx)

# --- TOOL 20: Set Regular Key ---
def tool_build_set_regular_key(frm: str, regular_key: str = None):
    kwargs = dict(account=frm)
    if regular_key:
        kwargs["regular_key"] = regular_key
    tx = SetRegularKey(**kwargs)
    note_out("# SetRegularKey TX JSON - signer-ready JSON - paste into Xaman Developer tab")
    json_tx_out(tx)

# --- TOOL 21: Account Delete ---
def tool_build_account_delete(frm: str, to: str):
    tx = AccountDelete(account=frm, destination=to)
    note_out("# AccountDelete TX JSON - signer-ready JSON - paste into Xaman Developer tab")
    json_tx_out(tx)

# --- TOOL 22: Deposit Preauth ---
def tool_build_deposit_preauth(frm: str, authorize: str = None, unauthorize: str = None):
    if not authorize and not unauthorize:
        print("DepositPreauth requires --authorize OR --unauthorize")
        return
    kwargs = dict(account=frm)
    if authorize:
        kwargs["authorize"] = authorize
    if unauthorize:
        kwargs["unauthorize"] = unauthorize
    tx = DepositPreauth(**kwargs)
    note_out("# DepositPreauth TX JSON - signer-ready JSON - paste into Xaman Developer tab")
    json_tx_out(tx)

# --- TOOL 23: Account Objects ---
def tool_account_objects(address: str, obj_type: str = None):
    try:
        req_kwargs = dict(account=address, ledger_index="validated")
        if obj_type:
            try:
                from xrpl.models.requests.account_objects import AccountObjectType
                req_kwargs["type"] = AccountObjectType(obj_type.lower())
            except Exception:
                pass
        resp = _request(AccountObjects(**req_kwargs))
    except Exception as e:
        json_out({"Error": "AccountObjectsError", "Message": str(e), "Account": address})
        return
    objects = resp.result.get("account_objects", [])
    json_out({
        "Account": address,
        "Type": obj_type,
        "ObjectCount": len(objects),
        "Objects": objects,
    })

# --- TOOL 35: Clawback ---
def tool_build_clawback(frm: str, destination: str, currency: str,
                         amount: str, issuer: str = None, memo: str = None):
    """Build a Clawback transaction (issuer reclaims tokens from holder).

    In the Clawback TX: account=issuer, amount.issuer=holder_address.
    --destination is the holder being clawed back from.
    --issuer is the token issuer (defaults to --from if omitted).
    """
    import re
    try:
        amt_val = float(amount)
        if amt_val <= 0:
            print("Error: amount must be positive")
            return
    except ValueError:
        print(f"Error: invalid amount '{amount}'")
        return

    cur = currency.upper()
    if not (re.match(r'^[A-Z0-9]{3}$', cur) or re.match(r'^[0-9A-F]{40}$', cur)):
        print(f"Error: currency must be 3-letter ISO code or 40-char hex, got '{currency}'")
        return

    # amount.issuer = holder being clawed back (XRPL Clawback protocol)
    amount_obj = IssuedCurrencyAmount(currency=cur, issuer=destination, value=amount)
    kwargs: dict = dict(account=frm, amount=amount_obj)
    if memo:
        memo_hex = memo.encode("utf-8").hex().upper()
        from xrpl.models.transactions.transaction import Memo
        kwargs["memos"] = [Memo(memo_data=memo_hex)]
    tx = Clawback(**kwargs)
    note_out("# Clawback TX JSON - signer-ready JSON - paste into Xaman Developer tab")
    json_tx_out(tx)


# --- TOOL 36: AMM Deposit ---
def tool_build_amm_deposit(frm: str, asset1: str, asset2: str,
                            amount1: str = None, amount2: str = None,
                            lp_token_out: str = None, mode: str = "two-asset",
                            amount: str = None):
    """Build AMMDeposit. mode: two-asset | single-asset | lp-token"""
    _FLAGS = {"two-asset": 0x00100000, "single-asset": 0x00080000, "lp-token": 0x00010000}
    flags = _FLAGS.get(mode, 0x00100000)
    kwargs = dict(account=frm, asset=_parse_asset(asset1), asset2=_parse_asset(asset2), flags=flags)
    if amount and not amount1:
        amount1 = amount
    if amount1:
        kwargs["amount"] = _parse_amount_for_amm(amount1)
    if amount2:
        kwargs["amount2"] = _parse_amount_for_amm(amount2)
    if lp_token_out:
        parts = lp_token_out.split(":", 2)
        if len(parts) == 3:
            kwargs["lp_token_out"] = IssuedCurrencyAmount(currency=parts[0], issuer=parts[1], value=parts[2])
    tx = AMMDeposit(**kwargs)
    note_out("# AMMDeposit TX JSON - signer-ready JSON - paste into Xaman Developer tab")
    json_tx_out(tx)


# --- TOOL 37: AMM Withdraw ---
def tool_build_amm_withdraw(frm: str, asset1: str, asset2: str,
                             amount1: str = None, amount2: str = None,
                             lp_token_in: str = None, mode: str = "two-asset",
                             lp_amount: str = None):
    """Build AMMWithdraw. mode: two-asset | single-asset | lp-token | withdraw-all"""
    _FLAGS = {
        "two-asset": 0x00100000, "single-asset": 0x00080000,
        "lp-token": 0x00010000, "withdraw-all": 0x00020000,
    }
    flags = _FLAGS.get(mode, 0x00100000)
    kwargs = dict(account=frm, asset=_parse_asset(asset1), asset2=_parse_asset(asset2), flags=flags)
    if lp_amount and not lp_token_in:
        lp_token_in = lp_amount
    if amount1:
        kwargs["amount"] = _parse_amount_for_amm(amount1)
    if amount2:
        kwargs["amount2"] = _parse_amount_for_amm(amount2)
    if lp_token_in:
        parts = lp_token_in.split(":", 2)
        if len(parts) == 3:
            kwargs["lp_token_in"] = IssuedCurrencyAmount(currency=parts[0], issuer=parts[1], value=parts[2])
    tx = AMMWithdraw(**kwargs)
    note_out("# AMMWithdraw TX JSON - signer-ready JSON - paste into Xaman Developer tab")
    json_tx_out(tx)


# --- TOOL 38: AMM Vote ---
def tool_build_amm_vote(frm: str, asset1: str, asset2: str, trading_fee: str):
    """Build AMMVote to vote on trading fee. trading_fee: 0-1000 (1000 = 1%)"""
    tx = AMMVote(
        account=frm,
        asset=_parse_asset(asset1),
        asset2=_parse_asset(asset2),
        trading_fee=int(trading_fee),
    )
    note_out("# AMMVote TX JSON - signer-ready JSON - paste into Xaman Developer tab")
    json_tx_out(tx)


# --- TOOL 39: AMM Bid ---
def tool_build_amm_bid(frm: str, asset1: str, asset2: str,
                        bid_min: str = None, bid_max: str = None,
                        auth_accounts: str = None):
    """Build AMMBid for auction slot. auth_accounts: comma-separated rADDR list"""
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
    note_out("# AMMBid TX JSON - signer-ready JSON - paste into Xaman Developer tab")
    json_tx_out(tx)


# --- TOOL 40: Signer List Set ---
def tool_build_signer_list_set(frm: str, quorum: str, signers: str = None):
    """Build SignerListSet. signers: comma-separated rADDR:WEIGHT pairs"""
    signer_entries = []
    if signers:
        for pair in signers.split(","):
            pair = pair.strip()
            if ":" in pair:
                addr, weight = pair.rsplit(":", 1)
                signer_entries.append(SignerEntry(account=addr.strip(), signer_weight=int(weight.strip())))
    kwargs: dict = dict(account=frm, signer_quorum=int(quorum))
    if signer_entries:
        kwargs["signer_entries"] = signer_entries
    tx = SignerListSet(**kwargs)
    note_out("# SignerListSet TX JSON - signer-ready JSON - paste into Xaman Developer tab")
    json_tx_out(tx)


# --- TOOL 41: MPT Issuance Create ---
def tool_build_mpt_issuance_create(frm: str, asset_scale: str = None,
                                    maximum_amount: str = None, transfer_fee: str = None,
                                    flags: str = None):
    """Build MPTokenIssuanceCreate (XLS-33 Multi-Purpose Token)."""
    kwargs: dict = dict(account=frm)
    if asset_scale is not None:
        kwargs["asset_scale"] = int(asset_scale)
    if maximum_amount is not None:
        kwargs["maximum_amount"] = maximum_amount
    if transfer_fee is not None:
        kwargs["transfer_fee"] = int(transfer_fee)
        # Auto-set tfMPTCanTransfer flag when transfer_fee is provided
        if flags is None:
            flags = 0
        flags = int(flags, 16) if str(flags).startswith("0x") else int(flags)
        flags |= 0x20  # tfMPTCanTransfer
    if flags is not None:
        kwargs["flags"] = int(flags, 16) if str(flags).startswith("0x") else int(flags)
    tx = MPTokenIssuanceCreate(**kwargs)
    note_out("# MPTokenIssuanceCreate TX JSON - signer-ready JSON - paste into Xaman Developer tab")
    json_tx_out(tx)


# --- TOOL 42: MPT Authorize ---
def tool_build_mpt_authorize(frm: str, mpt_issuance_id: str, holder: str = None,
                              flags: str = None):
    """Build MPTokenAuthorize. Issuer uses --holder to authorize; holder omits it."""
    kwargs: dict = dict(account=frm, mptoken_issuance_id=mpt_issuance_id)
    if holder:
        kwargs["holder"] = holder
    if flags is not None:
        kwargs["flags"] = int(flags)
    tx = MPTokenAuthorize(**kwargs)
    note_out("# MPTokenAuthorize TX JSON - signer-ready JSON - paste into Xaman Developer tab")
    json_tx_out(tx)


# --- TOOL 43: Oracle Set ---
def tool_build_set_oracle(frm: str, oracle_doc_id: str, provider: str,
                           asset_class: str, last_update_time: str,
                           price_data: str = None, uri: str = None):
    """Build OracleSet (XLS-47). price_data: BASE/QUOTE:PRICE:SCALE,... (comma-separated). last_update_time is Unix epoch seconds."""
    if not price_data:
        print("Error: --price-data is required for OracleSet (XLS-47).")
        print("Format: BASE/QUOTE:PRICE:SCALE  (comma-separated for multiple feeds)")
        print("Example: --price-data XRP/USD:50000:6,BTC/USD:65000000:2")
        return
    price_data_series = []
    for entry in price_data.split(","):
        entry = entry.strip()
        parts = entry.split(":")
        if len(parts) >= 3:
            pair, price_val, scale = parts[0], parts[1], parts[2]
            pair_parts = pair.split("/")
            base_asset = pair_parts[0] if len(pair_parts) >= 1 else pair
            quote_asset = pair_parts[1] if len(pair_parts) >= 2 else "USD"
            price_data_series.append(PriceData(
                base_asset=base_asset,
                quote_asset=quote_asset,
                asset_price=int(price_val),
                scale=int(scale),
            ))
    if not price_data_series:
        print("Error: --price-data could not be parsed. Use BASE/QUOTE:PRICE:SCALE format.")
        return
    kwargs: dict = dict(
        account=frm,
        oracle_document_id=int(oracle_doc_id),
        provider=provider,
        asset_class=asset_class,
        last_update_time=int(last_update_time),
        price_data_series=price_data_series,
    )
    if uri:
        kwargs["uri"] = uri
    tx = OracleSet(**kwargs)
    note_out("# OracleSet TX JSON - signer-ready JSON - paste into Xaman Developer tab")
    json_tx_out(tx)


# --- TOOL 44: Credential Create ---
def tool_build_credential_create(frm: str, subject: str, credential_type: str,
                                  uri: str = None, expiration: str = None):
    """Build CredentialCreate (XLS-70). credential_type: hex-encoded type string."""
    kwargs: dict = dict(account=frm, subject=subject, credential_type=credential_type)
    if uri:
        kwargs["uri"] = uri
    if expiration:
        kwargs["expiration"] = int(expiration)
    tx = CredentialCreate(**kwargs)
    note_out("# CredentialCreate TX JSON - signer-ready JSON - paste into Xaman Developer tab")
    json_tx_out(tx)


# --- TOOL 45: Credential Accept ---
def tool_build_credential_accept(frm: str, issuer: str, credential_type: str):
    """Build CredentialAccept. Subject accepts a credential issued to them."""
    tx = CredentialAccept(account=frm, issuer=issuer, credential_type=credential_type)
    note_out("# CredentialAccept TX JSON - signer-ready JSON - paste into Xaman Developer tab")
    json_tx_out(tx)


# --- TOOL 46: Credential Delete ---
def tool_build_credential_delete(frm: str, credential_type: str,
                                  subject: str = None, issuer: str = None):
    """Build CredentialDelete. --subject if account is issuer; --issuer if account is subject."""
    kwargs: dict = dict(account=frm, credential_type=credential_type)
    if subject:
        kwargs["subject"] = subject
    if issuer:
        kwargs["issuer"] = issuer
    tx = CredentialDelete(**kwargs)
    note_out("# CredentialDelete TX JSON - signer-ready JSON - paste into Xaman Developer tab")
    json_tx_out(tx)


# --- TOOL 47: Cross-Currency Payment ---
def tool_build_cross_currency_payment(frm: str, to: str, deliver: str, send_max: str,
                                       paths: str = None, dest_tag: str = None,
                                       currency: str = None, issuer: str = None):
    """Build cross-currency Payment. deliver: CUR:ISSUER:VALUE  send_max: XRP:DROPS or CUR:ISSUER:VALUE"""
    d_parts = deliver.split(":", 2)
    if currency and currency.upper() != "XRP" and issuer and ":" not in deliver and "/" not in deliver:
        amount = IssuedCurrencyAmount(currency=currency.upper(), issuer=issuer, value=deliver)
    elif d_parts[0].upper() == "XRP":
        amount = d_parts[1] if len(d_parts) >= 2 else deliver
    elif len(d_parts) == 3:
        amount = IssuedCurrencyAmount(currency=d_parts[0], issuer=d_parts[1], value=d_parts[2])
    else:
        amount = deliver

    sm_parts = send_max.split(":", 2)
    if sm_parts[0].upper() == "XRP":
        send_max_val = sm_parts[1] if len(sm_parts) >= 2 else send_max
    elif len(sm_parts) == 3:
        send_max_val = IssuedCurrencyAmount(currency=sm_parts[0], issuer=sm_parts[1], value=sm_parts[2])
    else:
        send_max_val = send_max

    kwargs: dict = dict(account=frm, destination=to, amount=amount, send_max=send_max_val)
    if paths:
        try:
            kwargs["paths"] = json.loads(paths)
        except Exception:
            print(f"Warning: could not parse --paths JSON: {paths}")
    if dest_tag:
        kwargs["destination_tag"] = int(dest_tag)
    tx = Payment(**kwargs)
    note_out("# Cross-Currency Payment TX JSON - signer-ready JSON - paste into Xaman Developer tab")
    json_tx_out(tx)


# --- TOOL 48: Batch ---
def tool_build_batch(frm: str, inner_txs: str = None, flags: str = None, txns: str = None):
    """Build Batch transaction (XLS-56). inner_txs: JSON array of pre-built TX dicts."""
    inner_txs = inner_txs or txns
    try:
        raw_txs = json.loads(inner_txs)
    except Exception as e:
        json_out({"Error": "InvalidJSON", "Message": f"Error parsing --inner-txs JSON: {e}"})
        return
    if not isinstance(raw_txs, list):
        json_out({"Error": "InvalidBatch", "Message": "--inner-txs must be a JSON array of transaction objects"})
        return
    if len(raw_txs) < 2 or len(raw_txs) > 8:
        json_out({"Error": "InvalidBatch", "Message": f"Batch requires 2-8 inner transactions, got {len(raw_txs)}"})
        return

    # Build a lookup from TransactionType string → model class
    TX_MODELS = {
        "Payment": Payment,
        "TrustSet": TrustSet,
        "OfferCreate": OfferCreate,
        "NFTokenMint": NFTokenMint,
        "AMMCreate": AMMCreate,
        "AMMDeposit": AMMDeposit,
        "AMMWithdraw": AMMWithdraw,
        "AMMVote": AMMVote,
        "AMMBid": AMMBid,
        "Clawback": Clawback,
        "AccountSet": AccountSet,
        "SignerListSet": SignerListSet,
        "EscrowCreate": EscrowCreate,
        "EscrowFinish": EscrowFinish,
        "EscrowCancel": EscrowCancel,
        "CheckCreate": CheckCreate,
        "CheckCash": CheckCash,
        "CheckCancel": CheckCancel,
        "PaymentChannelCreate": PaymentChannelCreate,
        "PaymentChannelFund": PaymentChannelFund,
        "PaymentChannelClaim": PaymentChannelClaim,
        "SetRegularKey": SetRegularKey,
        "AccountDelete": AccountDelete,
        "DepositPreauth": DepositPreauth,
        "TicketCreate": TicketCreate,
        "OracleSet": OracleSet,
        "MPTokenIssuanceCreate": MPTokenIssuanceCreate,
        "MPTokenAuthorize": MPTokenAuthorize,
        "CredentialCreate": CredentialCreate,
        "CredentialAccept": CredentialAccept,
        "CredentialDelete": CredentialDelete,
        "NFTokenCreateOffer": NFTokenCreateOffer,
        "Batch": Batch,
    }

    wrapped = []
    for raw in raw_txs:
        tx_type = raw.get("TransactionType")
        model_class = TX_MODELS.get(tx_type)
        if model_class is None:
            json_out({"Error": "UnsupportedTransactionType", "Message": f"Unknown or unsupported TransactionType '{tx_type}'"})
            return
        # Convert XRPL JSON field names to snake_case xrpl-py kwargs
        FIELD_MAP = {
            "Account": "account", "Destination": "destination", "Amount": "amount",
            "Fee": "fee", "Sequence": "sequence", "Flags": "flags",
            "SigningPubKey": "signing_pub_key", "LastLedgerSequence": "last_ledger_sequence",
            "SourceTag": "source_tag", "TicketSequence": "ticket_sequence",
            "Memos": "memos", "Signers": "signers",
            "Owner": "owner", "OfferSequence": "offer_sequence",
            "CheckID": "check_id", "Channel": "channel",
            "SettleDelay": "settle_delay", "PublicKey": "public_key",
            "LimitAmount": "limit_amount", "TakerGets": "taker_gets", "TakerPays": "taker_pays",
            "NFTokenTaxon": "nftoken_taxon", "URI": "uri", "TransferFee": "transfer_fee",
            "Issuer": "issuer", "Subject": "subject", "CredentialType": "credential_type",
            "MPTokenIssuanceID": "mptoken_issuance_id",
            "OracleDocumentID": "oracle_document_id",
            "Provider": "provider", "AssetClass": "asset_class",
            "LastUpdateTime": "last_update_time",
            "PriceDataSeries": "price_data_series",
            "RawTransactions": "raw_transactions",
            "DestinationTag": "destination_tag", "InvoiceID": "invoice_id",
            "Expiration": "expiration", "CancelAfter": "cancel_after",
            "FinishAfter": "finish_after", "Condition": "condition",
            "Fulfillment": "fulfillment",
            "Authorize": "authorize", "Unauthorize": "unauthorize",
            "RegularKey": "regular_key",
            "Asset": "asset", "Asset2": "asset2",
            "Amount2": "amount2", "LPTokenOut": "lp_token_out",
            "LPTokenIn": "lp_token_in", "TradingFee": "trading_fee",
            "BidMin": "bid_min", "BidMax": "bid_max", "AuthAccounts": "auth_accounts",
            "SignerQuorum": "signer_quorum", "SignerEntries": "signer_entries",
            "AssetScale": "asset_scale", "MaximumAmount": "maximum_amount",
            "RawTransaction": "raw_transaction",
            "HookOn": "hook_on",
        }
        kwargs = {}
        for k, v in raw.items():
            if k == "TransactionType":
                continue
            mapped = FIELD_MAP.get(k, k[0].lower() + k[1:] if k else k)
            kwargs[mapped] = v
        # Mark inner tx with required Batch flags and defaults
        kwargs.setdefault("flags", 0)
        kwargs["flags"] |= 0x40000000  # tfInnerBatchTxn
        kwargs.setdefault("fee", "0")
        kwargs.setdefault("signing_pub_key", "")
        try:
            wrapped.append(model_class(**kwargs))
        except Exception as e:
            json_out({"Error": "InvalidInnerTransaction", "Message": f"Error validating inner {tx_type}: {e}"})
            return

    kwargs: dict = dict(account=frm, raw_transactions=wrapped)
    if flags is not None:
        kwargs["flags"] = int(flags)
    tx = Batch(**kwargs)
    note_out("# Batch TX JSON - signer-ready JSON - paste into Xaman Developer tab (each inner tx must be signed separately)")
    json_tx_out(tx)


if __name__ == "__main__":
    main()
