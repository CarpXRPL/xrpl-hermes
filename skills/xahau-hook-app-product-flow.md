# Xahau Hook App Product Flow

Use for planning a Xahau on-ledger automation product. HookOn calculation and installed-Hook inspection are **available**; compilation and deployment require **external setup**; an end-to-end deployable product is **not shipped**.

## Product boundary

XRPL-Hermes can produce a grounded product specification, calculate legacy `HookOn`, and inspect validated installed Hook state on Mainnet/Testnet. It does not compile, audit, serialize, sign, submit, or deploy Hooks.

## Intake

Capture:

- user and painful workflow;
- one narrow Hook behavior;
- Xahau Testnet account and chain slot;
- intended and explicitly excluded transaction types;
- accept/reject/state/emission behavior;
- off-ledger UI/indexing/monitoring needs;
- rollback and business model.

## Read first

- `skills/build-xrpl-product-flow.md`
- `skills/xahau-hook-setup-flow.md`
- `references/xahau-hooks.md`

## Grounding commands

```bash
python3 scripts/xrpl_tools.py hooks-bitmask Payment Invoke
python3 scripts/xrpl_tools.py hooks-info rACCOUNT testnet
```

Use `mainnet` only for read-only inspection until Testnet acceptance and independent audit are complete.

## MVP deliverable

1. Product one-pager and user flow.
2. Precise Hook behavior/non-behavior contract.
3. Target network ID, account, chain slot, and current validated chain snapshot.
4. Calculated legacy `HookOn` with resolved transaction IDs.
5. Off-ledger architecture for UI, indexing, receipts, and monitoring.
6. External-toolchain handoff: source, build, Xahau-aware serialization, simulation, wallet signing.
7. Testnet acceptance plan: positive, negative, boundary, malformed-input, and rollback tests.
8. Honest monetization/cost assumptions without inventing XAH fees or limits.

## Testnet acceptance

- endpoint proves `NetworkID=21338`;
- source and resulting WASM are independently reviewable;
- exact unsigned `SetHook` passes current Xahau serialization and simulation;
- user signs outside Hermes;
- validated transaction and installed hash/slot match reviewed artifacts;
- trigger and non-trigger behavior match the specification;
- rollback succeeds and validated post-state is recorded.

## Mainnet gate

Do not call the product Mainnet-ready until:

- current Mainnet amendments support every used field;
- independent security audit passes;
- fees/reserves and operational risks are measured live;
- monitoring and emergency recovery are implemented;
- a human explicitly approves signing.

## Failure modes

- confusing Xahau with XRPL Mainnet;
- hand-editing active-low masks;
- using Testnet-only fields such as currently enabled HookOnV2/NamedHooks on Mainnet;
- presenting a malformed `SetHook` template as signer-ready;
- using opaque WASM or unpinned tooling;
- counting an RPC error as an empty chain;
- claiming Hermes compiled or deployed the Hook.
