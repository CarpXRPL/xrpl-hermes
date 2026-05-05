#!/usr/bin/env python3
"""MPT (Multi-Purpose Token) tools."""
from ._shared import (
    note_out, json_tx_out, _dispatch_build,
    MPTokenIssuanceCreate, MPTokenAuthorize,
)

def tool_build_mpt_issuance_create(frm: str, asset_scale: str = None,
                                    maximum_amount: str = None, transfer_fee: str = None,
                                    flags: str = None):
    kwargs: dict = dict(account=frm)
    if asset_scale is not None: kwargs["asset_scale"] = int(asset_scale)
    if maximum_amount is not None: kwargs["maximum_amount"] = maximum_amount
    if transfer_fee is not None:
        kwargs["transfer_fee"] = int(transfer_fee)
        if flags is None: flags = 0
        flags = int(flags, 16) if str(flags).startswith("0x") else int(flags)
        flags |= 0x20  # tfMPTCanTransfer
    if flags is not None:
        kwargs["flags"] = int(flags, 16) if str(flags).startswith("0x") else int(flags)
    tx = MPTokenIssuanceCreate(**kwargs)
    note_out("# MPTokenIssuanceCreate TX JSON - signer-ready JSON")
    json_tx_out(tx)

def tool_build_mpt_authorize(frm: str, mpt_issuance_id: str, holder: str = None,
                              flags: str = None):
    kwargs: dict = dict(account=frm, mptoken_issuance_id=mpt_issuance_id)
    if holder: kwargs["holder"] = holder
    if flags is not None: kwargs["flags"] = int(flags)
    tx = MPTokenAuthorize(**kwargs)
    note_out("# MPTokenAuthorize TX JSON - signer-ready JSON")
    json_tx_out(tx)

COMMANDS = {
    "build-mpt-issuance-create": lambda: _dispatch_build(1, tool_build_mpt_issuance_create),
    "build-mpt-authorize": lambda: _dispatch_build(2, tool_build_mpt_authorize),
}
