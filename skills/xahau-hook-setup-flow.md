# Xahau Hook Setup Flow

For: "install a hook on my Xahau account", "what should HookOn be?", "is there a hook
on rADDR?", "write me a hook". Hooks are small WASM programs that run on-ledger on
**Xahau** — a separate network from XRPL (own ledger, own native asset **XAH**, own
amendment set). Nothing here touches XRPL mainnet.

Read first: `knowledge/51-xrpl-xahau-hooks.md` (concepts + SetHook anatomy),
`knowledge/32-xrpl-hooks-dev.md` (development), `knowledge/43-xrpl-hooks-advanced.md`
(state, emitted transactions).

## What this toolkit can and cannot do — say this up front

| Can (this toolkit) | Cannot (external tooling required) |
|---|---|
| `hooks-bitmask TXTYPE …` — compute the `HookOn` value for the triggers you want | Write or compile hook C/WASM code — use the Hooks Builder (hooks-builder.xrpl.org) or the hooks toolchain |
| `hooks-info rADDR` — live list of hooks installed on a Xahau **mainnet** account | Build a SetHook transaction — there is no `build-set-hook` command |
| Explain hook concepts, SetHook fields, and lifecycle from the knowledge files | Sign or submit anything to Xahau — signing stays in a Xahau-capable wallet (e.g. Xaman) or the user's own stack |

Never present a hand-assembled SetHook JSON as toolkit output — label it clearly as a
manual template the user completes and signs externally.

---

## Step 1 — Check what's already installed (live, Xahau mainnet)

```bash
python3 scripts/xrpl_tools.py hooks-info rXAHAU_ACCOUNT
```

Returns the account's Hook objects (`HookCount`, hook hashes, namespaces). Note the
limit: this queries **xahau.network mainnet only** — Xahau-testnet hooks won't show
here; verify testnet installs in a Xahau testnet explorer instead.

## Step 2 — Decide the triggers and compute HookOn

A hook fires only for transaction types its `HookOn` bitmask enables. Compute it —
never hand-derive it, the semantics invert per bit:

```bash
python3 scripts/xrpl_tools.py hooks-bitmask Payment URITokenMint
```

Output gives the exact 64-hex `HookOn` value plus the semantics: bits are
**active-low** (0 = hook fires for that type) **except bit 22 (ttHOOK_SET), which is
active-high** — so "fire on everything" is not all-zeros, and a wrong hand-rolled mask
either silently never fires or fires on SetHook and can block hook updates. Accepts
names (`Payment`, `ttPAYMENT`, `Invoke`) or numeric tt IDs.

## Step 3 — Develop and compile the hook (external)

Hook code is C compiled to WASM with the Xahau hooks toolchain, or built/tested in the
browser Hooks Builder. Guardrails: hooks must be deterministic, are strictly
resource-bounded, and every install should be tested on **Xahau testnet first** —
a buggy hook can reject every payment to the account. This step happens entirely
outside this toolkit; `knowledge/32` and `knowledge/43` cover the development model.

## Step 4 — Assemble the SetHook transaction (manual template)

There is no builder for this — the user fills this template themselves with values
from Steps 2–3 and signs it in their Xahau wallet:

```json
{
  "TransactionType": "SetHook",
  "Account": "rXAHAU_ACCOUNT",
  "Hooks": [{
    "Hook": {
      "CreateCode": "<compiled WASM as hex, from Step 3>",
      "HookOn": "<64-hex value from hooks-bitmask>",
      "HookNamespace": "<64-hex namespace, e.g. SHA-256 of a label>",
      "HookApiVersion": 0,
      "Flags": 1
    }
  }]
}
```

- `Flags: 1` (`hsfOverride`) replaces/installs in that hook position; omitting it on an
  occupied position fails. Deleting a hook = `CreateCode: ""` with `hsfOverride` (and
  `hsfNSDELETE` to clear its namespace state).
- Up to 10 hook positions per account; order matters (they execute in sequence).
- `HookNamespace` scopes the hook's on-ledger state; two hooks sharing a namespace
  share state (`knowledge/43`).
- Fee: SetHook is expensive relative to base transactions — let the wallet autofill on
  Xahau and sanity-check before signing.

Confirm-before-build applies in spirit even though the toolkit isn't building: restate
network (Xahau mainnet vs testnet), account, triggers, and the consequence (this code
runs on every matching transaction) before handing over the template.

## Step 5 — Verify after install

```bash
python3 scripts/xrpl_tools.py hooks-info rXAHAU_ACCOUNT   # mainnet installs only
```

Then send a small test transaction of a triggering type and confirm the hook's effect
(accept/reject/emit) matches intent before relying on it.

## Common mistakes

| Mistake | Fix |
|---|---|
| Treating Xahau as XRPL mainnet | Separate network, XAH not XRP — XRPL commands query the wrong chain |
| Hand-computing HookOn | Bits are active-low except bit 22 — always use `hooks-bitmask` |
| Expecting a `build-set-hook` command | Doesn't exist — manual template + external signing (say so explicitly) |
| Checking testnet installs with `hooks-info` | It queries xahau.network mainnet only — use a testnet explorer |
| Installing straight to mainnet | A rejecting hook can freeze all incoming payments — testnet first, always |
| Forgetting `hsfOverride` when replacing | Install into an occupied position fails without Flags 1 |

See also: `knowledge/51-xrpl-xahau-hooks.md`, `knowledge/32-xrpl-hooks-dev.md`,
`knowledge/43-xrpl-hooks-advanced.md`, `skills/failed-transaction-diagnosis-flow.md`
(result-code classes apply on Xahau too).
