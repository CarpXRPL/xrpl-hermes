#!/usr/bin/env python3
"""Payment Channel tools: create, fund, claim."""
from ._shared import (
    note_out, json_tx_out, _dispatch_build,
    PaymentChannelCreate, PaymentChannelFund, PaymentChannelClaim,
)

def tool_build_paychannel_create(frm: str, to: str, amount: str, settle_delay: str,
                                  public_key: str, cancel_after: str = None):
    kwargs = dict(account=frm, destination=to, amount=amount,
                  settle_delay=int(settle_delay), public_key=public_key)
    if cancel_after: kwargs["cancel_after"] = int(cancel_after)
    tx = PaymentChannelCreate(**kwargs)
    note_out("# PaymentChannelCreate TX JSON - signer-ready JSON")
    json_tx_out(tx)

def tool_build_paychannel_fund(frm: str, channel_id: str, amount: str):
    tx = PaymentChannelFund(account=frm, channel=channel_id, amount=amount)
    note_out("# PaymentChannelFund TX JSON - signer-ready JSON")
    json_tx_out(tx)

def tool_build_paychannel_claim(frm: str, channel_id: str, amount: str = None,
                                 balance: str = None, signature: str = None,
                                 public_key: str = None):
    kwargs = dict(account=frm, channel=channel_id)
    if amount: kwargs["amount"] = amount
    if balance: kwargs["balance"] = balance
    if signature: kwargs["signature"] = signature
    if public_key: kwargs["public_key"] = public_key
    tx = PaymentChannelClaim(**kwargs)
    note_out("# PaymentChannelClaim TX JSON - signer-ready JSON")
    json_tx_out(tx)

COMMANDS = {
    "build-paychannel-create": lambda: _dispatch_build(5, tool_build_paychannel_create),
    "build-paychannel-fund": lambda: _dispatch_build(3, tool_build_paychannel_fund),
    "build-paychannel-claim": lambda: _dispatch_build(2, tool_build_paychannel_claim),
}
