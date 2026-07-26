# Agentic Payment Flow

Build and settle an **agent-initiated** XRPL payment (XRP or RLUSD) the signer-separated way:
Hermes builds typed **unsigned** JSON; the user's wallet/signing layer signs. **Testnet-first; keys
stay with the user.** Read `references/agentic-payments.md` first; safety = the **Safety rules**
block in `SKILL.md`.

## Architecture

```
agent intent
  └── Hermes build-* ──► unsigned Payment JSON  (SourceTag + Memo; no keys, no signing)
        └── human preview + approval (asset/amount/destination/tags/memos/fee)
              └── compatible external authorization/broadcast layer
                    └── returned hash/result ──► tx-info <hash> (validated finality)
```

---

## Step 1 — Build the unsigned payment (XRP)

Always set `--source-tag` (marks the tx as agent-initiated) and `--memo` (audit trail / order id).

```bash
python3 scripts/xrpl_tools.py build-payment \
  --from rSENDER --to rDEST --amount 1000000 \
  --source-tag 20260615 --memo "agent:order-4417"
```

Output is signer-ready JSON (`SigningPubKey:""`), with `SourceTag` (int) and hex-encoded `Memos`.
No `Fee`/`Sequence`/`LastLedgerSequence` — the signing layer autofills those.

---

## Step 2 — RLUSD (or any issued currency): trust line first, then pay

RLUSD currency code is the 160-bit hex `524C555344000000000000000000000000000000` (the literal
`"RLUSD"` is invalid on-ledger). Issuers — re-verify on-ledger (`references/rlusd.md`): mainnet
`rMxCKbEDwqr76QuheSUMdEGf4B9xJ8m5De`, testnet `rQhWct2fv4Vc4KRjRgMrxa8xPN9Zx9iLKV`.

```bash
# 1. Recipient (or agent) must hold a trust line to the issuer before receiving RLUSD
python3 scripts/xrpl_tools.py build-trustset \
  --from rHOLDER --currency 524C555344000000000000000000000000000000 \
  --issuer rMxCKbEDwqr76QuheSUMdEGf4B9xJ8m5De --value 1000000

# 2. Pay 5 RLUSD, tagged for the agent
python3 scripts/xrpl_tools.py build-payment \
  --from rSENDER --to rDEST --amount 5 \
  --cur 524C555344000000000000000000000000000000 \
  --iss rMxCKbEDwqr76QuheSUMdEGf4B9xJ8m5De \
  --source-tag 20260615 --memo "agent:invoice-88"
```

---

## Step 3 — Preview and confirm (before any signing)

Show the human the exact transfer and get approval (Safety rule 4):

```
Network:     testnet
Asset:       5 RLUSD (524C5553...0000 @ rMxCKb...)
From → To:   rSENDER → rDEST
SourceTag:   20260615   DestinationTag: (none)
Memos:       "agent:invoice-88"
```

Mainnet spend requires **explicit human approval** (Safety rule 5).

---

## Step 4 — Hand off to the wallet/signing layer (testnet)

Signing stays with the user—**never put a seed in chat/logs.** Hand reviewed JSON to a compatible
user-owned external wallet/HSM/KMS whose exact network and transaction support has been independently
verified. Joey and Privy are not certified handoffs. `xaman-payload` supports reviewed XRPL L1
Payments only and creates a guarded external side effect.

**Legacy in-process signing:**

**JavaScript/TypeScript projects:** use a separately audited user-owned external wallet/signing layer;
do not place wallet keys or signing code inside the Hermes workflow.

---

## Step 5 — Read the result code, confirm finality

| Prefix | Meaning |
|---|---|
| `tesSUCCESS` | applied — done |
| `tec*` | failed but **fee charged / ledger touched** (e.g. `tecUNFUNDED_PAYMENT`, `tecNO_LINE`) |
| `tef*` / `tem*` / `tel*` | rejected pre-flight, **no fee**, never in a ledger |
| `ter*` | retry possible (transient) |

```bash
python3 scripts/xrpl_tools.py tx-info <HASH>   # confirm validated; deterministic finality ~3-5s
```

---

## Step 6 — x402 / pay-per-request (optional)

For HTTP-402 machine-to-machine billing, the Payment from Steps 1–2 settles the 402 charge; the
facilitator issues a receipt. Full flow, package names, and network ids: `references/x402-payments.md`.

---

## Common mistakes

| Mistake | Fix |
|---|---|
| No `SourceTag` on agent payments | Always `--source-tag N` — agent attribution/accounting |
| Passing `"RLUSD"` as the currency | Use the 160-bit hex `524C5553...0000`; the 5-letter literal is invalid on-ledger |
| Paying RLUSD before a trust line exists | `build-trustset` first → `tecNO_LINE` otherwise |
| Setting `Fee`/`Sequence` by hand on a connected flow | Let `autofill` populate them (Safety rule 7) |
| Seed/key requested by agent code | Stop; use a user-owned external wallet/HSM/KMS that never exposes the key to Hermes |
| Raw XRP floats | `xrp_to_drops()` / drops only |
| Going to mainnet without approval | Explicit human sign-off; change endpoint deliberately |

See also: `references/agentic-payments.md`, `references/x402-payments.md`,
`references/track-agent-behavior.md` (attribute & monitor the tx you just built), `references/rlusd.md`,
`knowledge/02-xrpl-payments.md`, `knowledge/53-xrpl-wallets-auth.md`.
