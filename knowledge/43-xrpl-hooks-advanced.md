# Advanced Xahau Hooks — Operations and Risk

## Scope

This guide covers architecture and operational controls, not deployment commands. XRPL-Hermes does not compile, serialize, sign, submit, or deploy Hooks.

## Security model

Hooks execute in ledger transaction processing and can reject transactions involving their account. A defective Hook can impair normal account operations. Review a Hook as both application logic and account-control infrastructure.

High-risk capabilities include:

- rejecting broad transaction classes;
- mutating persistent state;
- emitting transactions;
- authorizing other Hooks/accounts through grants;
- replacing code in an occupied chain slot;
- deleting shared namespaces;
- interacting with earlier/later Hooks in the chain.

## Chain design

An account's Hook chain has up to 10 ordered positions. Position is behavior, not presentation:

- `SetHook.Hooks[n]` maps to chain slot `n`;
- empty wrappers preserve positions and are no-ops;
- replace/update/delete must target the intended slot;
- behavior may differ when the same Hook moves earlier or later in the chain.

Document the complete chain before changing one slot. After every update, inspect validated state with `hooks-info` and compare all slots, not only the changed hash.

## State and namespaces

Treat namespace IDs and state keys as part of the public storage schema.

- Use deterministic namespacing and explicit key encoding.
- Version state layouts.
- Plan migrations before code replacement.
- Do not use namespace deletion as an ordinary rollback; it destroys state.
- Prove that one Hook cannot unintentionally collide with or erase another Hook's state.

Exact state-size and entry limits are protocol/version dependent. Read current source/definitions rather than copying unpinned numbers.

## Parameters and grants

Parameters affect behavior without changing code, so they require the same review discipline as source changes:

- decode every hex name/value for the signer;
- reject duplicates and unknown keys;
- enforce type, range, and endianness in the Hook;
- record the expected parameter set in release artifacts.

Grants expand who or what can exercise Hook capabilities. Keep them minimal, review account/hash pairs, and verify post-install state.

## Emission

Emitted transactions increase complexity and failure surface:

- confirm the target network enables required amendments;
- constrain transaction types and recipients;
- account for fee and reserve effects;
- test recursion/circularity protections and delayed execution behavior;
- retain transaction-level receipts for emitted results;
- define behavior when emission fails while originating execution continues or rejects.

`HookCanEmit` is enabled on reviewed Mainnet/Testnet definitions, but that does not certify any specific emitted transaction flow.

## Amendment divergence

At review time, Testnet enabled fields that Mainnet disabled/vetoed, including `HookOnV2` and NamedHooks. Therefore:

- a successful Testnet serialization may still be invalid for Mainnet;
- never copy Testnet feature state into Mainnet assumptions;
- refresh `server_definitions.json` and feature status at release time;
- generate Mainnet artifacts from Mainnet definitions.

## Upgrade and rollback

Every release needs:

1. current chain snapshot;
2. source and WASM hashes;
3. exact target slot and operation classification;
4. expected state migration;
5. unsigned transaction review;
6. simulation result;
7. validated installation proof;
8. rollback/delete transaction prepared and independently reviewed;
9. emergency signer access that does not depend on the affected application.

Rehearse rollback on Testnet. Verify ordinary payments/account maintenance after install and after rollback.

## Monitoring

Monitor validated state and behavior, not only transaction submission:

- installed Hook hashes and slots;
- amendment changes;
- Hook execution result codes/messages in metadata;
- rejected transaction rate;
- emitted transaction outcomes;
- reserve/fee changes;
- unexpected parameter, grant, or namespace changes.

Alert on drift between the reviewed release manifest and live account Hook state.

## Production acceptance

Do not approve Mainnet unless:

- behavior and non-behavior are precisely specified;
- current Mainnet amendments support every field;
- deterministic build and independent audit pass;
- Testnet positive/negative/boundary/rollback evidence is complete;
- wallet displays and human review expose the exact `SetHook` effects;
- rollout, monitoring, and emergency recovery have named owners;
- a human explicitly approves the Mainnet signature.

See `references/xahau-hooks.md` for pinned protocol facts and `knowledge/32-xrpl-hooks-dev.md` for the development gate.
