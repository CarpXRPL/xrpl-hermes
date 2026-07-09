# Xahau Hook App Product Flow

Use this playbook when the user wants a Xahau Hook app, on-ledger automation product, account firewall, auto-forwarder, savings rule, or Xahau-specific product.

## Product promise

A realistic Xahau Hook product plan with a hard boundary:

XRPL-Hermes can plan, calculate HookOn, and verify installed hook state. It does not compile, audit, or deploy hook C/WASM code; those steps happen in the Xahau toolchain outside this skill.

## Triggers

- "build a Xahau Hook app"
- "on-ledger automation"
- "account firewall hook"
- "auto-forward hook"
- "Xahau product"

## Target user

Advanced builders using Xahau for on-ledger logic.

## XRPL/Xahau primitives

- SetHook transaction structure
- HookOn bitmask
- installed hook state
- Xahau reserves / account objects
- URITokens where relevant

## Read first

- `skills/build-xrpl-product-flow.md`
- `skills/xahau-hook-setup-flow.md`
- `knowledge/32-xrpl-hooks-dev.md`
- `knowledge/43-xrpl-hooks-advanced.md`
- `knowledge/51-xrpl-xahau-hooks.md`

## Commands/tools

- `hooks-bitmask TXTYPE ...`
- `hooks-info rADDR`

## MVP deliverable

1. Pick one narrow hook behavior.
2. State what happens on matching and non-matching transaction types.
3. Calculate HookOn with `hooks-bitmask`.
4. Hand hook code compile/deploy to Xahau tooling outside XRPL-Hermes.
5. Verify install with `hooks-info`.
6. Document rollback/delete plan.

## Testnet demo checklist

- Hook deployed through Xahau tooling on testnet.
- `hooks-info` proves it is installed.
- One triggering transaction behaves as expected.
- One non-triggering transaction is unaffected.
- HookOn bitmask is documented.

## Mainnet-safe checklist

- Code audited externally before real funds.
- Rollback/delete rehearsed on testnet.
- Product docs clearly say Xahau Hooks are not XRPL mainnet Hooks.
- The UI never claims Hermes compiled/deployed the hook.

## Common failure modes

- Assuming Hooks exist on XRPL mainnet.
- HookOn active-low inversion mistakes.
- Unaudited hook blocks or redirects funds unexpectedly.
- Promising behavior that cannot be verified with `hooks-info`.
