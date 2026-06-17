#!/usr/bin/env node
/**
 * Build an UNSIGNED NFTokenMint that records what an agent did, or how a skill
 * improved, as an on-chain receipt — xrpl.js builder layer only.
 *
 * An "agent receipt" is provenance you don't own: an account mints a small NFT
 * whose URI carries a compact, tamper-evident summary of a run or a skill
 * evolution (v1 -> v2). The ledger gives it a timestamp (ledger index), an
 * author (the minting account), and public verifiability (anyone can fetch the
 * NFT and decode the URI). It is the audit-trail idea, kept honest.
 *
 * This mirrors XRPL-Hermes's signer-separated model and is the safe twin of the
 * common "agent mints its own NFT" demo:
 *
 *   builder layer (this file) -> typed, UNSIGNED NFTokenMint JSON
 *   wallet / signing layer    -> autofill -> human preview -> sign -> submitAndWait
 *
 * It NEVER reads a seed, NEVER signs, NEVER submits, and does not connect to a
 * node. There is no autonomous minting here: the agent prepares the receipt; a
 * human-held wallet decides whether to record it. See
 * skills/agent-receipt-flow.md and references/agentic-payments.md.
 *
 * Run:
 *   cd examples/js && npm install
 *   node agent-receipt-nft.js
 *
 * Then hand the printed JSON to your wallet/signing stack (Xaman, Crossmark, or
 * your own xrpl.js signer) to autofill -> preview -> sign locally -> submitAndWait.
 */
"use strict";

let xrpl;
try {
  xrpl = require("xrpl");
} catch (e) {
  console.error(
    "This example needs xrpl.js. Install it first:\n" +
      "  cd examples/js && npm install\n"
  );
  process.exit(1);
}

// --- Inputs (placeholders — replace with a real classic address) -----------
const MINTER = "rSENDERxxxxxxxxxxxxxxxxxxxxxxxxx"; // the account recording the receipt

// taxon groups a "collection"; use one dedicated value to group all your
// agent receipts so they are easy to query later.
const RECEIPT_TAXON = 1;

// Flags: 8 (tfTransferable) lets others hold/verify the receipt — the default,
// matching the Python `build-nft-mint` command. Use Flags: 0 for a
// non-transferable (soulbound) receipt bound to the minting account when you
// want pure provenance that can never change hands.
const FLAGS = 8;

// The compact, on-ledger summary. Keep it small: XRPL's NFTokenMint URI field
// holds at most 256 bytes. For anything larger, switch to "pointer" mode below
// and keep the full record off-ledger (IPFS / your API). This default encodes
// to well under the limit so `node agent-receipt-nft.js` runs out of the box.
const RECEIPT = {
  t: "skill-evolution",      // receipt type: agent-run | skill-evolution | audit
  skill: "xrpl_send_payment",
  v: "v1->v2",               // what changed
  agent: "hermes",
  net: "testnet",
  ts: "2026-06-16",          // ISO date; ledger index is the authoritative time
};

// --- Encode the receipt into a 256-byte-safe URI ---------------------------
// XRPL URI max = 256 bytes on-ledger, stored as hex (so <= 512 hex chars).
// base64 inflates ~33%, so the check MUST be on the final hex length — checking
// the raw JSON would pass payloads that then fail on-ledger with temMALFORMED.
const URI_MAX_HEX = 512;

function inlineDataUri(receipt) {
  const json = JSON.stringify(receipt);
  const dataUri = `data:application/json;base64,${Buffer.from(json).toString("base64")}`;
  const hex = xrpl.convertStringToHex(dataUri).toUpperCase();
  if (hex.length > URI_MAX_HEX) {
    throw new Error(
      `Receipt too large for an inline URI: ${hex.length} hex chars ` +
        `(max ${URI_MAX_HEX} = 256 bytes). Trim the summary, or use pointer ` +
        `mode: put the full record on IPFS/your API and set the URI to that link.`
    );
  }
  return hex;
}

// Pointer mode (documented fallback for large records — not the default):
//   const POINTER = "ipfs://bafy.../receipt.json";        // or https://...
//   const uriHex  = xrpl.convertStringToHex(POINTER).toUpperCase();
// The full receipt lives off-ledger; the NFT just anchors a verifiable link.

const uriHex = inlineDataUri(RECEIPT);

// --- Build the unsigned, signer-ready NFTokenMint --------------------------
const mint = {
  TransactionType: "NFTokenMint",
  Account: MINTER,
  NFTokenTaxon: RECEIPT_TAXON,
  Flags: FLAGS,
  TransferFee: 0,
  URI: uriHex,
  // A human-readable label for explorers, alongside the machine-readable URI.
  Memos: [
    {
      Memo: {
        MemoData: xrpl.convertStringToHex(`hermes:${RECEIPT.t}-receipt`),
        MemoType: xrpl.convertStringToHex("text/plain"),
      },
    },
  ],
  // Empty SigningPubKey marks this as unsigned/signer-ready, exactly like the
  // Python builder. The wallet layer replaces it when it signs.
  SigningPubKey: "",
  // No Fee / Sequence / LastLedgerSequence — autofill populates them at signing.
};

// --- Output ----------------------------------------------------------------
console.log("# Unsigned agent-receipt NFTokenMint (xrpl.js builder layer) — paste into your wallet/signing stack");
console.log(`# URI carries: ${JSON.stringify(RECEIPT)}`);
console.log(`# URI hex length: ${uriHex.length}/${URI_MAX_HEX} chars`);
console.log(JSON.stringify(mint, null, 2));
console.log(
  "\n# Next: wallet layer runs autofill -> human preview -> sign locally -> submitAndWait.\n" +
    "# Then read it back with the Python CLI: nft-info <NFTokenID>."
);
