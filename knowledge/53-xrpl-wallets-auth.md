# Wallet Authentication and Signing — Certification Boundary

## Custody rule

XRPL-Hermes builds unsigned intent and verifies validated results. It does not receive, generate, store or use a user's seed/private key in an integration workflow.

Wallet/platform support is not universal. Verify current first-party evidence for the exact network, transaction type, callback/auth contract and user-authorization behavior before naming a wallet as compatible.

## Xaman

The local-only `xaman-payload` command is the sole implemented hosted-payload helper. It currently:

- accepts locally validated unsigned XRPL L1 Payments only;
- rejects secrets recursively, signatures, unsupported transaction types and Xahau/non-XRPL payloads;
- validates Payment addresses, amount and model fields before contacting Xaman;
- requires configured application credentials;
- validates the returned UUID and trusted HTTPS signing URL;
- reports whether the real external side effect was created;
- remains denied over MCP.

Payload creation is not login proof, signing, submission or final success. Verify the wallet-selected network and the final validated XRPL transaction independently.

Do not bypass the guarded helper with raw hosted-payload HTTP snippets in product guidance.

## Other wallets/providers

Joey support is unsupported/unverified. Privy and MetaMask are external dependencies with separate network/custody models. Do not claim compatibility from a remembered SDK example. Use a generic external-signer boundary until current first-party evidence and a reproduced flow exist.

## Acceptance checklist

1. Pin provider docs/SDK/API version.
2. Prove exact network and transaction-type support.
3. Define custody, export/recovery and application authority.
4. Authenticate callbacks/webhooks and prevent replay.
5. Decode signed output and compare it with original intent.
6. Verify final network, hash, validated/final status and result code.
7. Test reject, cancel, expiry, timeout, malformed callback and provider outage.
