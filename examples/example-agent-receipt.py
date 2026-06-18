#!/usr/bin/env python3
"""
☤ xrpl-hermes — Build an UNSIGNED agent / skill receipt (NFTokenMint).

The build-only Python exemplar. It constructs signer-ready transaction JSON and
prints it — it never reads a seed, never signs, and never submits, exactly like
the `build-*` CLI commands and the examples/js/ twins. Signing stays in your
wallet/signing layer (the user's stack). Contrast the sign+submit examples in
this directory: those are the *wallet layer* (see ./README.md).

An "agent receipt" records what an agent did, or how a skill improved (v1->v2),
as a small NFT whose URI carries a compact, tamper-evident summary — provenance
you don't own (timestamp via ledger index, author = minting account, public
verifiability). Full flow: ../skills/agent-receipt-flow.md.

Usage:
    python3 examples/example-agent-receipt.py
    # -> prints unsigned NFTokenMint JSON; hand it to your wallet to sign.
"""

import base64
import json

from xrpl.models.transactions import NFTokenMint

# XRPL NFTokenMint URI max = 256 bytes on-ledger, stored as hex (<= 512 hex chars).
URI_MAX_HEX = 512

# Taxon groups a "collection"; use one dedicated value to group your receipts.
RECEIPT_TAXON = 1
# Flags 8 (tfTransferable) lets others hold/verify the receipt (matches the
# build-nft-mint default); use 0 for a non-transferable (soulbound) provenance
# receipt bound to the minting account.
FLAGS = 8


def receipt_data_uri(receipt: dict) -> str:
    """Compact base64 data: URI for an inline receipt, size-checked AFTER encoding.

    base64 + hex inflate the payload, so the 256-byte limit must be checked on
    the final hex length — checking the raw JSON would pass payloads that then
    fail on-ledger with temMALFORMED. For large records use a pointer URI
    instead (ipfs://... or https://...) and keep the full record off-ledger.
    """
    # Compact separators (no spaces) — match the examples/js twin and waste no
    # bytes against the 256-byte budget.
    compact = json.dumps(receipt, separators=(",", ":"))
    data_uri = "data:application/json;base64," + base64.b64encode(compact.encode()).decode()
    hex_len = len(data_uri.encode().hex())
    if hex_len > URI_MAX_HEX:
        raise ValueError(
            f"Receipt too large for an inline URI: {hex_len} hex chars "
            f"(max {URI_MAX_HEX} = 256 bytes). Trim the summary, or use a "
            f"pointer URI (ipfs://... / https://...) to off-ledger metadata.")
    return data_uri


def build_receipt_mint(minter: str, receipt: dict) -> NFTokenMint:
    """Construct an UNSIGNED, signer-ready NFTokenMint. No seed, no signing."""
    uri_hex = receipt_data_uri(receipt).encode().hex().upper()
    return NFTokenMint(
        account=minter,
        nftoken_taxon=RECEIPT_TAXON,
        flags=FLAGS,
        transfer_fee=0,
        uri=uri_hex,
    )


def main():
    # Placeholder — replace with the account that will record the receipt.
    minter = "rSENDERxxxxxxxxxxxxxxxxxxxxxxxxx"
    receipt = {
        "t": "skill-evolution",      # receipt type: agent-run | skill-evolution | audit
        "skill": "xrpl_send_payment",
        "v": "v1->v2",               # what changed
        "agent": "hermes",
        "net": "testnet",
        "ts": "2026-06-17",          # ISO date; the ledger index is the authoritative time
    }

    tx = build_receipt_mint(minter, receipt)

    print("# Unsigned agent-receipt NFTokenMint (Python builder layer) — hand to your wallet to sign")
    print(f"# URI carries: {json.dumps(receipt, separators=(',', ':'))}")
    # to_xrpl() emits the ledger/PascalCase form with an empty SigningPubKey —
    # the unsigned/signer-ready marker. Your wallet layer replaces it when it signs.
    print(json.dumps(tx.to_xrpl(), indent=2))
    print("\n# Next: your wallet/signing layer runs autofill -> human preview -> sign -> submit_and_wait.")
    print("# Then read it back with the CLI: python3 scripts/xrpl_tools.py nft-info <NFTokenID>")


if __name__ == "__main__":
    main()
