#!/usr/bin/env python3
"""Shared utilities for all xrpl-hermes tool modules."""
import json, sys, os, hashlib
from typing import Optional, Dict, Any, List
from urllib.parse import quote
from datetime import datetime, timezone
from decimal import Decimal
import time

# --- xrpl-py imports (with helpful error) ---
try:
    import xrpl
    from xrpl.models.requests import AccountInfo, AccountLines, AccountObjects, AccountTx, \
        BookOffers, NFTInfo, LedgerEntry, ServerInfo, Ledger, ServerState, RipplePathFind, Tx, \
        NFTSellOffers, NFTBuyOffers
    from xrpl.clients import JsonRpcClient
    from xrpl.utils import drops_to_xrp, xrp_to_drops
    from xrpl.models.transactions import Payment, TrustSet, OfferCreate, NFTokenMint, \
        NFTokenCreateOffer, NFTokenAcceptOffer, NFTokenCancelOffer, NFTokenBurn, \
        AMMCreate, AMMDeposit, AMMWithdraw, AMMVote, AMMBid, \
        AccountSet, SignerListSet, EscrowCreate, TicketCreate, \
        EscrowFinish, EscrowCancel, CheckCreate, CheckCancel, CheckCash, \
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
    parts = arg.split(":", 2)
    if len(parts) == 1:
        return parts[0], None, None
    elif len(parts) == 2:
        return parts[0], None, parts[1]
    else:
        return parts[0], parts[1], parts[2]

def make_amount(currency: str, issuer: Optional[str], value: str) -> dict:
    if currency.upper() == "XRP" and not issuer:
        return value if value is not None else currency
    return {"currency": currency, "issuer": issuer, "value": value}

def json_out(obj):
    print(json.dumps(obj, indent=2, default=str))

def usage_out(command: str, usage: str):
    json_out({"Error": "UsageError", "Command": command, "Usage": usage})

def note_out(message: str):
    if not os.environ.get("XRPL_TOOLS_QUIET"):
        print(message, file=sys.stderr)

def tx_to_xrpl_json(tx):
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
    parsed = parse_amount_arg(arg)
    if not isinstance(parsed, str) or _is_numeric_text(parsed):
        return parsed
    parts = arg.split(":", 2)
    if parts[0].upper() == "XRP":
        return parts[1] if len(parts) >= 2 else arg
    if len(parts) == 3:
        return IssuedCurrencyAmount(currency=parts[0].upper(), issuer=parts[1], value=parts[2])
    raise ValueError(f"Invalid amount '{arg}'. Use 'XRP:DROPS' or 'CUR:ISSUER:VALUE'")

# --- Dispatch Helpers ---

def _parse_build_kwargs(keys: list) -> dict:
    kwargs = {}
    for i in range(2, len(sys.argv) - 1, 2):
        k = sys.argv[i].lstrip("--").replace("-", "_")
        v = sys.argv[i + 1]
        if k in keys:
            kwargs[k] = v
    return kwargs

_AMENDMENT_CACHE = {"ts": 0.0, "data": None}

AMENDMENT_ENDPOINTS = [
    "https://s1.ripple.com:51234",
    "https://s2.ripple.com:51234",
]

FEATURE_ALIASES = {
    "MPT": "MPTokensV1",
    "MPTS": "MPTokensV1",
    "MPTokenIssuanceCreate": "MPTokensV1",
    "MPTokenAuthorize": "MPTokensV1",
    "Oracle": "PriceOracle",
    "OracleSet": "PriceOracle",
    "Batch": "Batch",
    "Credentials": "Credentials",
    "CredentialCreate": "Credentials",
    "CredentialAccept": "Credentials",
    "CredentialDelete": "Credentials",
    "AMMClawback": "AMMClawback",
    "DID": "DID",
    "XRPFees": "XRPFees",
}


def _fetch_features() -> Dict[str, Any]:
    """Fetch live amendment/feature status from public XRPL mainnet nodes."""
    now = time.time()
    if _AMENDMENT_CACHE["data"] is not None and now - _AMENDMENT_CACHE["ts"] < 300:
        return _AMENDMENT_CACHE["data"]
    last_err = None
    for ep in AMENDMENT_ENDPOINTS:
        try:
            import httpx
            resp = httpx.post(ep, json={"method": "feature", "params": [{}]}, timeout=20)
            payload = resp.json()
            features = payload.get("result", {}).get("features", {})
            if features:
                data = {"endpoint": ep, "features": features, "fetched_at": datetime.now(timezone.utc).isoformat()}
                _AMENDMENT_CACHE["data"] = data
                _AMENDMENT_CACHE["ts"] = now
                return data
        except Exception as e:
            last_err = e
    raise RuntimeError(f"Could not fetch XRPL amendment status: {last_err}")


