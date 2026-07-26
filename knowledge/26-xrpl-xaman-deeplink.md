# Xaman Payload Handoff — Guarded External Side Effect

## Status

`xaman-payload` can create a guarded external Xaman Platform request for a locally validated XRPL L1 Payment only. It is denied over MCP and is not signing, submission, settlement, or validated-ledger proof.

Creating a payload is **not** signing, submission, validation or transaction success.

## Local validation

Before contacting Xaman, the tool:

- requires transaction JSON to be an object;
- rejects recursive seed/secret/private-key fields;
- certifies XRPL L1 `Payment` intents only;
- validates classic Account/Destination addresses, positive XRP or issued-currency Amount, and optional Payment fields;
- rejects signed JSON;
- rejects Xahau and non-XRPL payloads;
- rejects malformed API responses;
- requires a valid payload UUID and trusted HTTPS `xumm.app` signing URL.

## Safe workflow

1. Build and review an unsigned XRPL L1 Payment intent.
2. Confirm network, transaction type, complete addresses, asset/amount and consequences.
3. Create the external payload only with configured app credentials.
4. User reviews and approves in Xaman.
5. Resolve provider status.
6. Independently fetch and verify the expected validated XRPL transaction/result.

Do not treat `PayloadUUID`, `SignURL`, QR generation, `pushed`, or provider approval as ledger finality.

## Credential boundary

The application secret can create signing requests on behalf of the application. Keep it outside chat, source, browser code and MCP. Rotate it if exposed.

Official source: https://docs.xaman.dev/
