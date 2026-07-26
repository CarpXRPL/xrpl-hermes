#!/usr/bin/env python3
"""Shared utilities for all xrpl-hermes tool modules."""
import json, sys, os, hashlib, re
from typing import Optional, Dict, Any, List
from urllib.parse import quote
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
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
        CredentialCreate, CredentialAccept, CredentialDelete, Batch, Memo
    from xrpl.models.transactions.signer_list_set import SignerEntry
    from xrpl.models.transactions.oracle_set import PriceData
    from xrpl.models.auth_account import AuthAccount
    from xrpl.models.currencies import XRP as XRPCurrency, IssuedCurrency
    from xrpl.models.amounts import IssuedCurrencyAmount
    from xrpl.core.binarycodec.exceptions import XRPLBinaryCodecException
    from xrpl.core.binarycodec.types.amount import verify_iou_value as _xrpl_verify_iou_value
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
    if currency == "XRP":
        if issuer:
            raise ValueError("XRP does not take an issuer")
        return value if value is not None else currency
    if not issuer:
        raise ValueError(f"issued currency {currency!r} requires an issuer")
    return {
        "currency": normalize_currency_code(currency),
        "issuer": validate_xrpl_address(issuer, "issuer"),
        "value": value,
    }

def to_uint32(value, name: str = "tag"):
    """Coerce a CLI-supplied tag to a UInt32 int, or None. Raises on out-of-range."""
    if value is None or value == "":
        return None
    try:
        iv = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be an integer (got {value!r})")
    if not (0 <= iv <= 0xFFFFFFFF):
        raise ValueError(f"{name} must be a UInt32 (0..4294967295)")
    return iv

def build_memos(memo):
    """Turn plain-text memo(s) into XRPL Memo objects with hex-encoded MemoData.

    Accepts a single string or a list of strings. Memos are an on-chain audit
    trail for agent-initiated transactions; the ledger stores MemoData as hex.
    """
    if not memo:
        return None
    texts = memo if isinstance(memo, (list, tuple)) else [memo]
    memos = []
    for t in texts:
        if t is None or t == "":
            continue
        memos.append(Memo(memo_data=str(t).encode("utf-8").hex().upper()))
    return memos or None

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
        if "reserve_base_xrp" not in ledger or "reserve_inc_xrp" not in ledger:
            raise RuntimeError("validated ledger did not return reserve settings")
        return Decimal(str(ledger["reserve_base_xrp"])), Decimal(str(ledger["reserve_inc_xrp"]))
    except Exception as exc:
        raise RuntimeError("unable to derive current reserve settings from the selected XRPL server") from exc

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

XRP_DROPS_HINT = (
    "XRP amounts are integer drops (1 XRP = 1000000 drops): pass 1000000, not 1.0. "
    "For an issued currency use CUR:ISSUER:VALUE."
)

_PLAIN_ISSUED_VALUE_RE = re.compile(r"^-?[0-9]+(?:\.[0-9]+)?$")

def validate_issued_currency_value(value: str) -> str:
    """Return an XRPL-binary-codec-valid issued value without changing its text."""
    if not isinstance(value, str) or not _PLAIN_ISSUED_VALUE_RE.fullmatch(value):
        raise ValueError(
            f"Invalid issued currency value '{value}'. Use plain decimal notation "
            "within XRPL's issued-currency precision and exponent limits."
        )
    try:
        _xrpl_verify_iou_value(value)
    except (XRPLBinaryCodecException, InvalidOperation, ValueError) as exc:
        raise ValueError(
            f"Invalid issued currency value '{value}': not representable by the XRPL binary codec."
        ) from exc
    return value

def _is_drops_text(arg) -> bool:
    """True for an integer drops amount. XRP has no unit smaller than a drop."""
    return isinstance(arg, str) and arg.isascii() and arg.isdigit()

XRP_MAX_DROPS = 100_000_000_000_000_000

def validate_drops_amount(value, field: str = "amount") -> str:
    """Return a nonnegative integer drops string for an XRP-only field, or raise."""
    if not _is_drops_text(value):
        raise ValueError(f"Invalid XRP {field} '{value}'. {XRP_DROPS_HINT}")
    if int(value) > XRP_MAX_DROPS:
        raise ValueError(
            f"Invalid XRP {field} '{value}': maximum is {XRP_MAX_DROPS} drops."
        )
    return value

