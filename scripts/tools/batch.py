#!/usr/bin/env python3
"""Batch transaction tool (XLS-56)."""
from ._shared import (
    json_out, note_out, json_tx_out, _dispatch_build,
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

COMMANDS = {
    "build-batch": lambda: _dispatch_build(2, tool_build_batch),
}
