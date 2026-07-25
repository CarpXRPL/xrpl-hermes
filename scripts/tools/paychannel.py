#!/usr/bin/env python3
"""Payment Channel tools: create, fund, claim."""
from ._shared import (
    note_out, json_tx_out, usage_out, validate_drops_amount,
    validate_positive_drops_amount,
    _dispatch_build,
    PaymentChannelCreate, PaymentChannelFund, PaymentChannelClaim,
)

# PaymentChannelFund/Claim declare their amounts as plain strings: those fields are
# XRP drops and nothing else, so they get the drops-only validator, which already
# names the required unit in its message.

def tool_build_paychannel_create(frm: str, to: str, amount: str, settle_delay: str,
                                  public_key: str, cancel_after: str = None):
    try:
        amt = validate_positive_drops_amount(amount)
    except ValueError as exc:
        usage_out("build-paychannel-create",
                  f"build-paychannel-create --from rSRC --to rDST --amount DROPS: {exc}")
        return
    kwargs = dict(account=frm, destination=to, amount=amt,
                  settle_delay=int(settle_delay), public_key=public_key)
    if cancel_after: kwargs["cancel_after"] = int(cancel_after)
    tx = PaymentChannelCreate(**kwargs)
    note_out("# PaymentChannelCreate TX JSON - signer-ready JSON")
    json_tx_out(tx)

def tool_build_paychannel_fund(frm: str, channel_id: str, amount: str):
    try:
        amt = validate_positive_drops_amount(amount)
    except ValueError as exc:
        usage_out("build-paychannel-fund",
                  f"build-paychannel-fund --from rSRC --channel-id ID --amount DROPS. {exc}")
        return
    tx = PaymentChannelFund(account=frm, channel=channel_id, amount=amt)
    note_out("# PaymentChannelFund TX JSON - signer-ready JSON")
    json_tx_out(tx)

def tool_build_paychannel_claim(frm: str, channel_id: str, amount: str = None,
                                 balance: str = None, signature: str = None,
                                 public_key: str = None):
    kwargs = dict(account=frm, channel=channel_id)
    try:
        if amount: kwargs["amount"] = validate_drops_amount(amount)
        if balance: kwargs["balance"] = validate_drops_amount(balance, "balance")
    except ValueError as exc:
        usage_out("build-paychannel-claim",
                  f"build-paychannel-claim --from rSRC --channel-id ID "
                  f"[--amount DROPS] [--balance DROPS]. {exc}")
        return
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
