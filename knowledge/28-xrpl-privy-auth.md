# Privy Embedded Wallet/Auth — External Dependency Boundary

## Status

Privy is an external authentication and embedded-wallet provider. No Privy SDK version, XRPL account model, EVM chain support, custody/recovery mode, transaction schema or signing behavior is certified by XRPL-Hermes v1.9.0.

XRPL-Hermes does not route seeds/private keys through Privy examples and does not claim Privy supports an XRPL network or transaction type without current first-party evidence.

## Requirements before integration

1. Pin current official Privy documentation and SDK version.
2. Establish whether the requested flow is XRPL L1 or an EVM network; never conflate their address/signature models.
3. Document who controls/export/recovery keys and what the application/provider can sign.
4. Verify exact network/chain ID and transaction/call support.
5. Keep auth tokens and server credentials outside browser bundles and agent prompts.
6. Require explicit user review and authorization for each value-moving action.
7. Reconcile the signed output against the original decoded intent.
8. Verify the final transaction independently on the correct validated ledger/chain.
9. Test rejection, expiry, callback authentication, replay resistance and account recovery.

## Current workflow

Use a compatible user-owned external signer with current network/type evidence. XRPL-Hermes builds unsigned intent and verifies final state. Its built-in `xaman-payload` path is separate, Payment-only and does not establish Privy compatibility.

Reviewed: **2026-07-26**.
