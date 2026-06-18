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


# --- examples/example-agent-receipt.py: the build-only Python exemplar --------

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_RECEIPT_EXAMPLE = _ROOT / "examples" / "example-agent-receipt.py"


def test_example_agent_receipt_runs_and_emits_unsigned_mint():
    proc = subprocess.run([sys.executable, str(_RECEIPT_EXAMPLE)],
                          cwd=_ROOT, capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, proc.stderr
    # Strip comment / blank lines, leaving the pretty-printed NFTokenMint JSON.
    body = "\n".join(l for l in proc.stdout.splitlines()
                     if not l.lstrip().startswith("#")).strip()
    tx = json.loads(body)
    assert tx["TransactionType"] == "NFTokenMint"
    assert tx["SigningPubKey"] == ""          # unsigned / signer-ready
    assert len(tx["URI"]) <= 512              # 256-byte on-ledger URI budget
    assert "Fee" not in tx and "Sequence" not in tx  # left for wallet autofill
    decoded = bytes.fromhex(tx["URI"]).decode()
    payload = base64.b64decode(decoded.split(",", 1)[1])
    assert json.loads(payload)["skill"] == "xrpl_send_payment"


def test_example_agent_receipt_is_build_only():
    """No seed, no signing, no submission, no node client — the source proves it
    is the builder layer, not the wallet layer (executable calls, not the
    documentary 'submit_and_wait' mention in the next-steps print)."""
    src = _RECEIPT_EXAMPLE.read_text()
    assert "from_seed" not in src
    assert "submit_and_wait(" not in src
    assert "JsonRpcClient" not in src
    assert ".sign(" not in src
