# JavaScript examples

The supported JavaScript sample is build-only. It creates unsigned XRPL transaction JSON and never receives a seed/private key, signs or submits.

- `agent-receipt-nft.js` — unsigned `NFTokenMint` receipt builder.

Review output and hand it to a compatible user-owned external wallet/signing system. Verify the returned hash independently on a validated ledger with XRPL-Hermes `tx-info`.

No generic xrpl.js private-key/sign/submit recipe is certified here. Pin and audit the wallet-layer SDK separately and prove exact network, transaction-type, callback and authorization behavior before production.
