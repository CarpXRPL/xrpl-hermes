#!/usr/bin/env node
/**
 * Build an UNSIGNED XRP Payment with xrpl.js — builder layer only.
 *
 * This is the TypeScript/JavaScript twin of the Python `build-payment` CLI
 * command. It mirrors XRPL-Hermes's signer-separated model:
 *
 *   builder layer (this file)  -> typed JSON, SourceTag/DestinationTag/Memos
 *   wallet / signing layer     -> autofill -> preview -> sign -> submitAndWait
 *
 * It NEVER signs, NEVER submits, and NEVER touches a seed. It does not even
 * connect to a node: Fee / Sequence / LastLedgerSequence are deliberately left
 * unset so the wallet/signing layer fills them via `autofill` (Safety rule 7).
 *
 * Run:
 *   cd examples/js && npm install
 *   node build-xrp-payment.js
 *
 * Then hand the printed JSON to your wallet/signing stack (Xaman, Crossmark,
 * or your own xrpl.js signer) to autofill, preview to a human, sign locally,
 * and `submitAndWait`. See references/agentic-payments.md.
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

// --- Inputs (placeholders — replace with real classic addresses) -----------
const SENDER = "rSENDERxxxxxxxxxxxxxxxxxxxxxxxxx"; // your account (Account)
const DEST = "rDESTxxxxxxxxxxxxxxxxxxxxxxxxxxxx"; // recipient (Destination)
const AMOUNT_XRP = "1"; // human XRP; converted to drops below

// SourceTag tags every agent-initiated payment for attribution/accounting.
// DestinationTag is required by many exchanges/hosted wallets.
const SOURCE_TAG = 20260616;
const DEST_TAG = 42;
const MEMO_TEXT = "agent:order-4417"; // on-chain audit trail / invoice id

// --- Build the unsigned, signer-ready Payment object -----------------------
const payment = {
  TransactionType: "Payment",
  Account: SENDER,
  Destination: DEST,
  // Always convert via xrpToDrops — never hand-write drops or use raw floats.
  Amount: xrpl.xrpToDrops(AMOUNT_XRP), // "1000000"
  SourceTag: SOURCE_TAG,
  DestinationTag: DEST_TAG,
  Memos: [
    {
      Memo: {
        // MemoData is stored on-ledger as hex; xrpl.js encodes it for us.
        MemoData: xrpl.convertStringToHex(MEMO_TEXT),
      },
    },
  ],
  // Empty SigningPubKey marks this as unsigned/signer-ready, exactly like the
  // Python builder. The wallet layer replaces it when it signs.
  SigningPubKey: "",
  // NOTE: no Fee, Sequence, or LastLedgerSequence here on purpose — autofill
  // populates them from a live node at signing time.
};

// --- Output ----------------------------------------------------------------
console.log("# Unsigned XRP Payment (xrpl.js builder layer) — paste into your wallet/signing stack");
console.log(JSON.stringify(payment, null, 2));
console.log(
  "\n# Next: wallet layer runs autofill -> preview to a human -> sign locally -> submitAndWait -> read the result code."
);
