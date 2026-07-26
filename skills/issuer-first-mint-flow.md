# Issuer Setup + First Mint Flow

The minimal, checkpointed path from "I want to issue a token" to the first issued-currency
payment: issuer flags → domain → distributor trust line → first mint. Everything here is
**build-only unsigned JSON** (AccountSet, TrustSet, Payment) — the user's wallet signs each
step. Testnet first. For the full launch (DEX listing, AMM pool), continue with
`skills/token-launch-flow.md`.

Read first: `knowledge/21-xrpl-token-model.md`, `knowledge/22-xrpl-token-issuance.md`,
`knowledge/03-xrpl-trustlines.md`, `knowledge/60-xrpl-account-set.md`.

## Architecture

```
issuer account (cold)                       distributor / hot wallet
  1. AccountSet: policy flags + domain        3. TrustSet: trust the issuer
  2. (checkpoint) freeze / clawback choice    4. receive first mint (Payment)
                                              5. distribute onward
```

XRPL has no separate "mint" transaction: the issuer paying an issued currency to a
trust-line holder **is** the mint. The issuer's own balance of its token is always 0;
supply lives on trust lines.

---

## Step 0 — Verify current issuer state (live)

```bash
python3 scripts/xrpl_tools.py account rISSUER
```

Check: enough XRP for reserves + fees, `Sequence`, existing `FlagDescriptions`, and —
critical for the clawback checkpoint — whether **any trust lines already exist**
(`trustlines rISSUER`).

## Step 1 — Decision checkpoints (settle these BEFORE minting)

Confirm each choice with the user explicitly — they are hard or impossible to change
after supply circulates (confirm-before-build applies: state network, account, flag,
consequence).

| Checkpoint | Options | Irreversibility |
|---|---|---|
| **DefaultRipple** (`asfDefaultRipple`, flag 8) | ON for any token that should trade holder↔holder / on DEX/AMM | Reversible, but flipping it later breaks assumptions on existing lines |
| **Clawback** (`asfAllowTrustLineClawback`, flag 16) | Regulated/RWA assets usually ON; community tokens usually OFF | Can only be enabled while the issuer has **zero trust lines**; once set it **cannot be unset** |
| **Freeze policy** | Keep freeze ability (default) or renounce with `asfNoFreeze` (flag 6) | `asfNoFreeze` is **permanent** — you can never freeze again (and cannot un-set GlobalFreeze) |
| **RequireAuth** (`asfRequireAuth`, flag 2) | **Not shipped as a complete XRPL-Hermes workflow** | The current trust-line builder cannot authorize holder lines; do not enable it through this flow |
| **TransferRate / TickSize / Domain** | fee 0–100%, DEX precision 3–15, identity domain | Changeable, but set them before liquidity exists |

## Step 2 — Build the issuer AccountSet(s) (unsigned)

One flag per AccountSet transaction. Typical sequence:

```bash
# DefaultRipple (almost always wanted for tradeable tokens)
python3 scripts/xrpl_tools.py build-account-set --from rISSUER --set-flag 8

# Optional, per Step 1 — clawback must precede ANY trust line, and is permanent:
python3 scripts/xrpl_tools.py build-account-set --from rISSUER --set-flag 16

# Identity + market parameters (combinable in one AccountSet)
python3 scripts/xrpl_tools.py build-account-set --from rISSUER \
  --domain example.com --tick-size 5 --transfer-rate 1005000000
```

- `--domain` is auto-hex-encoded; `--transfer-rate 1005000000` = 0.5% transfer fee
  (1000000000 = 0%, bounds enforced by the builder); `--tick-size` 3–15.
- Each payload is signer-ready JSON → wallet handoff → sign → submit.
- Verify after signing: `account rISSUER` shows the new `FlagDescriptions`/`Domain`.
- Publish `https://<domain>/.well-known/xrp-ledger.toml` listing the issuer address and
  currency so wallets don't show "unknown issuer" (`skills/token-launch-flow.md` Step 2
  has the TOML template).

## Step 3 — Distributor sets the trust line (unsigned)

The distributor (hot wallet) must trust the issuer before it can receive the mint:

```bash
python3 scripts/xrpl_tools.py build-trustset \
  --from rDISTRIBUTOR --currency USD --issuer rISSUER --value 1000000
```

- `--value` is the trust limit = the maximum the distributor can hold. Size it to the
  planned supply, not "unlimited by reflex".
- 4–20 char symbols must be the 160-bit hex form on-ledger; 3-char codes pass as-is
  (`knowledge/21` explains the encoding).
- If the issuance requires `RequireAuth`, stop here. XRPL-Hermes does not ship the
  issuer-side trust-line authorization builder needed to complete this workflow. Do not
  hand-edit `Flags` into generated JSON and present that as a supported path.

## Step 4 — First mint: issuer pays the distributor (unsigned)

```bash
python3 scripts/xrpl_tools.py build-cross-currency-payment \
  --from rISSUER --to rDISTRIBUTOR \
  --deliver USD:rISSUER:500000 \
  --send-max USD:rISSUER:500000
```

For an issuer's **first mint**, prefer the cross-currency builder with matching
`--deliver` and `--send-max` issued-currency amounts. This keeps the payload explicit
and avoids xrpl-py's direct-Payment validation edge case where the source account is
also the issued currency's issuer. For ordinary holder-to-holder IOU payments, use
`build-payment --amount VALUE --cur CUR --iss rISSUER`.

Confirm before build (value transfer): network, issuer → distributor, `500000 USD.rISSUER`,
and that this creates supply. Then wallet handoff.

## Step 5 — Verify the mint (live)

```bash
python3 scripts/xrpl_tools.py trustlines rDISTRIBUTOR USD   # balance = 500000
python3 scripts/xrpl_tools.py trustlines rISSUER USD        # issuer view: negative balance = supply issued
python3 scripts/xrpl_tools.py account rISSUER               # flags still as designed
```

From here: end-user distribution, DEX listing, AMM pool → `skills/token-launch-flow.md`
Steps 5–6.

## Common mistakes

| Mistake | Fix |
|---|---|
| Minting before flags are final | Set DefaultRipple / clawback / RequireAuth **first** — some cannot be added later |
| Enabling clawback after trust lines exist | Impossible — flag 16 requires zero trust lines on the issuer |
| Setting `asfNoFreeze` casually | Permanent renunciation — confirm the user understands before building it |
| `build-payment --amount USD:rISSUER:500000` | Wrong arg shape — holder-to-holder IOU payments use `--amount 500000 --cur USD --iss rISSUER`; issuer first-mint uses `build-cross-currency-payment --deliver USD:rISSUER:500000 --send-max USD:rISSUER:500000` |
| Issuing from the same key that holds reserves long-term | Cold issuer / hot distributor separation (`knowledge/22`) |
| Skipping the domain/TOML | Wallets flag the token as unknown issuer — costs trust |

See also: `skills/token-launch-flow.md` (full launch), `skills/clawback-flow.md`
(exercising clawback later), `knowledge/59-rwa-tokenization.md` (regulated assets),
`knowledge/58-rlusd-operations.md` (RLUSD specifics).
