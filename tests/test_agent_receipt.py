#!/usr/bin/env python3
"""Agent-receipt primitive: build-nft-mint must emit an unsigned, size-safe
NFTokenMint that carries a compact receipt URI.

These lock the CLI/Python side of skills/agent-receipt-flow.md and the safe
behavior the JS twin (examples/js/agent-receipt-nft.js) mirrors. Node-free so
they run anywhere the rest of the suite does.
"""
import base64
import io
import json
from contextlib import redirect_stdout

import pytest
from xrpl.models.exceptions import XRPLModelException

from scripts.tools.nfts import tool_build_nft_mint


SRC = "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe"


def capture_json(fn, *args, **kwargs):
    buf = io.StringIO()
    with redirect_stdout(buf):
        fn(*args, **kwargs)
    return json.loads(buf.getvalue())


def test_build_nft_mint_emits_unsigned_signer_ready_json():
    tx = capture_json(tool_build_nft_mint, SRC, taxon=1, uri="ipfs://example")
    assert tx["TransactionType"] == "NFTokenMint"
    assert tx["Account"] == SRC
    # Empty SigningPubKey is the unsigned/signer-ready marker — the builder
    # never signs. A receipt is recorded by the user's wallet, not the agent.
    assert tx["SigningPubKey"] == ""


def test_build_nft_mint_hex_encodes_text_uri():
    tx = capture_json(tool_build_nft_mint, SRC, taxon=1, uri="ipfs://example")
    assert tx["URI"] == "ipfs://example".encode().hex().upper()


def test_build_nft_mint_passes_through_existing_hex_uri():
    already_hex = "ipfs://example".encode().hex().upper()
    tx = capture_json(tool_build_nft_mint, SRC, taxon=1, uri=already_hex)
    # Already-hex input is not double-encoded — it passes through uppercased.
    assert tx["URI"] == already_hex


def test_build_nft_mint_receipt_data_uri_round_trips():
    """A compact base64 data: URI survives build -> on-ledger hex -> decode."""
    receipt = {"t": "skill-evolution", "skill": "xrpl_send_payment", "v": "v1->v2"}
    data_uri = "data:application/json;base64," + base64.b64encode(
        json.dumps(receipt).encode()).decode()
    tx = capture_json(tool_build_nft_mint, SRC, taxon=1, uri=data_uri)
    # XRPL URI max is 256 bytes == 512 hex chars; a compact receipt fits.
    assert len(tx["URI"]) <= 512
    decoded = bytes.fromhex(tx["URI"]).decode()
    assert decoded == data_uri
    b64 = decoded.split(",", 1)[1]
    assert json.loads(base64.b64decode(b64)) == receipt


def test_build_nft_mint_rejects_oversize_uri():
    """Over-256-byte URIs are refused (xrpl-py enforces 512 hex chars), so an
    oversized receipt can never produce a temMALFORMED mint. Use pointer mode."""
    with pytest.raises(XRPLModelException, match="512"):
        tool_build_nft_mint(SRC, taxon=1, uri="x" * 300)
