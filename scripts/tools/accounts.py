#!/usr/bin/env python3
"""Account tools: info, objects, tx history, key management, account delete, deposit preauth, signer list, ticket create."""
from decimal import Decimal
from ._shared import (
    _request, json_out, usage_out, note_out, json_tx_out, get_reserve_settings,
    fmt_xrp, short, drops_to_xrp, parse_amount_arg, IssuedCurrencyAmount,
    _dispatch_build, AccountInfo, AccountObjects, AccountTx, SignerListSet, SignerEntry,
    SetRegularKey, AccountDelete, DepositPreauth, TicketCreate, AccountSet,
    to_uint32, validate_xrpl_address,
)

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
    json_out({"Account": address, "Type": obj_type, "ObjectCount": len(objects), "Objects": objects})

def tool_build_set_regular_key(frm: str, regular_key: str = None):
    kwargs = dict(account=frm)
    if regular_key:
        kwargs["regular_key"] = regular_key
    tx = SetRegularKey(**kwargs)
    note_out("# SetRegularKey TX JSON - signer-ready JSON - paste into Xaman Developer tab")
    json_tx_out(tx)

ACCOUNT_DELETE_WARNING = """\
# =====================================================================
# WARNING - DESTRUCTIVE: AccountDelete removes {frm} from the ledger.
# The deletion is irreversible. All remaining XRP is sent to {to}, and
# ledger entries that do not block deletion (Offers, Tickets, SignerLists,
# DepositPreauth) are destroyed along with the account.
#
# This builder is offline and CANNOT prove the ledger preconditions. Verify
# each of the following against the live ledger before signing:
#   1. Sequence + 256 is below the current ledger index (account_info, ledger).
#   2. The account owns no deletion-blocking objects - e.g. Escrow, Check,
#      PayChannel, trust lines (RippleState), NFTokenPage - and not more than
#      1000 objects in total (account_objects).
#   3. The transaction pays a special cost of at least the current
#      owner reserve increment (read it from server_info) - far above a
#      normal fee. A failed AccountDelete still burns that cost.
#   4. The destination account already exists, can receive XRP (DepositAuth
#      off, or this sender preauthorized), and if it requires a destination
#      tag you must supply --dest-tag.
# The list above follows xrpl.org; treat it as the minimum to check, not as
# proof that the delete will succeed.
# ====================================================================="""

def tool_build_account_delete(frm: str, to: str, dest_tag=None, destination_tag=None):
    try:
        frm = validate_xrpl_address(frm, "source account")
        to = validate_xrpl_address(to, "destination account")
        tag = to_uint32(dest_tag if dest_tag is not None else destination_tag,
                        "destination tag")
    except ValueError as exc:
        usage_out("build-account-delete",
                  "build-account-delete --from rSRC --to rDST [--dest-tag N]. "
                  f"{exc}")
        return
    kwargs = dict(account=frm, destination=to)
    if tag is not None:
        kwargs["destination_tag"] = tag
    tx = AccountDelete(**kwargs)
    note_out(ACCOUNT_DELETE_WARNING.format(frm=frm, to=to))
    note_out("# AccountDelete TX JSON - signer-ready JSON - paste into Xaman Developer tab")
    json_tx_out(tx)

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

def tool_build_signer_list_set(frm: str, quorum: str, signers: str = None):
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

def tool_build_ticket_create(frm: str, count: int):
    tx = TicketCreate(account=frm, ticket_count=int(count))
    note_out(f"# TicketCreate TX JSON - creates {count} sequence slots")
    json_tx_out(tx)

