# Wallet Signing UX Product Flow

Use this product playbook when the user wants wallet login, transaction signing handoff, Xaman/Joey/Privy/MetaMask integration, or a reusable "sign this unsigned XRPL JSON" component.

This is a **cross-cutting product component**: every XRPL product that moves value should depend on it instead of inventing signing UX again.

## Product promise

A non-custodial signing path:

```text
connect/identify wallet → show decoded unsigned JSON → QR/deeplink/manual handoff → wallet signs → product confirms with tx-info → receipt
```

XRPL-Hermes never holds keys and never signs. The product makes the signing boundary obvious to the user.

## Triggers

- "add wallet login"
- "integrate Xaman"
- "how should users sign in my app?"
- "build wallet handoff UX"
- "sign this JSON from a web app"
- any product flow that emits unsigned XRPL transaction JSON

## Target user

Builders creating web apps, dashboards, bots, launch tools, payment apps, or agent workflows where humans approve XRPL actions.

## Read first

- `knowledge/26-xrpl-xaman-deeplink.md`
- `knowledge/27-xrpl-joey-wallet.md`
- `knowledge/28-xrpl-privy-auth.md`
- `knowledge/29-xrpl-metamask-evm.md` for EVM Sidechain signing only
- `knowledge/53-xrpl-wallets-auth.md`
- `skills/build-xrpl-product-flow.md`

## Commands/tools

- `validate-address rADDR`
- `xaman-payload '{...}'` when Xaman API keys are configured
- `decode TX_BLOB` for signed material review
- `tx-info HASH` for final validated confirmation
- the relevant `build-*` command from the operation flow

## MVP deliverable

A wallet-handoff component spec with three paths:

1. **Manual path** — copy unsigned JSON into a wallet/developer signing surface. Requires no API keys.
2. **Xaman path** — create a payload/QR/deeplink with `xaman-payload` where credentials exist.
3. **Callback/confirmation path** — after signing/submission, verify the tx hash with `tx-info` and require `validated: true` before marking complete.

## Required UX rules

Before signing, the UI shows:

- network
- account signing
- destination/counterparty
- asset and amount/limit
- issuer for issued currencies
- `SourceTag`/`DestinationTag`
- decoded `Memos`
- operation consequence, especially irreversible operations
- clear label: **unsigned JSON; your wallet signs**

No truncated addresses in the final approval preview.

## Testnet demo checklist

- Build one unsigned Payment on testnet.
- Show decoded preview in the UI.
- Sign externally through Xaman/manual path.
- Confirm with `tx-info` and require `validated: true`.
- Show failure state for an unvalidated/missing hash.

## Mainnet-safe checklist

- Destination tag requirements are checked for exchange/hosted destinations.
- Payload expiration/error states are handled.
- Product never treats wallet-approved as ledger-final; it waits for `tx-info`.
- No seed/private-key fields exist in forms, logs, URLs, browser storage, or env examples.

## Common failure modes

- Blind-signing UX with no decoded preview.
- Treating payload creation as payment completion.
- Asking users to paste a seed for convenience.
- Storing signed blobs as if they are private keys, or treating public signed data as sufficient proof without `tx-info`.
- Mixing XRPL L1 wallets with EVM Sidechain wallets without explaining which network is being signed.
