# RWA / Compliance Rails Product Flow

Use this playbook when the user wants technical rails for a regulated, permissioned, KYC-gated, RWA, institutional, or compliance-sensitive issuance product.

This is technical architecture only. It is not legal advice.

## Product promise

A technical issuance plan that maps policy requirements to XRPL primitives while loudly preserving the legal/counsel boundary.

## Triggers

- "tokenize real estate"
- "RWA issuance platform"
- "KYC-gated token"
- "compliant token platform"
- "institutional issuance"

## Target user

Fintech/RWA builders working with counsel and compliance operators.

## XRPL primitives

- RequireAuth and authorized trustlines
- Credentials when amendment/network support allows
- DepositPreauth
- Clawback / freeze policy
- MPTs as an alternate asset model
- issuer flags and domain identity

## Read first

- `skills/build-xrpl-product-flow.md`
- `skills/issuer-first-mint-flow.md`
- `skills/clawback-flow.md`
- `knowledge/59-rwa-tokenization.md`
- `knowledge/58-rlusd-operations.md`
- `knowledge/07-xrpl-clawback.md`
- `knowledge/08-xrpl-mpts.md`

## Commands/tools

- `amendment NAME`
- `build-account-set`
- `build-trustset` plus operation-flow guidance for authorization/freeze semantics
- `build-credential-create`
- `build-credential-accept`
- `build-credential-delete`
- `build-deposit-preauth`
- `build-clawback`
- `build-mpt-issuance-create`

## MVP deliverable

A testnet technical gate:

1. Issuer has RequireAuth where appropriate.
2. Credential/authorization flow is modeled if supported.
3. Authorized holder can receive/transfer.
4. Unauthorized holder fails.
5. Freeze/clawback policy is documented and rehearsed if used.
6. Legal/compliance responsibilities are listed as external requirements.

## Testnet demo checklist

- Live amendment checks before promising Credentials/MPT behavior.
- Authorized and unauthorized paths both demonstrated.
- One clawback/freeze rehearsal if the policy uses it.
- No KYC/PII is stored on-ledger or in memos.

## Mainnet-safe checklist

- Counsel boundary appears in product docs and onboarding.
- Policy doc says when freeze/clawback/authorization is used.
- Clawback is configured before any trustline if required.
- PII/KYC data remains off-ledger.
- Issuer domain/TOML identity is verified.

## Common failure modes

- Implying compliance is achieved by a flag.
- Choosing IOU vs MPT by trend instead of requirements.
- Wanting clawback after supply has circulated.
- Storing sensitive identity data in public memos.
- Giving legal conclusions instead of technical rails.
