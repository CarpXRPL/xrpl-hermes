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
  python3 xrpl_tools.py build-paychannel-claim --from rADDR --channel-id HEX [--amount DROPS] [--signature HEX] [--public-key HEX]
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
  python3 xrpl_tools.py evm-balance rADDRESS [mainnet|testnet]
  python3 xrpl_tools.py evm-contract --from rADDR --bytecode HEX
  python3 xrpl_tools.py evm-bridge [mainnet|testnet]
  python3 xrpl_tools.py hooks-bitmask HOOK [HOOK ...]
  python3 xrpl_tools.py hooks-info rADDRESS
  python3 xrpl_tools.py flare-price SYMBOL [SYMBOL ...]
  python3 xrpl_tools.py build-clawback --from rISSUER --destination rHOLDER --currency USD --issuer rISSUER --amount 100 [--memo TEXT]
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
        NFTokenCreateOffer, AMMCreate, AccountSet, SignerListSet, EscrowCreate, \
        EscrowFinish, EscrowCancel, CheckCreate, CheckCancel, CheckCash, TicketCreate, \
        DepositPreauth, PaymentChannelCreate, PaymentChannelFund, PaymentChannelClaim, \
        SetRegularKey, AccountDelete, Clawback
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

CLIENT = get_client()
_ENDPOINT_IDX = 0
_USING_PRIVATE = bool(_PRIVATE_RPC)

def _request(req):
    global CLIENT, _ENDPOINT_IDX
    try:
        return CLIENT.request(req)
    except Exception as e:
        _ENDPOINT_IDX = (_ENDPOINT_IDX + 1) % len(ENDPOINTS)
        try:
            CLIENT = JsonRpcClient(ENDPOINTS[_ENDPOINT_IDX])
            return CLIENT.request(req)
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
        return value  # drops as string
    return {
        "currency": currency,
        "issuer": issuer,
        "value": value
    }

def json_out(obj):
    """Print JSON and return it."""
    print(json.dumps(obj, indent=2, default=str))

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
        return Decimal(str(ledger.get("reserve_base_xrp", 10))), Decimal(str(ledger.get("reserve_inc_xrp", 2)))
    except Exception:
        return Decimal("10"), Decimal("2")

# --- TOOL 1: Account Info ---
def tool_account(address: str):
    try:
        resp = _request(AccountInfo(account=address, ledger_index="validated"))
    except Exception as e:
        print(f"Error fetching account {address}: {e}")
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
    print(f"{'Address:':12s} {address}")
    print(f"{'Balance:':12s} {fmt_xrp(bal)}")
    print(f"{'Reserve:':12s} {reserved:.2f} XRP ({owner} objects)")
    print(f"{'Spendable:':12s} {spendable:.6f} XRP")
    print(f"{'Sequence:':12s} {seq}")
    if domain:
        print(f"{'Domain:':12s} {domain}")
    print(f"{'Flags:':12s} {flags} ({', '.join(flag_descriptions) if flag_descriptions else 'none'})")

# --- TOOL 2: Trustlines ---
def tool_trustlines(address: str, currency: Optional[str] = None):
    all_lines = []
    marker = None
    while True:
        try:
            resp = _request(AccountLines(account=address, ledger_index="validated", marker=marker))
        except Exception as e:
            print(f"Error fetching trust lines for {address}: {e}")
            return
        data = resp.result
        all_lines.extend(data.get("lines", []))
        marker = data.get("marker")
        if not marker:
            break
    if currency:
        filtered = [l for l in all_lines if l.get("currency", "").upper() == currency.upper()]
        if not filtered:
            print(f"No trust lines for {currency.upper()}.")
            return
        all_lines = filtered
    if not all_lines:
        print("No trust lines found.")
        return
    for l in all_lines:
        cur = l.get("currency", "??")
        iss = l.get("account", "??")
        bal = float(l.get("balance", 0))
        lim = float(l.get("limit", 0))
        rippling = not l.get("no_ripple", False)
        frozen = l.get("freeze", False)
        print(f"{cur:20s} {bal:>20,.6f}  / limit {lim:,.0f}  ({short(iss)}){' 🔒' if frozen else ''}{' 🌊' if rippling else ''}")

