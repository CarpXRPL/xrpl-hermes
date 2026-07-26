# Wallet and Authentication — Safety Card

## Non-custodial rule

XRPL-Hermes is not a wallet. It must not receive, derive, print, persist, or transmit a seed, mnemonic, private key, or recovery secret. Hermes builds or reviews unsigned intent; the user's wallet shows and signs it; Hermes verifies the validated/finalized result.

## Capability status

| Integration | Current posture |
|---|---|
| Xaman Platform payload | external API integration; requires user-supplied application credentials; external-side-effect command is safety-skipped by autonomous tests |
| XRPL local CLI broadcast/key commands | excluded from MCP; only deliberate local use |
| Joey | unsupported/unverified; do not assume current distribution, API, XRPL support, Xahau support, or Hook transaction support |
| Crossmark | external wallet; verify current first-party API and target transaction support |
| MetaMask / EVM wallet | external wallet; verify current chain ID and decoded call |
| Privy or other embedded wallet | external/custodial-policy dependency; verify custody, export, recovery, region, and transaction-decoding behavior |
| Hardware wallet | external dependency; verify exact network and transaction-type support |

## Required handoff fields

Before creating any signing request, show:

- exact target network and network/chain ID;
- transaction type or EVM method;
- source account;
- destination/account/contract;
- asset/currency and issuer/contract;
- gross amount, fees/gas, limits, and slippage where relevant;
- destination tag, memo, Hook parameters, or calldata in decoded form;
- expiration/last-ledger constraints;
- why the action is needed and what state it changes.

Reject network ambiguity, placeholder addresses, unverified issuers/contracts, hidden calldata, unsupported transaction types, and stale wallet capability assumptions.

## Xahau boundary

No wallet is certified by this reference for Xahau `SetHook`, `Invoke`, `Remit`, or URIToken signing. Xahau uses separate Mainnet/Testnet identity and definitions. Use a current Xahau-aware serializer and a currently documented Xahau-compatible wallet, verify decoded `NetworkID` and transaction fields, and keep all keys in the wallet.

XRPL-Hermes can only calculate legacy `HookOn` and inspect validated installed hook chains. See `references/xahau-hooks.md`.

## Callback and verification

1. Generate a unique application-side intent ID and nonce.
2. Bind the wallet request to the authenticated user, expected account, exact network, and short expiry.
3. Store no secrets in URLs, logs, analytics, or callbacks.
4. Authenticate callback/webhook messages according to the wallet's current first-party specification.
5. Treat wallet/API completion as provisional.
6. Independently fetch the submitted transaction from the intended network.
7. Require validated/finalized success and compare every material field with the approved intent.
8. Record transaction hash, ledger/block, network, account, decoded fields, and verification time.
9. Do not credit balances or unlock application state on an unvalidated callback alone.

## Xaman notes

Use `xaman-payload` only with valid Xaman Platform credentials and a complete, reviewed unsigned XRPL L1 Payment. Other transaction types are rejected until independently validated. Creating a payload is an external side effect. Never expose the application secret client-side. Verify the returned payload UUID and then verify the final XRPL transaction independently.

Current first-party documentation: <https://docs.xaman.dev/>

## Acceptance requirement for any wallet claim

A compatibility claim requires a current official source, pinned app/SDK version, exact network and transaction type, exercised unsigned-to-wallet flow, decoded review screen, user rejection test, validated-result verification, and documented failure/recovery behavior. Without that evidence, label it external/unverified.
