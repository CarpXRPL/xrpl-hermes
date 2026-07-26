# Token Launch Product Flow

Use this product playbook when the user wants to build a launchpad, token creator platform, issuer wizard, or launch tooling for other creators.

This is product altitude. If the user wants to launch **their own** token now, route to `skills/issuer-first-mint-flow.md` or `skills/token-launch-flow.md` instead.

## Product promise

A non-custodial token launch wizard:

```text
creator connects wallet → wizard explains irreversible choices → emits unsigned JSON per step → creator signs externally → app verifies live state before unlocking next step
```

The platform never holds creator issuer keys.

## Triggers

- "build a token launch platform"
- "make a launchpad"
- "token creator tool"
- "issuer wizard"
- "help creators issue tokens"

## Target user

Builders serving token creators, communities, and projects that need safer issuance tooling.

## XRPL primitives

- AccountSet flags/domain/tick size/transfer rate
- TrustSet
- issued-currency Payment / issuer first mint
- OfferCreate
- AMMCreate/AMMDeposit where liquidity launch is in scope
- Clawback/freeze decisions via operation flows; RequireAuth trust-line authorization is not shipped

## Read first

- `skills/build-xrpl-product-flow.md`
- `skills/wallet-signing-ux-product-flow.md`
- `skills/issuer-first-mint-flow.md`
- `skills/token-launch-flow.md`
- `skills/clawback-flow.md`
- `knowledge/21-xrpl-token-model.md`
- `knowledge/22-xrpl-token-issuance.md`
- `knowledge/24-xrpl-deploy-guide.md`
- `knowledge/38-xrpl-minting-ops.md`

## Commands/tools

- `account rISSUER`
- `trustlines rADDR CUR`
- `build-account-set`
- `build-trustset`
- issuer first mint through `build-cross-currency-payment --deliver CUR:rISSUER:VALUE --send-max CUR:rISSUER:VALUE`
- `build-offer`
- `amm-info`
- `build-amm-create` / `build-amm-deposit` when liquidity stage is included
- `token-intel CUR rISSUER` for post-launch self-report

## MVP deliverable

A creator wizard over `issuer-first-mint-flow.md`:

1. Creator connects issuer wallet.
2. App explains issuer/account model and irreversible choices.
3. App builds one unsigned transaction at a time.
4. Creator signs externally.
5. App verifies the live ledger state before unlocking the next step.
6. Distributor trustline and first mint happen only after prerequisites are verified.

## State-machine rule

Do not trust local click state. Each wizard step unlocks only from live ledger state:

| Wizard stage | Live proof |
|---|---|
| issuer account ready | `account rISSUER` |
| domain/flags/tick/transfer config landed | `account rISSUER` |
| distributor trustline exists | `trustlines rDISTRIBUTOR CUR` |
| first mint landed | `tx-info HASH` + holder trustline balance |
| liquidity exists | `amm-info` or `book-offers` |

## Testnet demo checklist

- Full creator journey on testnet.
- UI enforces clawback/freeze/NoFreeze ordering by linking to operation flows.
- One failed/missing prerequisite blocks the next step.
- Post-launch token report uses `token-intel`, not fabricated metrics.

## Mainnet-safe checklist

- Irreversible issuer choices are shown before each relevant transaction.
- Platform never batches silent irreversible flags.
- Creator signs every step in their own wallet.
- No seed/private-key input exists anywhere.
- Legal/compliance caveats are shown for regulated/RWA/financial claims.
- Liquidity/holder metrics are live or explicitly unavailable.

## Common failure modes

- Custody drift: holding creators' issuer keys.
- Treating "launchpad" as a single AccountSet JSON.
- Letting creators choose clawback after trustlines exist.
- Claiming holder/liquidity numbers without `trustlines`, `amm-info`, or `book-offers`.
- Batching flags so creators cannot understand irreversible consequences.