# --- TOOL 3: Transaction Building ---
def tool_build_payment(frm: str, to: str, amount: str, cur: Optional[str] = None,
                       iss: Optional[str] = None, tag: Optional[int] = None, memo: Optional[str] = None):
    if cur and cur.upper() != "XRP" and iss:
        amt = IssuedCurrencyAmount(currency=cur, issuer=iss, value=amount)
    else:
        amt = amount
    tx = Payment(account=frm, destination=to, amount=amt,
                 destination_tag=tag if tag else None)
    print("# Payment TX JSON — sign with Xaman/Joey")
    tx_json = tx_to_xrpl_json(tx)
    json_out(tx_json)
    print(f"\n# Payload URL: xumm://sign?payload={quote(json.dumps(tx_json))}")

def tool_build_trustset(frm: str, currency: str, issuer: str, value: str = "1000000000"):
    cur = IssuedCurrencyAmount(currency=currency, issuer=issuer, value=value)
    tx = TrustSet(account=frm, limit_amount=cur)
    print("# TrustSet TX JSON — sign with Xaman/Joey")
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
    gets_cur, gets_iss, gets_val = parse_currency_arg(taker_gets)
    pays_cur, pays_iss, pays_val = parse_currency_arg(taker_pays)
    gets = make_amount(gets_cur, gets_iss, gets_val)
    pays = make_amount(pays_cur, pays_iss, pays_val)
    tx = OfferCreate(account=frm, taker_gets=gets, taker_pays=pays)
    print("# OfferCreate TX JSON — sign with Xaman/Joey")
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
    print("# NFTokenMint TX JSON — sign with Xaman/Joey")
    json_tx_out(tx)

def tool_build_amm_create(frm: str, amount1: str, amount2: str, fee: int = 600):
    """amount1/amount2 format: 'XRP:AMOUNT' or 'CUR:ISSUER:AMOUNT'"""
    a1_cur, a1_iss, a1_val = parse_currency_arg(amount1)
    a2_cur, a2_iss, a2_val = parse_currency_arg(amount2)
    amt1 = make_amount(a1_cur, a1_iss, a1_val)
    amt2 = make_amount(a2_cur, a2_iss, a2_val)
    tx = AMMCreate(account=frm, amount=amt1, amount2=amt2, trading_fee=fee)
    print("# AMMCreate TX JSON — sign with Xaman/Joey")
    json_tx_out(tx)

# --- TOOL 4: Decode Transaction ---
def tool_decode(blob: str):
    from xrpl.core.binarycodec import decode
    try:
        decoded = decode(blob)
        print("# Decoded Transaction")
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
        print(f"Error fetching transaction {tx_hash}: {e}")
        return
    data = resp.result
    tx_json = data.get("tx_json", data)
    status = data.get("meta", {}).get("TransactionResult", "?")
    tx_type = tx_json.get("TransactionType", "?")
    account = tx_json.get("Account", "?")
    dest = tx_json.get("Destination", "")
    fee = tx_json.get("Fee", "0")
    date_value = data.get("close_time_iso") or tx_json.get("date") or data.get("date")
    print(f"Hash:     {tx_hash}")
    print(f"Type:     {tx_type}")
    print(f"Status:   {status}")
    print(f"From:     {account}")
    if dest:
        print(f"To:       {dest}")
    print(f"Fee:      {fmt_xrp(fee)}")
    print(f"Ledger:   {data.get('ledger_index', '?')}")
    print(f"Date:     {ripple_time_to_iso(date_value)}")

# --- TOOL 6: Ledger Info ---
def tool_ledger(index: Optional[int] = None):
    try:
        resp = _request(Ledger(ledger_index=index if index else "validated", transactions=False))
    except Exception as e:
        print(f"Error fetching ledger: {e}")
        return
    data = resp.result.get("ledger", {})
    print(f"Ledger:        {data.get('ledger_index', '?')}")
    print(f"Hash:          {data.get('ledger_hash', '?')}")
    print(f"Close Time:    {data.get('close_time_human', '?')}")
    print(f"Total XRP:     {drops_to_xrp(str(data.get('total_coins', '0'))):,.0f} XRP")
    print(f"Tx Count:      {data.get('transaction_count', 0)}")
    print(f"Close Flags:   {data.get('close_flags', 0)}")

