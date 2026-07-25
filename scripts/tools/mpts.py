#!/usr/bin/env python3
"""MPT (Multi-Purpose Token) tools."""
from ._shared import (
    note_out, json_tx_out, usage_out, _dispatch_build, warn_if_amendment_not_enabled,
    validate_xrpl_address,
    MPTokenIssuanceCreate, MPTokenAuthorize,
)

def tool_build_mpt_issuance_create(frm: str, asset_scale: str = None,
                                    maximum_amount: str = None, transfer_fee: str = None,
                                    flags: str = None):
    warn_if_amendment_not_enabled("MPTokensV1")
    try:
        kwargs: dict = dict(account=validate_xrpl_address(frm, "source account"))
        if asset_scale is not None:
            scale = int(asset_scale)
            if not 0 <= scale <= 255:
                raise ValueError("asset-scale must be an integer from 0 through 255")
            kwargs["asset_scale"] = scale
        if maximum_amount is not None:
            maximum_text = str(maximum_amount)
            if not maximum_text or any(char < "0" or char > "9" for char in maximum_text):
                raise ValueError("maximum-amount must be a positive base-10 integer")
            maximum = int(maximum_text)
            if not 1 <= maximum <= 9_223_372_036_854_775_807:
                raise ValueError("maximum-amount must be from 1 through 9223372036854775807")
            kwargs["maximum_amount"] = str(maximum)
        flag_value = (int(str(flags), 0) if flags is not None else 0)
        if flag_value & ~(0x7E | 0x80000000):
            raise ValueError("flags contain bits unsupported by MPTokenIssuanceCreate")
        if transfer_fee is not None:
            fee = int(transfer_fee)
            if not 0 <= fee <= 50_000:
                raise ValueError("transfer-fee must be an integer from 0 through 50000")
            kwargs["transfer_fee"] = fee
            flag_value |= 0x20  # tfMPTCanTransfer is required when TransferFee is present.
        if flags is not None or transfer_fee is not None:
            kwargs["flags"] = flag_value
    except (ValueError, TypeError) as exc:
        usage_out("build-mpt-issuance-create",
                  "build-mpt-issuance-create --from rISSUER [--asset-scale 0..255] "
                  "[--maximum-amount 1..9223372036854775807] [--transfer-fee 0..50000] "
                  f"[--flags N]. {exc}")
        return
    tx = MPTokenIssuanceCreate(**kwargs)
    note_out("# MPTokenIssuanceCreate TX JSON - signer-ready JSON")
    json_tx_out(tx)

def tool_build_mpt_authorize(frm: str, mpt_issuance_id: str, holder: str = None,
                              flags: str = None):
    warn_if_amendment_not_enabled("MPTokensV1")
    try:
        issuance_id = str(mpt_issuance_id)
        if (len(issuance_id) != 48
                or any(char not in "0123456789abcdefABCDEF" for char in issuance_id)):
            raise ValueError("mpt-issuance-id must be exactly 48 hexadecimal characters (UInt192)")
        kwargs: dict = dict(
            account=validate_xrpl_address(frm, "source account"),
            mptoken_issuance_id=issuance_id.upper(),
        )
        if holder is not None:
            kwargs["holder"] = validate_xrpl_address(holder, "holder")
        if flags is not None:
            flag_value = int(str(flags), 0)
            if flag_value & ~(0x1 | 0x80000000):
                raise ValueError("flags may contain only tfMPTUnauthorize (1) and tfFullyCanonicalSig")
            kwargs["flags"] = flag_value
    except (ValueError, TypeError) as exc:
        usage_out("build-mpt-authorize",
                  "build-mpt-authorize --from rACCOUNT --mpt-issuance-id 48_HEX "
                  f"[--holder rHOLDER] [--flags 0|1]. {exc}")
        return
    tx = MPTokenAuthorize(**kwargs)
    note_out("# MPTokenAuthorize TX JSON - signer-ready JSON")
    json_tx_out(tx)

COMMANDS = {
    "build-mpt-issuance-create": lambda: _dispatch_build(1, tool_build_mpt_issuance_create),
    "build-mpt-authorize": lambda: _dispatch_build(2, tool_build_mpt_authorize),
}
