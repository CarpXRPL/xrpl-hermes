#!/usr/bin/env node
/**
 * Build an UNSIGNED RLUSD (issued-currency) Payment with xrpl.js — builder only.
 *
 * Twin of the Python `build-payment --cur <hex> --iss <issuer>` flow, focused on
 * the one thing that trips people up: currency codes longer than 3 characters
 * (like "RLUSD") MUST be sent as a 160-bit (40 hex char) code on-ledger. The
 * 5-letter literal "RLUSD" is invalid as an on-ledger currency.
 *
 * Builder layer only: no signing, no submission, no seed, no node connection.
 * Fee / Sequence / LastLedgerSequence are left for the wallet layer's autofill.
 *
 * Run:
 *   cd examples/js && npm install
 *   node build-rlusd-payment.js
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

/**
 * Normalize a currency code to its on-ledger form (mirrors the Python
 * normalize_currency_code helper):
 *   - 3-char ISO-style codes pass through (e.g. "USD")
 *   - 4-20 char symbols become the 160-bit hex code, zero-padded to 40 chars
 */
function toCurrencyHex(code) {
  if (code.length <= 3) return code;
  return Buffer.from(code, "ascii").toString("hex").toUpperCase().padEnd(40, "0");
}

// --- Inputs ----------------------------------------------------------------
const SENDER = "rSENDERxxxxxxxxxxxxxxxxxxxxxxxxx"; // your account
const DEST = "rDESTxxxxxxxxxxxxxxxxxxxxxxxxxxxx"; // recipient
// RLUSD mainnet issuer — public, re-verify on-ledger before production.
const RLUSD_ISSUER = "rMxCKbEDwqr76QuheSUMdEGf4B9xJ8m5De";
const AMOUNT = "25.50"; // RLUSD has dollar-like decimals; send a string, not a float

const RLUSD_HEX = toCurrencyHex("RLUSD"); // 524C555344000000000000000000000000000000

// Sanity: the literal would be wrong; the hex is what the ledger expects.
if (RLUSD_HEX !== "524C555344000000000000000000000000000000") {
  throw new Error("RLUSD currency hex mismatch — check toCurrencyHex()");
}

// --- Build the unsigned issued-currency Payment ----------------------------
// Reminder: the DESTINATION must already hold an RLUSD trust line to the issuer
// (build one with the Python `build-trustset` command or a TrustSet tx) before
// this payment can deliver. See references/rlusd.md.
const payment = {
  TransactionType: "Payment",
  Account: SENDER,
  Destination: DEST,
  Amount: {
    currency: RLUSD_HEX, // 160-bit hex, NOT the literal "RLUSD"
    issuer: RLUSD_ISSUER,
    value: AMOUNT,
  },
  SourceTag: 20260616, // tag agent-initiated transfers
  Memos: [
    {
      Memo: {
        MemoData: xrpl.convertStringToHex("agent:invoice-7782"),
      },
    },
  ],
  SigningPubKey: "", // unsigned / signer-ready
  // No Fee / Sequence / LastLedgerSequence — the wallet layer autofills them.
};

// --- Output ----------------------------------------------------------------
console.log("# Unsigned RLUSD Payment (xrpl.js builder layer)");
console.log(`# RLUSD currency code (160-bit hex): ${RLUSD_HEX}`);
console.log(JSON.stringify(payment, null, 2));
console.log(
  "\n# Next: ensure the destination trust line exists, then the wallet layer autofills -> signs -> submitAndWait."
);