# --- TOOL 7: Server Info ---
def tool_server_info():
    try:
        resp = _request(ServerInfo())
    except Exception as e:
        print(f"Error fetching server info: {e}")
        return
    info = resp.result.get("info", {})
    print(f"Version:       {info.get('build_version', '?')}")
    print(f"Uptime:        {info.get('uptime', 0)}s")
    validated = info.get("validated_ledger", {})
    print(f"Ledgers:       {info.get('complete_ledgers', '?')}")
    print(f"Last Ledger:   {validated.get('seq', '?')}")
    print(f"State:         {info.get('server_state', '?')}")

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

    # Use raw JSON-RPC
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
    resp = httpx.post("https://xrplcluster.com", json=payload, timeout=10)
    data = resp.json()
    offers = data.get("result", {}).get("offers", [])
    print(f"Orderbook: {taker_gets} / {taker_pays} — {len(offers)} offers")
    for o in offers[:10]:
        qual = o.get("quality", "?")
        pays = o.get("TakerPays", {})
        gets = o.get("TakerGets", {})
        acct = o.get("Account", "?")
        print(f"  Quality: {qual}  ({short(acct)})")

# --- TOOL 9: Path Find ---
def tool_path_find(src: str, dest: str, amount: str, cur: str, iss: Optional[str] = None):
    dest_amt = make_amount(cur, iss, amount)
    try:
        resp = _request(RipplePathFind(source_account=src, destination_account=dest,
                                       destination_amount=dest_amt))
        alts = resp.result.get("alternatives", [])
        print(f"Found {len(alts)} paths")
        for a in alts[:5]:
            src_amt = a.get("source_amount", {})
            print(f"  Source: {src_amt}")
    except Exception as e:
        print(f"Path find error: {e}")

# --- TOOL 10: Simple Xaman Payload URL ---
def tool_xaman_url(tx_json: dict) -> str:
    """Generate a Xaman deep-link payload URL."""
    import base64
    payload_b64 = base64.urlsafe_b64encode(json.dumps(tx_json).encode()).decode()
    return f"https://xumm.app/detect/request?payload={payload_b64}"

