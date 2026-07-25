#!/usr/bin/env python3
"""Escrow tools: create, finish, cancel."""
import hashlib

from ._shared import (
    note_out, json_tx_out, usage_out, parse_amount_arg, validate_positive_amount,
    IssuedCurrencyAmount, to_uint32, _dispatch_build,
    EscrowCreate, EscrowFinish, EscrowCancel,
)

def _der_length(data: bytes, offset: int):
    """Read one canonical DER length and return (length, next_offset)."""
    if offset >= len(data):
        raise ValueError("truncated DER length")
    first = data[offset]
    offset += 1
    if first < 0x80:
        return first, offset
    count = first & 0x7F
    if count == 0 or count > 4 or offset + count > len(data):
        raise ValueError("invalid DER length")
    raw = data[offset:offset + count]
    if raw[0] == 0:
        raise ValueError("non-canonical DER length")
    value = int.from_bytes(raw, "big")
    if value < 0x80:
        raise ValueError("non-canonical DER length")
    return value, offset + count

def _der_value(data: bytes, offset: int, tag: int):
    if offset >= len(data) or data[offset] != tag:
        raise ValueError(f"expected DER tag 0x{tag:02X}")
    length, start = _der_length(data, offset + 1)
    end = start + length
    if end > len(data):
        raise ValueError("truncated DER value")
    return data[start:end], end

def _decode_hex(value: str, field: str) -> bytes:
    if not value or len(value) % 2:
        raise ValueError(f"--{field} must be non-empty even-length hexadecimal")
    try:
        return bytes.fromhex(value)
    except ValueError as exc:
        raise ValueError(f"--{field} must be non-empty even-length hexadecimal") from exc

def _parse_preimage_condition(value: str):
    """Parse rippled's supported PREIMAGE-SHA-256 condition DER subset."""
    data = _decode_hex(value, "condition")
    content, end = _der_value(data, 0, 0xA0)
    if end != len(data):
        raise ValueError("--condition has trailing DER data")
    fingerprint, offset = _der_value(content, 0, 0x80)
    if len(fingerprint) != 32:
        raise ValueError("--condition fingerprint must be 32 bytes")
    cost_raw, offset = _der_value(content, offset, 0x81)
    if offset != len(content) or not cost_raw:
        raise ValueError("--condition has malformed cost data")
    if cost_raw[0] & 0x80:
        raise ValueError("--condition cost must be nonnegative")
    if len(cost_raw) > 1 and cost_raw[0] == 0 and not (cost_raw[1] & 0x80):
        raise ValueError("--condition cost is not canonically encoded")
    cost = int.from_bytes(cost_raw, "big")
    if cost > 128:
        raise ValueError("--condition cost exceeds rippled's 128-byte preimage limit")
    return fingerprint, cost

def _parse_preimage_fulfillment(value: str) -> bytes:
    data = _decode_hex(value, "fulfillment")
    content, end = _der_value(data, 0, 0xA0)
    if end != len(data):
        raise ValueError("--fulfillment has trailing DER data")
    preimage, offset = _der_value(content, 0, 0x80)
    if offset != len(content) or len(preimage) > 128:
        raise ValueError("--fulfillment must contain one preimage of at most 128 bytes")
    return preimage

def _validate_escrow_fields(is_token, condition, cancel_after, finish_after):
    """Enforce the official EscrowCreate field-combination matrix."""
    has_condition = condition is not None
    has_cancel = cancel_after is not None
    has_finish = finish_after is not None
    allowed_xrp = {
        (True, False, False),
        (True, False, True),
        (True, True, False),
        (True, True, True),
        (False, True, True),
    }
    if is_token:
        if not (has_cancel and (has_finish or has_condition)):
            raise ValueError(
                "token escrows require --cancel-after plus --finish-after and/or --condition"
            )
    elif (has_finish, has_condition, has_cancel) not in allowed_xrp:
        raise ValueError(
            "invalid XRP escrow fields: use --finish-after, optionally with "
            "--cancel-after/--condition, or use --condition with --cancel-after"
        )
    if has_condition:
        _parse_preimage_condition(condition)
    cancel_value = to_uint32(cancel_after, "cancel-after") if has_cancel else None
    finish_value = to_uint32(finish_after, "finish-after") if has_finish else None
    if cancel_value is not None and finish_value is not None and finish_value >= cancel_value:
        raise ValueError("--finish-after must be earlier than --cancel-after")
    return condition.upper() if has_condition else None, cancel_value, finish_value

def tool_build_escrow_create(frm: str, to: str, amount: str, condition: str = None,
                              cancel_after: str = None, finish_after: str = None):
    # EscrowCreate.Amount admits an issued amount as well as drops; passing the
    # raw argument made the model's positivity check call float() on it, so a
    # token escrow failed naming a type the operator never supplied.
    try:
        amt = validate_positive_amount(parse_amount_arg(amount))
        condition_value, cancel_value, finish_value = _validate_escrow_fields(
            isinstance(amt, IssuedCurrencyAmount), condition, cancel_after, finish_after
        )
    except (ValueError, TypeError) as exc:
        usage_out("build-escrow-create",
                  "build-escrow-create --from rSRC --to rDST --amount VALUE "
                  "[--cancel-after RIPPLE_TIME] [--finish-after RIPPLE_TIME]: amounts are "
                  f"positive integer drops or CUR:ISSUER:VALUE. {exc}")
        return
    kwargs = dict(account=frm, destination=to, amount=amt)
    if condition_value is not None: kwargs["condition"] = condition_value
    if cancel_value is not None: kwargs["cancel_after"] = cancel_value
    if finish_value is not None: kwargs["finish_after"] = finish_value
    tx = EscrowCreate(**kwargs)
    note_out("# EscrowCreate TX JSON - signer-ready JSON")
    json_tx_out(tx)

def tool_build_escrow_finish(frm: str, owner: str, offer_sequence: str,
                              condition: str = None, fulfillment: str = None):
    try:
        if (condition is None) != (fulfillment is None):
            raise ValueError("--condition and --fulfillment must be supplied together")
        kwargs = dict(account=frm, owner=owner,
                      offer_sequence=to_uint32(offer_sequence, "offer-sequence"))
        if condition is not None:
            fingerprint, cost = _parse_preimage_condition(condition)
            preimage = _parse_preimage_fulfillment(fulfillment)
            if len(preimage) != cost or hashlib.sha256(preimage).digest() != fingerprint:
                raise ValueError("--fulfillment does not satisfy --condition")
            kwargs["condition"] = condition.upper()
            kwargs["fulfillment"] = fulfillment.upper()
    except (ValueError, TypeError) as exc:
        usage_out("build-escrow-finish",
                  "build-escrow-finish --from rSRC --owner rOWNER --offer-sequence UINT32 "
                  f"[--condition HEX --fulfillment HEX]. {exc}")
        return
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
