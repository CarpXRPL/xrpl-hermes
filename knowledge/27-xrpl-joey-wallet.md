# Joey Wallet — Unsupported/Unverified Boundary

Joey’s current distribution, official domain/repository, injected-provider API, supported networks, transaction types, custody model and security behavior were not certified for XRPL-Hermes v1.9.0.

## Rules

- Do not direct users to a remembered extension listing or repository.
- Do not call guessed browser globals or signing methods.
- Do not claim XRPL, Xahau/Hooks, TrustSet, NFT, multisig, hardware-wallet or mobile support.
- Do not claim keys remain local or transaction details are displayed without current first-party evidence and a reproduced acceptance test.
- Do not use Joey as a fallback for Xaman or any other wallet.

## Acceptance required

Before adding support, obtain current first-party documentation and reproduce:

1. authentic distribution/domain identity;
2. account connection and permission lifecycle;
3. exact target network and transaction-type support;
4. user review/rejection behavior;
5. callback/error/expiry semantics;
6. decoded transaction equality before authorization;
7. returned hash/blob handling and validated-ledger verification;
8. key/custody and recovery behavior.

Until then, use the generic external-signer handoff in `references/xrpl-wallets-auth.md`.
