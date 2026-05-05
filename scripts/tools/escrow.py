#!/usr/bin/env python3
"""Escrow tools: create, finish, cancel."""
from ._shared import (
    note_out, json_tx_out, _dispatch_build,
    EscrowCreate, EscrowFinish, EscrowCancel,
)

def tool_build_escrow_create(frm: str, to: str, amount: str, condition: str = None,
                              cancel_after: str = None, finish_after: str = None):
    kwargs = dict(account=frm, destination=to, amount=amount)
    if condition: kwargs["condition"] = condition
    if cancel_after: kwargs["cancel_after"] = int(cancel_after)
    if finish_after: kwargs["finish_after"] = int(finish_after)
    tx = EscrowCreate(**kwargs)
    note_out("# EscrowCreate TX JSON - signer-ready JSON")
    json_tx_out(tx)

def tool_build_escrow_finish(frm: str, owner: str, offer_sequence: str,
                              condition: str = None, fulfillment: str = None):
    kwargs = dict(account=frm, owner=owner, offer_sequence=int(offer_sequence))
    if condition: kwargs["condition"] = condition
    if fulfillment: kwargs["fulfillment"] = fulfillment
    tx = EscrowFinish(**kwargs)
    note_out("# EscrowFinish TX JSON - signer-ready JSON")
    json_tx_out(tx)

def tool_build_escrow_cancel(frm: str, owner: str, offer_sequence: str):
    tx = EscrowCancel(account=frm, owner=owner, offer_sequence=int(offer_sequence))
    note_out("# EscrowCancel TX JSON - signer-ready JSON")
    json_tx_out(tx)

COMMANDS = {
    "build-escrow-create": lambda: _dispatch_build(3, tool_build_escrow_create),
    "build-escrow-finish": lambda: _dispatch_build(3, tool_build_escrow_finish),
    "build-escrow-cancel": lambda: _dispatch_build(3, tool_build_escrow_cancel),
}