def tool_build_account_set(frm: str, set_flag: int = None, clear_flag: int = None,
                           domain: str = None, transfer_rate: int = None,
                           tick_size: int = None, nftoken_minter: str = None,
                           email_hash: str = None, message_key: str = None):
    kwargs: dict = dict(account=frm)
    if set_flag is not None: kwargs["set_flag"] = int(set_flag)
    if clear_flag is not None: kwargs["clear_flag"] = int(clear_flag)
    if domain:
        import re
        if re.match(r'^[0-9A-Fa-f]+$', domain):
            kwargs["domain"] = domain
        else:
            kwargs["domain"] = domain.encode().hex().upper()
    if transfer_rate is not None:
        try:
            rate = int(transfer_rate)
        except (TypeError, ValueError):
            json_out({"Error": "InvalidTransferRate",
                      "Message": f"transfer_rate must be an integer (got {transfer_rate!r})"})
            return
        # 0 is the documented shortcut for 1000000000 (no transfer fee) and the
        # only way an issuer can clear an existing rate.
        if rate != 0 and not (1_000_000_000 <= rate <= 2_000_000_000):
            json_out({"Error": "InvalidTransferRate",
                      "Message": "transfer_rate must be 0 (clear/no fee) or "
                                 "1000000000 (0%) to 2000000000 (100%)"})
            return
        kwargs["transfer_rate"] = rate
    if tick_size is not None:
        ts = int(tick_size)
        if ts < 3 or ts > 15:
            json_out({"Error": "InvalidTickSize", "Message": "tick_size must be 3-15"})
            return
        kwargs["tick_size"] = ts
    if nftoken_minter: kwargs["nftoken_minter"] = nftoken_minter
    if email_hash: kwargs["email_hash"] = email_hash
    if message_key: kwargs["message_key"] = message_key
    tx = AccountSet(**kwargs)
    note_out("# AccountSet TX JSON - issuer configuration")
    json_tx_out(tx)

def tool_account_tx(address: str, limit: int = 20, ledger_min: int = -1, ledger_max: int = -1):
    try:
        resp = _request(AccountTx(
            account=address, limit=int(limit),
            ledger_index_min=int(ledger_min), ledger_index_max=int(ledger_max),
        ))
        txs = resp.result.get("transactions", [])
        json_out({
            "Account": address,
            "Count": len(txs),
            "Transactions": [{
                "Hash": t.get("hash") or (t.get("tx") or t.get("tx_json") or {}).get("hash"),
                "Type": (t.get("tx") or t.get("tx_json") or {}).get("TransactionType"),
                "Result": t.get("meta", {}).get("TransactionResult"),
                "LedgerIndex": t.get("ledger_index"),
            } for t in txs],
            "Marker": resp.result.get("marker"),
        })
    except Exception as e:
        json_out({"Error": "AccountTxError", "Message": str(e)})

COMMANDS = {
    "account": lambda: tool_account(__import__('sys').argv[2]) if len(__import__('sys').argv) >= 3 else print("Usage: account rADDRESS"),
    "balance": lambda: tool_account(__import__('sys').argv[2]) if len(__import__('sys').argv) >= 3 else print("Usage: balance rADDRESS"),
    "account_objects": lambda: tool_account_objects(__import__('sys').argv[2], __import__('sys').argv[3] if len(__import__('sys').argv) >= 4 else None) if len(__import__('sys').argv) >= 3 else print("Usage: account_objects rADDRESS [type]"),
    "account-tx": lambda: tool_account_tx(__import__('sys').argv[2], *([int(x) for x in __import__('sys').argv[3:5]] if len(__import__('sys').argv) >= 4 else [])) if len(__import__('sys').argv) >= 3 else print("Usage: account-tx rADDR [limit] [ledger_min] [ledger_max]"),
    "build-set-regular-key": lambda: _dispatch_build(1, tool_build_set_regular_key),
    "build-account-delete": lambda: _dispatch_build(2, tool_build_account_delete),
    "build-deposit-preauth": lambda: _dispatch_build(2, tool_build_deposit_preauth),
    "build-signer-list-set": lambda: _dispatch_build(2, tool_build_signer_list_set),
    "build-ticket-create": lambda: _dispatch_build(2, tool_build_ticket_create),
    "build-account-set": lambda: _dispatch_build(0, tool_build_account_set),
}