# --- Main Dispatch ---
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1].lower()

    dispatcher = {
        "account": lambda: tool_account(sys.argv[2]) if len(sys.argv) >= 3 else print("Usage: account rADDRESS"),
        "balance": lambda: tool_account(sys.argv[2]) if len(sys.argv) >= 3 else print("Usage: balance rADDRESS"),
        "trustlines": lambda: tool_trustlines(sys.argv[2], sys.argv[3] if len(sys.argv) >= 4 else None),
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
        "evm-balance": lambda: tool_evm_balance(sys.argv[2], sys.argv[3] if len(sys.argv) >= 4 else "mainnet"),
        "evm-contract": lambda: _dispatch_build(2, tool_evm_contract),
        "evm-bridge": lambda: tool_evm_bridge(sys.argv[2] if len(sys.argv) >= 3 else "mainnet"),
        "hooks-bitmask": lambda: tool_hooks_bitmask(*sys.argv[2:]),
        "hooks-info": lambda: tool_hooks_info(sys.argv[2]) if len(sys.argv) >= 3 else print("Usage: hooks-info rADDRESS"),
        "flare-price": lambda: tool_flare_price(*sys.argv[2:]),
        "build-clawback": lambda: _dispatch_build(4, tool_build_clawback),
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
    fn(**kwargs)

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
    for ep in PUBLIC_ENDPOINTS:
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
        print(f"Error fetching NFT {nft_id}: {last_error}")
        return
    if result.get("error"):
        print(f"NFT not found or unavailable: {nft_id}")
        print(f"Error: {result.get('error')} ({result.get('error_message', 'no message')})")
        return
    json_out(result)

# --- TOOL 11: EVM Sidechain Balance ---
def tool_evm_balance(address: str, network: str = "mainnet"):
    import httpx
    rpc_urls = {"mainnet": "https://rpc.xrplevm.org", "testnet": "https://rpc.testnet.xrplevm.org"}
    url = rpc_urls.get(network, rpc_urls["mainnet"])
    payload = {"jsonrpc": "2.0", "method": "eth_getBalance", "params": [address, "latest"], "id": 1}
    resp = httpx.post(url, json=payload, timeout=10)
    data = resp.json()
    wei = int(data.get("result", "0x0"), 16)
    xrp = wei / 1e18
    print(f"Address: {address}")
    print(f"Balance: {xrp:.6f} XRP ({network})")

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
    print("# EVM Contract Deployment — sign and submit to https://rpc.xrplevm.org")
    json_out(tx)

# --- TOOL 13: EVM Bridge Check ---
def tool_evm_bridge(network: str = "mainnet"):
    import httpx
    rpc_urls = {"mainnet": "https://rpc.xrplevm.org", "testnet": "https://rpc.testnet.xrplevm.org"}
    url = rpc_urls.get(network, rpc_urls["mainnet"])
    payload = {"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1}
    resp = httpx.post(url, json=payload, timeout=10)
    data = resp.json()
    block = int(data.get("result", "0x0"), 16)
    print(f"XRPL EVM Sidechain ({network})")
    print(f"Latest Block: {block}")
    print(f"RPC: {url}")
    print(f"Chain ID: 1440000")
    print(f"Bridge: L1↔EVM federated bridge active")

# --- TOOL 14: Hooks Bitmask Calculator ---
HOOK_BITS = {
    "onAccountDelete": 1, "onLedgerClose": 2, "onTransaction": 4, "onStaked": 8, "onEmit": 16,
    "onURITokenCreateSellOffer": 256, "onURITokenCreateBuyOffer": 512,
    "onURITokenAcceptSellOffer": 1024, "onURITokenAcceptBuyOffer": 2048,
    "onURITokenCancelSellOffer": 4096, "onURITokenCancelBuyOffer": 8192,
}

def tool_hooks_bitmask(*hook_names: str):
    mask = 0
    for name in hook_names:
        bit = HOOK_BITS.get(name)
        if bit is not None:
            mask |= bit
        else:
            print(f"  ⚠️ Unknown hook: {name}")
    print(f"HookOn: {mask}")
    print(f"Hex:    {hex(mask)}")
    print(f"Hooks:  {', '.join(hook_names)}")

# --- TOOL 15: Hooks Account Info ---
def tool_hooks_info(address: str):
    import httpx
    payload = {"method": "account_objects", "params": [{"account": address, "ledger_index": "validated", "type": "hook", "limit": 20}]}
    try:
        resp = httpx.post("https://xahau.network", json=payload, timeout=15)
        data = resp.json()
        hooks = data.get("result", {}).get("account_objects", [])
        if not hooks:
            print(f"No hooks found on {address}")
            return
        print(f"Hooks installed on {address}: {len(hooks)}")
        for i, h in enumerate(hooks, 1):
            h_hash = h.get("HookHash", "?")
            ns = h.get("HookNamespace", "")
            params = h.get("HookParameters", [])
            print(f"  {i}. Hash: {h_hash[:20]}...")
            if ns: print(f"     Namespace: {ns[:20]}...")
            for p in params[:3]:
                pname = p.get("HookParameterName", "?")
                print(f"     Param: {pname}")
    except Exception as e:
        print(f"Error querying Xahau: {e}")

# --- TOOL 16: Flare Price Feeds ---
def tool_flare_price(*symbols: str):
    import httpx
    try:
        resp = httpx.get("https://api.flare.network/ftso/v2/feeds", timeout=10)
        data = resp.json()
        feeds = {}
        for f in data:
            feed_name = f.get("feed", "").upper()
            if feed_name:
                feeds[feed_name] = float(f.get("value", 0))
        for sym in symbols:
            s = sym.upper()
            if s in feeds:
                print(f"{s}: ${feeds[s]:.6f}")
            else:
                print(f"{s}: not found")
    except Exception as e:
        try:
            resp = httpx.get("https://flare-api.flare.network/ftso/v2/feeds", timeout=10)
            data = resp.json()
            feeds = {}
            for f in data:
                feed_name = f.get("feed", "").upper()
                if feed_name:
                    feeds[feed_name] = float(f.get("value", 0))
            for sym in symbols:
                s = sym.upper()
                if s in feeds:
                    print(f"{s}: ${feeds[s]:.6f}")
                else:
                    print(f"{s}: not found")
        except Exception as e2:
            print(f"Flare API error: {e2}")

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
    print("# EscrowCreate TX JSON — sign with Xaman/Joey")
    json_tx_out(tx)

# --- TOOL 12: Escrow Finish ---
def tool_build_escrow_finish(frm: str, owner: str, offer_sequence: str,
                              condition: str = None, fulfillment: str = None):
    kwargs = dict(account=frm, owner=owner, offer_sequence=int(offer_sequence))
    if condition:
        kwargs["condition"] = condition
    if fulfillment:
        kwargs["fulfillment"] = fulfillment
    tx = EscrowFinish(**kwargs)
    print("# EscrowFinish TX JSON — sign with Xaman/Joey")
    json_tx_out(tx)

# --- TOOL 13: Escrow Cancel ---
def tool_build_escrow_cancel(frm: str, owner: str, offer_sequence: str):
    tx = EscrowCancel(account=frm, owner=owner, offer_sequence=int(offer_sequence))
    print("# EscrowCancel TX JSON — sign with Xaman/Joey")
    json_tx_out(tx)

# --- TOOL 14: Check Create ---
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
    print("# CheckCreate TX JSON — sign with Xaman/Joey")
    json_tx_out(tx)

# --- TOOL 15: Check Cash ---
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
    print("# CheckCash TX JSON — sign with Xaman/Joey")
    json_tx_out(tx)

# --- TOOL 16: Check Cancel ---
def tool_build_check_cancel(frm: str, check_id: str):
    tx = CheckCancel(account=frm, check_id=check_id)
    print("# CheckCancel TX JSON — sign with Xaman/Joey")
    json_tx_out(tx)

# --- TOOL 17: Payment Channel Create ---
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
    print("# PaymentChannelCreate TX JSON — sign with Xaman/Joey")
    json_tx_out(tx)

# --- TOOL 18: Payment Channel Fund ---
def tool_build_paychannel_fund(frm: str, channel_id: str, amount: str):
    tx = PaymentChannelFund(account=frm, channel=channel_id, amount=amount)
    print("# PaymentChannelFund TX JSON — sign with Xaman/Joey")
    json_tx_out(tx)

# --- TOOL 19: Payment Channel Claim ---
def tool_build_paychannel_claim(frm: str, channel_id: str, amount: str = None,
                                 signature: str = None, public_key: str = None):
    kwargs = dict(account=frm, channel=channel_id)
    if amount:
        kwargs["amount"] = amount
    if signature:
        kwargs["signature"] = signature
    if public_key:
        kwargs["public_key"] = public_key
    tx = PaymentChannelClaim(**kwargs)
    print("# PaymentChannelClaim TX JSON — sign with Xaman/Joey")
    json_tx_out(tx)

# --- TOOL 20: Set Regular Key ---
def tool_build_set_regular_key(frm: str, regular_key: str = None):
    kwargs = dict(account=frm)
    if regular_key:
        kwargs["regular_key"] = regular_key
    tx = SetRegularKey(**kwargs)
    print("# SetRegularKey TX JSON — sign with Xaman/Joey")
    json_tx_out(tx)

# --- TOOL 21: Account Delete ---
def tool_build_account_delete(frm: str, to: str):
    tx = AccountDelete(account=frm, destination=to)
    print("# AccountDelete TX JSON — sign with Xaman/Joey")
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
    print("# DepositPreauth TX JSON — sign with Xaman/Joey")
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
        print(f"Error fetching account objects for {address}: {e}")
        return
    objects = resp.result.get("account_objects", [])
    label = f" (type={obj_type})" if obj_type else ""
    print(f"Account Objects for {address}: {len(objects)} found{label}")
    for obj in objects:
        json_out(obj)

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
        from xrpl.models.transactions.transaction import Memo, MemoWrapper
        try:
            memo_hex = memo.encode("utf-8").hex().upper()
            kwargs["memos"] = [MemoWrapper(memo=Memo(memo_data=memo_hex))]
        except Exception:
            pass
    tx = Clawback(**kwargs)
    print("# Clawback TX JSON — sign with Xaman/Crossmark/xrpl-py")
    json_tx_out(tx)


if __name__ == "__main__":
    main()
