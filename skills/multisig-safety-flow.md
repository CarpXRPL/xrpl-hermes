# Multisig Safety Flow

For: "set up multisig on our treasury", "change/remove the signer list", "we lost a
signer key", "submit this multisigned transaction". Multisig mistakes are the ones that
permanently lock accounts, so this flow is checkpoint-heavy: verify live state, do the
quorum math, build unsigned, and treat list deletion as the most dangerous operation in
the toolkit.

Read first: `knowledge/12-xrpl-multisig.md`, `knowledge/13-xrpl-tickets.md`,
`knowledge/15-xrpl-transaction-format.md`.

Boundary reminder: `build-signer-list-set` emits unsigned JSON; the signing ceremony
happens in the signers' own wallets or their own xrpl-py stack. `submit-multisigned`
accepts **already-signed** transaction JSON only — it never signs anything.

---

## Step 0 — Verify current access state (live)

```bash
python3 scripts/xrpl_tools.py account rTREASURY                     # flags: is lsfDisableMaster set? RegularKey?
python3 scripts/xrpl_tools.py account_objects rTREASURY signer_list # existing SignerList, if any
```

Record three facts before touching anything: (1) is the master key disabled,
(2) is a regular key set, (3) what signer list (quorum + entries) exists now.
Every safety judgment below depends on these.

## Step 1 — Design checkpoints (quorum math)

| Check | Rule | Failure mode |
|---|---|---|
| Quorum reachable | `SignerQuorum` ≤ Σ(signer weights) | Unsatisfiable list = the list can never sign anything |
| Quorum meaningful | Quorum high enough that no single compromised key clears it (unless 1-of-N is the explicit design) | Multisig that isn't actually multi |
| Signer count | 1–32 entries, each weight ≥ 1 | Out-of-range = malformed |
| No self-entry | The account must **not** appear in its own signer list | Rejected as malformed |
| Key independence | Signers should be separate people/devices, not one person's three wallets | Correlated loss/compromise defeats the design |
| Loss tolerance | Ask: "if K keys are lost, can the remaining weights still reach quorum?" | See Step 5 recovery — sometimes the answer is "never again" |
| Reserve | A signer list costs one owner-reserve increment | `server-info` for the current increment; `account rTREASURY` SpendableXRP |

Confirm-before-build applies (`SKILL.md` high-risk table): echo network, account,
quorum, every signer:weight pair, and the loss-tolerance consequence back to the user
before emitting JSON.

## Step 2 — Build the SignerListSet (unsigned)

```bash
python3 scripts/xrpl_tools.py build-signer-list-set \
  --from rTREASURY --quorum 3 --signers "rALICE:2,rBOB:1,rCAROL:1"
```

- `--signers` is comma-separated `address:weight`. This example: any two of the three
  can sign only if Alice is one of them (2+1 ≥ 3); Bob+Carol alone (1+1) cannot.
- A new SignerListSet **replaces the entire existing list** — there is no incremental
  add/remove. To change one signer, re-emit the full intended list.
- This transaction is signed by the account's *current* authority (master, regular key,
  or the *existing* signer list) — the new list takes effect only after validation.

## Step 3 — The signing ceremony (outside this toolkit)

Each signer signs the **identical** transaction JSON (same `Sequence`, `Fee`, every
field) in their own wallet or stack. Rules the ceremony must respect:

- **Fee scales with signatures:** a multisigned transaction pays at least
  `(1 + N) × base fee` where N = number of signatures attached. Autofill from a single
  signer's wallet will underpay — set the fee for the final N before anyone signs.
- The outer `SigningPubKey` must be the empty string; each signature lives in the
  `Signers` array (sorted by account — xrpl-py's multisign helpers handle ordering).
- Attached weights must sum to ≥ quorum, or submission fails.
- **Parallel signing without sequence races:** if the treasury also sends normal
  transactions, reserve tickets first (`build-ticket-create --from rTREASURY --count 5`)
  and multisign against a `TicketSequence` instead of the live `Sequence`
  (`knowledge/13`). Otherwise any interleaved transaction invalidates the half-signed
  JSON (`tefPAST_SEQ`).

If signers use xrpl-py, keys come from their own environment (`os.environ["XRPL_SEED"]`
pattern) — never paste seeds into this toolkit; it has no command that accepts one.

## Step 4 — Submit and verify

```bash
python3 scripts/xrpl_tools.py submit-multisigned '{"TransactionType":"...","Signers":[...]}'
python3 scripts/xrpl_tools.py tx-info HASH                          # wait for validated
python3 scripts/xrpl_tools.py account_objects rTREASURY signer_list # list matches design?
```

The submit result is provisional — apply the finality rules from
`skills/failed-transaction-diagnosis-flow.md` (only a validated ledger is final).

## Step 5 — Changing, removing, recovering

**Change:** re-run Step 1 math for the new list, then Steps 2–4. The old list authorizes
the change; the new list replaces it atomically.

**Remove** (quorum 0, no signers):

```bash
python3 scripts/xrpl_tools.py build-signer-list-set --from rTREASURY --quorum 0
```

⚠ Before building this, re-check Step 0: if `lsfDisableMaster` is set and no regular
key exists, the signer list is the **only** authority — deleting it locks the account
and its funds **forever**. Refuse to hand this JSON over until the user confirms an
alternative authority exists.

**Recover from lost signer keys** — reason from Step 0 facts, in order:

1. Remaining signers still reach quorum → they multisign a replacement SignerListSet.
2. Master key enabled → master signs a replacement list directly.
3. Regular key set and held → regular key signs the replacement.
4. None of the above → the account is permanently inaccessible. Say so honestly; nothing
   on-ledger can fix it. (Funds can still *arrive*; they can never leave.)

## Common mistakes

| Mistake | Fix |
|---|---|
| Quorum > Σ weights | Unsatisfiable — redo Step 1 math before building |
| Account listed as its own signer | Malformed — remove the self-entry |
| Base fee on a multisigned tx | Fee ≥ (1+N) × base; set it before the ceremony starts |
| Signers signed slightly different JSON | Every signer must sign byte-identical fields; restart the ceremony |
| Deleting the list with master disabled and no regular key | Permanent lockout — check Step 0 facts first, always |
| "Add one signer" as an incremental edit | SignerListSet replaces the whole list — emit the complete new list |
| Half-signed tx dies with `tefPAST_SEQ` | The account transacted mid-ceremony — use tickets (`knowledge/13`) |

See also: `skills/account-access-safety-flow.md` (regular keys, master-key disable),
`skills/treasury-monitor-flow.md` (watching the treasury after setup),
`skills/failed-transaction-diagnosis-flow.md` (if the submission fails).
