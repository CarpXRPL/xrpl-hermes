# Treasury Tool Product Flow

Use this product playbook when the user wants a DAO/project treasury dashboard, multisig coordination app, signer proposal tool, or funds-monitoring cockpit.

## Product promise

A non-custodial treasury cockpit:

```text
read-only visibility → unsigned proposal → external signatures → assembled multisigned submit → ledger-confirmed receipt
```

The product never holds a quorum or any signer key.

## Triggers

- "build a treasury tool"
- "DAO treasury dashboard"
- "multisig proposal app"
- "signer coordination"
- "project funds dashboard"

## Target user

Project teams, communities, small funds, grant programs, and signer groups.

## XRPL primitives

- SignerListSet
- multisigned transaction submission
- Tickets for parallel proposal slots
- Escrow for vesting/locked payments
- account objects and reserves
- RegularKey hygiene

## Read first

- `skills/build-xrpl-product-flow.md`
- `skills/multisig-safety-flow.md`
- `skills/treasury-monitor-flow.md`
- `skills/account-access-safety-flow.md`
- `knowledge/12-xrpl-multisig.md`
- `knowledge/13-xrpl-tickets.md`
- `knowledge/42-xrpl-treasury.md`
- `knowledge/40-xrpl-monitoring.md`

## Commands/tools

- `account rTREASURY`
- `account_objects rTREASURY signer_list`
- `account-tx rTREASURY LIMIT`
- `subscribe streams=transactions`
- `server-info`
- `build-signer-list-set`
- escrow/check/ticket builders as needed
- `submit-multisigned` for already-signed JSON only

## MVP deliverable

1. Read-only dashboard: balances, reserve headroom, signer list, quorum, open escrows/checks/tickets, recent txs.
2. Proposal builder: creates unsigned JSON and a decoded preview.
3. Signature collection checklist/link handoff; product does not sign.
4. Assembly/submit path for already-multisigned JSON.
5. Receipt and alert after `validated: true`.

## Testnet demo checklist

- 2-of-3 signer list setup rehearsed on testnet.
- One payment proposal signed externally by enough signers.
- `submit-multisigned` accepts already-signed JSON and validates.
- One rejected/expired proposal path is shown.

## Mainnet-safe checklist

- Lockout linter: quorum cannot exceed total weights; removing signer lists with master disabled is blocked/warned.
- Alerts are tuned before funds migrate.
- Proposal amount caps and allowlists are available.
- Signer rotation and emergency contact plan exist.
- Product never holds signers' seeds/private keys.

## Common failure modes

- Becoming a signing service.
- UI allows unsatisfiable quorum.
- Losing funds through master-key/regular-key/signer-list lockout.
- Treating collected signatures as enough without validating ledger result.
- Parallel proposals conflict because Tickets are not handled.