def validate_positive_drops_amount(value, field: str = "amount") -> str:
    """Return a strictly positive integer drops string, or raise."""
    text = validate_drops_amount(value, field)
    if int(text) <= 0:
        raise ValueError(f"Invalid XRP {field} '{value}': amount must be positive.")
    return text

def validate_nonnegative_issued_value(value: str, field: str = "amount") -> str:
    """Validate an issued value for transaction fields that permit zero."""
    text = validate_issued_currency_value(value)
    if Decimal(text) < 0:
        raise ValueError(f"Invalid {field} '{value}': amount must be nonnegative.")
    return text

def validate_positive_issued_value(value: str, field: str = "amount") -> str:
    """Validate an issued value that must be strictly positive."""
    text = validate_issued_currency_value(value)
    if Decimal(text) <= 0:
        raise ValueError(f"Invalid {field} '{value}': amount must be positive.")
    return text

def validate_positive_amount(amount, field: str = "amount"):
    """Validate a parsed XRP or issued amount as strictly positive."""
    value = amount if isinstance(amount, str) else amount.value
    if Decimal(value) <= 0:
        raise ValueError(f"Invalid {field} '{value}': amount must be positive.")
    return amount

def validate_xrpl_address(value, field: str = "address") -> str:
    """Return a classic address valid in a raw transaction AccountID field.

    X-addresses embed a tag and network bit. Accepting one without decoding it
    would discard those semantics when emitting raw transaction JSON.
    """
    from xrpl.core.addresscodec import is_valid_classic_address
    if isinstance(value, str) and is_valid_classic_address(value):
        return value
    raise ValueError(f"Invalid XRPL {field} '{value}': expected a classic r-address.")

def parse_amount_arg(arg: str):
    if "/" in arg:
        value, asset = arg.split("/", 1)
        if not value or asset.count(":") != 1:
            raise ValueError(f"Invalid issued currency value '{arg}'. Use VALUE/CUR:ISSUER.")
    slash = _parse_value_slash_asset(arg)
    if slash:
        cur, iss, val = slash
        return IssuedCurrencyAmount(
            currency=normalize_currency_code(cur),
            issuer=validate_xrpl_address(iss, "issuer"),
            value=validate_nonnegative_issued_value(val),
        )
    if _is_drops_text(arg):
        return validate_drops_amount(arg)
    parts = arg.split(":", 2)
    if parts[0] == "XRP":
        if len(parts) != 2:
            raise ValueError(f"Invalid XRP amount '{arg}'. {XRP_DROPS_HINT}")
        drops = parts[1]
        if _is_drops_text(drops):
            return validate_drops_amount(drops)
        raise ValueError(f"Invalid XRP amount '{arg}'. {XRP_DROPS_HINT}")
    if len(parts) == 3:
        return IssuedCurrencyAmount(
            currency=normalize_currency_code(parts[0]),
            issuer=validate_xrpl_address(parts[1], "issuer"),
            value=validate_nonnegative_issued_value(parts[2]),
        )
    raise ValueError(f"Invalid amount '{arg}'. {XRP_DROPS_HINT}")

def _parse_asset(arg: str):
    """Legacy asset parser. `parse_asset_normalized` is the live path for every
    caller; this is kept only so the normalization rule has one definition."""
    if _is_numeric_text(arg):
        return XRPCurrency()
    slash = _parse_value_slash_asset(arg)
    if slash:
        currency, issuer, _value = slash
        return IssuedCurrency(currency=normalize_currency_code(currency), issuer=issuer)
    parts = arg.split(":", 2)
    if parts[0] == "XRP":
        return XRPCurrency()
    if len(parts) >= 2:
        return IssuedCurrency(currency=normalize_currency_code(parts[0]), issuer=parts[1])
    raise ValueError(f"Invalid asset '{arg}'. Use 'XRP' or 'CUR:ISSUER'")

