# RWA tokenization on XRPL

XRPL-Hermes provides ledger primitives, not legal issuance, custody, valuation, identity, transfer-agent, or regulatory services.

## Available primitives

| Requirement | XRPL primitive | Hermes surface |
|---|---|---|
| Issuer configuration | `AccountSet` | `build-account-set` |
| Holder relationship | `TrustSet` | `build-trustset`, `trustlines` |
| Distribution/redemption | `Payment` | `build-payment`, `tx-info` |
| Clawback | `Clawback` | `build-clawback` |
| Time lock | `EscrowCreate/Finish/Cancel` | escrow builders |
| Whitelisted deposits | `DepositPreauth` | `build-deposit-preauth` |
| Multisign policy | `SignerListSet` | `build-signer-list-set` |
| Secondary liquidity | DEX/AMM | offer and AMM builders/reads |
| MPT issuance/authorization | MPTokens | two MPT builders |

All transaction commands build unsigned JSON.

## Required off-ledger controls

A production RWA program normally needs independently accepted systems for:

- legal entity and issuance documents;
- investor eligibility and jurisdiction checks;
- identity, sanctions, and ongoing compliance;
- custody and proof of the underlying asset;
- valuation/NAV policy and independent attestations;
- subscriptions, redemptions, distributions, and tax reporting;
- transfer-agent records and dispute handling;
- wallet authorization, signing, recovery, and transaction broadcast.

XRPL ledger balances do not prove title to an off-ledger asset.

## Technical workflow

1. Define the legal claim and map it to exact ledger rights.
2. Choose issued currency or MPT based on required controls actually available on the intended network.
3. Configure issuer policy before distribution.
4. Build and review holder, issuance, payment, escrow, or liquidity intent.
5. Authorize in the user-controlled wallet under the approved governance policy.
6. Verify the validated transaction and resulting ledger objects.
7. Reconcile ledger state with the legal/custody/transfer-agent system.

## Important gaps

- The current trust-line builder does not expose issuer authorization flags, so `RequireAuth` token issuance is not a complete shipped workflow.
- XRPL-Hermes does not implement investor onboarding, NAV publication, document storage, dividend automation, redemption orchestration, or secondary-market compliance enforcement.
- MPT support is limited to issuance creation and authorization builders.

Do not market an RWA as compliant, fully reserved, redeemable, bankruptcy-remote, or independently audited based only on XRPL transactions.