def list_amendments() -> Dict[str, Any]:
    data = _fetch_features()
    buckets = {"enabled": [], "supported_not_enabled": [], "vetoed": [], "unsupported": []}
    for fid, feat in data["features"].items():
        rec = {
            "name": feat.get("name") or fid,
            "id": fid,
            "enabled": bool(feat.get("enabled")),
            "supported": bool(feat.get("supported")),
            "vetoed": bool(feat.get("vetoed")),
        }
        if rec["enabled"]:
            buckets["enabled"].append(rec)
        elif rec["vetoed"]:
            buckets["vetoed"].append(rec)
        elif rec["supported"]:
            buckets["supported_not_enabled"].append(rec)
        else:
            buckets["unsupported"].append(rec)
    for key in buckets:
        buckets[key] = sorted(buckets[key], key=lambda x: x["name"].lower())
    return {
        "Network": "XRPL Mainnet",
        "Endpoint": data["endpoint"],
        "FetchedAt": data["fetched_at"],
        "Counts": {k: len(v) for k, v in buckets.items()},
        **buckets,
    }


def get_amendment_status(name_or_id: str) -> Dict[str, Any]:
    wanted = FEATURE_ALIASES.get(name_or_id, name_or_id).lower()
    data = _fetch_features()
    for fid, feat in data["features"].items():
        name = feat.get("name") or fid
        if wanted in (name.lower(), fid.lower()) or wanted == fid.lower()[:16]:
            return {
                "Network": "XRPL Mainnet",
                "Endpoint": data["endpoint"],
                "FetchedAt": data["fetched_at"],
                "Name": name,
                "ID": fid,
                "Enabled": bool(feat.get("enabled")),
                "Supported": bool(feat.get("supported")),
                "Vetoed": bool(feat.get("vetoed")),
            }
    return {"Error": "UnknownAmendment", "Query": name_or_id}


def warn_if_amendment_not_enabled(feature_name: str):
    """Emit an honest warning for amendment-dependent builders.

    Builder commands still output JSON because teams may target devnet/testnet or
    prepare payloads ahead of activation. The warning prevents accidental
    mainnet claims when a feature is only supported/in voting.
    """
    status = get_amendment_status(feature_name)
    if status.get("Error"):
        note_out(f"# Amendment check: {feature_name} not found on live mainnet feature list. Treat output as build-only until verified.")
        return status
    if not status.get("Enabled"):
        note_out(
            f"# WARNING: {status['Name']} is not enabled on XRPL mainnet "
            f"(supported={status.get('Supported')}, vetoed={status.get('Vetoed')}). "
            "This payload is build-only unless you are targeting a network where the amendment is active."
        )
    else:
        note_out(f"# Amendment check: {status['Name']} is enabled on XRPL mainnet.")
    return status


def _dispatch_build(min_pairs: int, fn):
    kwargs = {}
    for i in range(2, len(sys.argv) - 1, 2):
        k = sys.argv[i].lstrip("--").replace("-", "_")
        v = sys.argv[i + 1]
        if k in ('taxon', 'transfer_fee', 'flags', 'fee', 'settle_delay', 'trading_fee',
                 'oracle_doc_id', 'last_update_time', 'expiration', 'cancel_after',
                 'finish_after', 'offer_sequence', 'quorum', 'scale', 'asset_scale',
                 'count', 'tick_size', 'transfer_rate', 'set_flag', 'clear_flag'):
            try: v = int(v)
            except: pass
        elif v.replace('.','',1).lstrip('-').isdigit() and '.' in v:
            try: v = float(v)
            except: pass
        kwargs[k] = v
    if len(kwargs) < min_pairs:
        print(f"Need at least {min_pairs} arguments for {sys.argv[1]}")
        return
    if 'from' in kwargs:
        kwargs['frm'] = kwargs.pop('from')
    try:
        fn(**kwargs)
    except Exception as e:
        json_out({"Error": e.__class__.__name__, "Message": str(e), "Command": sys.argv[1]})

def _dispatch_path_find():
    if len(sys.argv) < 6:
        print("Usage: path-find rSENDER rDEST AMOUNT CUR:ISSUER")
        return
    src, dest, amount = sys.argv[2], sys.argv[3], sys.argv[4]
    cur_parts = sys.argv[5].split(":", 1)
    cur = cur_parts[0]
    iss = cur_parts[1] if len(cur_parts) > 1 else None
    # Import here to avoid circular deps
    from . import payments
    payments.tool_path_find(src, dest, amount, cur, iss)
