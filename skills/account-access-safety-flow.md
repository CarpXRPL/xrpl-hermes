# Account Access Safety Flow

For: "rotate my key", "disable the master key", "lock down who can pay me",
"delete this account". These builders change *who can control an account* — the
failure mode is permanent lockout, so the invariant throughout is: **never remove an
authority until the replacement authority is proven to work on-ledger.**

Read first: `knowledge/01-xrpl-accounts.md`, `knowledge/60-xrpl-account-set.md`,
`knowledge/15-xrpl-transaction-format.md`. All builds below are high-risk —
confirm-before-build (`SKILL.md`) applies to every one.

## Step 0 — Decode current access state (live)

```bash
python3 scripts/xrpl_tools.py account rADDR                    # FlagDescriptions: lsfDisableMaster? lsfDepositAuth?
python3 scripts/xrpl_tools.py account_objects rADDR signer_list
python3 scripts/xrpl_tools.py account_objects rADDR deposit_preauth
```

Establish which authorities exist **now**: master key usable? regular key set? signer
list present? Never propose removing one without naming the survivor.

---

## Branch A — Key rotation (SetRegularKey → verify → optionally disable master)

The safe order is strict:

**A1. Assign the regular key (unsigned):**

```bash
python3 scripts/xrpl_tools.py build-set-regular-key --from rADDR --regular-key rNEWKEY
```

Signed by the current authority. `rNEWKEY` is the *address form* of the new key pair —
the user generates that pair in their own wallet; this toolkit never sees key material.

**A2. Prove the new key works BEFORE removing anything.** Have the user sign a harmless
transaction (e.g. a no-op `build-account-set --from rADDR` with no flags) **with the
regular key** and confirm it validates (`tx-info HASH`). An untested "backup key" is
not a backup.

**A3. Only then, if the user wants it, disable the master key (unsigned):**

```bash
python3 scripts/xrpl_tools.py build-account-set --from rADDR --set-flag 4   # asfDisableMaster
```

- This specific transaction must be signed by the **master key** itself.
- The ledger refuses it unless a regular key or signer list exists — but it cannot
  check whether the user actually *holds* that key. A2 is the only real protection.
- Re-enabling later (`--clear-flag 4`) requires the surviving authority to sign.
- Removing a regular key = `build-set-regular-key --from rADDR` with no `--regular-key`
  — refuse to build it if Step 0 showed the master disabled and no signer list.

**Deliberate blackhole warning:** setting the regular key to a well-known dead address
and then disabling master permanently removes all control — issuers do this on purpose
to renounce a token. If the user's request would produce this *accidentally*, stop and
say so before building.

## Branch B — Incoming-payment control (DepositAuth + preauthorization)

```bash
python3 scripts/xrpl_tools.py build-account-set --from rADDR --set-flag 9        # asfDepositAuth
python3 scripts/xrpl_tools.py build-deposit-preauth --from rADDR --authorize rSENDER
python3 scripts/xrpl_tools.py build-deposit-preauth --from rADDR --unauthorize rSENDER
```

- With `lsfDepositAuth` set, incoming payments fail (`tecNO_PERMISSION`) unless the
  sender is preauthorized. Exception: small XRP top-ups are allowed while the account's
  balance is at or below the base reserve, so it can't be starved of fee money.
- Each preauthorization is one owner-reserve object; `--unauthorize` releases it.
- Warn before building the flag: exchanges/contracts that pay this account will start
  failing until preauthorized — enumerate expected senders first
  (`account-tx rADDR 20` shows who actually pays them).
- Reversible: `--clear-flag 9`.

## Branch C — AccountDelete (checklist, then build)

AccountDelete sends the remaining XRP to a destination and removes the account. Work
the checklist top to bottom — each line is a live check:

| # | Check | Command |
|---|---|---|
| 1 | No blocking objects: trust lines, escrows, payment channels, checks, owned NFTs (NFT pages) all block deletion | `account_objects rOLD` — offers, tickets, signer lists, preauths do NOT block (auto-removed) |
| 2 | Account age: current validated ledger index must be ≥ account `Sequence` + 256 | `account rOLD` (Sequence) vs `ledger` |
| 3 | Special cost: the fee is the **owner reserve increment** (burned), far above a normal fee | `server-info` for the current increment |
| 4 | Destination exists and can receive | `account rDEST`; if it requires a destination tag, hand-add `"DestinationTag": N` to the JSON (the builder takes no tag argument); if it has DepositAuth, rOLD must be preauthorized |
| 5 | Nothing wanted is left behind | Issued-currency balances can't travel — trust lines had to be zeroed/closed in check 1 anyway |

Then build (unsigned), confirming network, both addresses, the burned cost, and the
consequence — the account, its history anchor, flags, and settings are gone; recreating
the address later starts a blank account:

```bash
python3 scripts/xrpl_tools.py build-account-delete --from rOLD --to rDEST
```

If it still fails, diagnose by code (`tecTOO_SOON` = check 2, `tecHAS_OBLIGATIONS` =
check 1) via `skills/failed-transaction-diagnosis-flow.md`.

## Common mistakes

| Mistake | Fix |
|---|---|
| Disabling master before test-signing with the regular key | A2 first — prove the survivor authority on-ledger |
| Removing a regular key while master is disabled and no signer list exists | Permanent lockout — Step 0 facts gate this build |
| Enabling DepositAuth on an account that receives third-party payments | Preauthorize expected senders first, or expect `tecNO_PERMISSION` everywhere |
| "Delete the account" with trust lines still open | `tecHAS_OBLIGATIONS` — close lines/escrows/channels/checks first (check 1) |
| Treating the AccountDelete fee as a normal fee | It burns the owner-reserve increment — state the number from `server-info` in the confirm |
| Forgetting the destination tag on delete-to-exchange | Builder has no tag flag — hand-add `DestinationTag` before signing |

See also: `skills/multisig-safety-flow.md` (signer lists as the surviving authority),
`skills/issuer-first-mint-flow.md` (issuer flag choices), `knowledge/60-xrpl-account-set.md`
(full asf/lsf flag catalog).
