#!/usr/bin/env python3
"""Batch transaction tool (XLS-56) — RETIRED 2026-07-11.

The XLS-56 `Batch` builder is intentionally NOT registered as a command. Official XRPL
material lists the `Batch` amendment as **obsolete** following the February 2026
signature-validation (unauthorized-inner-transaction) disclosure: the amendment was
disabled, and its proposed replacement `BatchV1_1` has no released implementation, no
finalized specification, and no live mainnet activation. A live `feature` response may
still report `supported: true` for the historical amendment ID — that raw flag does NOT
override the official obsolete/security lifecycle status.

The implementation below (`tool_build_batch`) is preserved unchanged as a historical /
internal artifact so the retirement stays auditable and reversible, but it is unreachable:
`COMMANDS` is empty, so `build-batch` is absent from CLI dispatch, from the MCP allowlist
and its listing, and from the dev-test matrix. Do NOT re-register it, and do NOT substitute
`BatchV1_1`, until a released implementation, an official specification, and independently
verified live amendment status all exist.

Sources (verified live 2026-07-11):
- https://xrpl.org/blog/2026/vulnerabilitydisclosurereport-bug-feb2026
- https://xrpl.org/resources/known-amendments

See also `SECURITY.md` (agent boundary) and the v1.8.3 entry in `CHANGELOG.md`.
"""
from ._shared import (
    json_out, note_out, json_tx_out, warn_if_amendment_not_enabled,
    Payment, TrustSet, OfferCreate, NFTokenMint, NFTokenCreateOffer,
    AMMCreate, AMMDeposit, AMMWithdraw, AMMVote, AMMBid,
    Clawback, AccountSet, SignerListSet,
    EscrowCreate, EscrowFinish, EscrowCancel,
    CheckCreate, CheckCash, CheckCancel,
    PaymentChannelCreate, PaymentChannelFund, PaymentChannelClaim,
    SetRegularKey, AccountDelete, DepositPreauth,
    TicketCreate, OracleSet,
    MPTokenIssuanceCreate, MPTokenAuthorize,
    CredentialCreate, CredentialAccept, CredentialDelete,
    Batch,
)
import json as json_mod

def tool_build_batch(frm: str, inner_txs: str = None, flags: str = None, txns: str = None):
    warn_if_amendment_not_enabled("Batch")
    inner_txs = inner_txs or txns
    try:
        raw_txs = json_mod.loads(inner_txs)
    except Exception as e:
        json_out({"Error": "InvalidJSON", "Message": f"Error parsing --inner-txs JSON: {e}"})
        return
    if not isinstance(raw_txs, list):
        json_out({"Error": "InvalidBatch", "Message": "--inner-txs must be a JSON array"})
        return
    if len(raw_txs) < 2 or len(raw_txs) > 8:
        json_out({"Error": "InvalidBatch", "Message": f"Batch requires 2-8 inner transactions, got {len(raw_txs)}"})
        return

    TX_MODELS = {
        "Payment": Payment, "TrustSet": TrustSet, "OfferCreate": OfferCreate,
        "NFTokenMint": NFTokenMint, "NFTokenCreateOffer": NFTokenCreateOffer,
        "AMMCreate": AMMCreate, "AMMDeposit": AMMDeposit, "AMMWithdraw": AMMWithdraw,
        "AMMVote": AMMVote, "AMMBid": AMMBid,
        "Clawback": Clawback, "AccountSet": AccountSet, "SignerListSet": SignerListSet,
        "EscrowCreate": EscrowCreate, "EscrowFinish": EscrowFinish, "EscrowCancel": EscrowCancel,
        "CheckCreate": CheckCreate, "CheckCash": CheckCash, "CheckCancel": CheckCancel,
        "PaymentChannelCreate": PaymentChannelCreate, "PaymentChannelFund": PaymentChannelFund,
        "PaymentChannelClaim": PaymentChannelClaim,
        "SetRegularKey": SetRegularKey, "AccountDelete": AccountDelete, "DepositPreauth": DepositPreauth,
        "TicketCreate": TicketCreate, "OracleSet": OracleSet,
        "MPTokenIssuanceCreate": MPTokenIssuanceCreate, "MPTokenAuthorize": MPTokenAuthorize,
        "CredentialCreate": CredentialCreate, "CredentialAccept": CredentialAccept,
        "CredentialDelete": CredentialDelete,
        "Batch": Batch,
    }

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
        "LastUpdateTime": "last_update_time", "PriceDataSeries": "price_data_series",
        "RawTransactions": "raw_transactions",
        "DestinationTag": "destination_tag", "InvoiceID": "invoice_id",
        "Expiration": "expiration", "CancelAfter": "cancel_after",
        "FinishAfter": "finish_after", "Condition": "condition", "Fulfillment": "fulfillment",
        "Authorize": "authorize", "Unauthorize": "unauthorize", "RegularKey": "regular_key",
        "Asset": "asset", "Asset2": "asset2", "Amount2": "amount2",
        "LPTokenOut": "lp_token_out", "LPTokenIn": "lp_token_in",
        "TradingFee": "trading_fee", "BidMin": "bid_min", "BidMax": "bid_max",
        "AuthAccounts": "auth_accounts",
        "SignerQuorum": "signer_quorum", "SignerEntries": "signer_entries",
        "AssetScale": "asset_scale", "MaximumAmount": "maximum_amount",
        "RawTransaction": "raw_transaction", "HookOn": "hook_on",
    }

    wrapped = []
    for raw in raw_txs:
        tx_type = raw.get("TransactionType")
        model_class = TX_MODELS.get(tx_type)
        if model_class is None:
            json_out({"Error": "UnsupportedTransactionType",
                      "Message": f"Unknown TransactionType '{tx_type}'"})
            return
        kwargs = {}
        for k, v in raw.items():
            if k == "TransactionType": continue
            mapped = FIELD_MAP.get(k, k[0].lower() + k[1:] if k else k)
            kwargs[mapped] = v
        kwargs.setdefault("flags", 0)
        kwargs["flags"] |= 0x40000000
        kwargs.setdefault("fee", "0")
        kwargs.setdefault("signing_pub_key", "")
        try:
            wrapped.append(model_class(**kwargs))
        except Exception as e:
            json_out({"Error": "InvalidInnerTransaction",
                      "Message": f"Error validating inner {tx_type}: {e}"})
            return

    bkwargs: dict = dict(account=frm, raw_transactions=wrapped)
    if flags is not None: bkwargs["flags"] = int(flags)
    tx = Batch(**bkwargs)
    note_out("# Batch TX JSON - each inner tx must be signed separately")
    json_tx_out(tx)

# RETIRED: no reachable command. `build-batch` is intentionally left unregistered (see the
# module docstring). Keeping COMMANDS empty removes it from the CLI dispatcher, the MCP
# allowlist listing, and the dev-test matrix, while `tool_build_batch` above is preserved as a
# historical artifact. A request for `build-batch` is therefore default-denied as an unknown
# command on every surface. Re-enabling requires a released BatchV1_1 implementation, an official
# spec, and independently verified live amendment status — not a raw `supported: true` flag.
COMMANDS: dict = {}