def normalize_currency_code(code: str) -> str:
    """Normalize a currency code to its on-ledger form.

    3-char ISO-style codes pass through **unchanged**: they occupy three raw
    bytes on-ledger and are case-sensitive, so `usd` and `USD` are different
    assets and uppercasing one silently retargets the transaction at the other.
    40-char hex passes through uppercased (hex case is not significant); 4-20
    char ASCII symbols become the 160-bit hex code (zero-padded), e.g.
    RLUSD -> 524C555344...0000, because there is no 3-byte slot to hold them.
    """
    code = (code or "").strip()
    if not code:
        raise ValueError("Empty currency code")
    if len(code) == 3:
        permitted = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789?!@#$%^&*<>(){}[]|")
        if any(char not in permitted for char in code):
            raise ValueError(
                f"Invalid currency '{code}': standard codes require 3 permitted ASCII characters"
            )
        if code != "XRP" and code.upper() == "XRP":
            # xrpl-py rejects case variants in its 3-character model path even
            # though consensus reserves only exact uppercase XRP. This is the
            # equivalent 160-bit standard-code representation and preserves
            # the original three bytes on-ledger.
            return (b"\x00" * 12 + code.encode("ascii") + b"\x00" * 5).hex().upper()
        return code
    if len(code) == 40:
        try:
            bytes.fromhex(code)
        except ValueError:
            raise ValueError(f"Invalid currency '{code}': 40-char codes must be hex")
        return code.upper()
    if 4 <= len(code) <= 20:
        try:
            raw = code.encode("ascii")
        except UnicodeEncodeError:
            raise ValueError(f"Currency '{code}' must be ASCII to normalize to 160-bit hex")
        return raw.hex().upper().ljust(40, "0")
    raise ValueError(f"Invalid currency '{code}': use a 3-char code, 4-20 char symbol, or 40-char hex")

def parse_asset_normalized(arg: str):
    """Like _parse_asset but normalizes 4+ char symbols to 160-bit hex (e.g. RLUSD:rISS)."""
    parts = arg.split(":", 1)
    if parts[0] == "XRP":
        if len(parts) == 1:
            return XRPCurrency()
        raise ValueError("XRP cannot have an issuer")
    if len(parts) == 2:
        return IssuedCurrency(
            currency=normalize_currency_code(parts[0]),
            issuer=validate_xrpl_address(parts[1], "issuer"),
        )
    raise ValueError(f"Invalid asset '{arg}'. Use 'XRP' or 'CUR:ISSUER'")

def _parse_amount_for_amm(arg: str):
    """AMM amounts use the same grammar as every other amount.

    The former fallback re-parsed the argument with `.upper()` applied to the
    currency; it was unreachable (`parse_amount_arg` either returns a drops
    string, returns an IssuedCurrencyAmount, or raises) and case-retargeting.
    """
    return parse_amount_arg(arg)

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
    command = sys.argv[1] if len(sys.argv) > 1 else "build"
    argv = sys.argv[2:]
    kwargs = {}
    # Arguments are --flag VALUE pairs. The old range stopped one short of the
    # end, so a trailing flag with no value was dropped without a word and the
    # builder emitted a payload missing what the operator asked for.
    for i in range(0, len(argv), 2):
        flag = argv[i]
        if not flag.startswith("--"):
            usage_out(command, f"Unexpected argument '{flag}' for {command}: "
                               "arguments are --flag VALUE pairs.")
            return
        if i + 1 >= len(argv):
            usage_out(command, f"Missing value after '{flag}' for {command}: "
                               "arguments are --flag VALUE pairs.")
            return
        k = flag.lstrip("--").replace("-", "_")
        v = argv[i + 1]
        if k in ('taxon', 'transfer_fee', 'flags', 'fee', 'settle_delay', 'trading_fee',
                 'oracle_doc_id', 'last_update_time', 'expiration', 'cancel_after',
                 'finish_after', 'offer_sequence', 'quorum', 'scale', 'asset_scale',
                 'count', 'tick_size', 'transfer_rate', 'set_flag', 'clear_flag'):
            try: v = int(v)
            except: pass
        # Everything else stays the operator's exact text. The dispatcher has no
        # currency context, so it cannot tell drops from an issued decimal value;
        # float() truncated exact decimals and re-rendered extremes in exponent
        # notation, which is not a valid XRPL amount. Amount validation belongs
        # in the builders, which know the currency.
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
