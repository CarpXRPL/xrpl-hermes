# Token Intelligence Reports — Live-Data Methodology

How to produce a serious intelligence report on an XRPL issued token using live ledger data. This file is the deep companion to the **Token Intelligence Rules** in `SKILL.md`: no buy/snipe/risk call is made on fewer than 5 verified live data points, and every report carries a confidence level and a missing-data list.

**Hard rule:** every number in a report comes from a tool run or a named API response. If a source fails, the report says *unavailable — <endpoint/command> failed*, never a plausible guess.

---

## Required inputs

| Input | Form | Notes |
|---|---|---|
| Issuer address | `r...` classic address | Validate first: `validate-address rISSUER` |
| Currency code | on-ledger form | 3-char ASCII, or 40-char hex for anything longer (e.g. SOLO = `534F4C4F00000000000000000000000000000000`). Convert before querying — display names never match ledger fields. |
| Network | mainnet / testnet | Default mainnet; say which one the report covers. |

---

## Data gathering checklist

Run these in order. Each row lists the command and what to extract.

### 1. Issuer account state
```bash
python3 -m scripts.xrpl_tools account rISSUER
```
Extract: `Domain`, `FlagDescriptions`, `OwnerCount`, balance, `Sequence` (account age proxy via first tx, see §7).

Interpret flags:
- `lsfDefaultRipple` — expected for a functioning issuer; its absence breaks third-party transfers of the token.
- `lsfDisableMasterKey` + regular key / signer list — issuer keys are managed; good operational hygiene.
- `lsfGlobalFreeze` — all trust lines frozen right now; trading is dead. Red flag unless explained.
- `lsfNoFreeze` — issuer permanently gave up freeze (and clawback is blocked by it).
- `lsfRequireAuth` — holders need issuer authorization (compliance token pattern).
- `lsfAllowTrustLineClawback` — issuer can claw back. Not inherently bad (RLUSD has it); it is a custody fact holders must know.

### 2. Domain verification
If `Domain` is set, decode it and fetch `https://<domain>/.well-known/xrp-ledger.toml`; confirm the issuer address appears in it. Domain set + TOML listing the account = strong identity signal. Domain unset, or TOML missing/mismatched = weaker identity; say so explicitly.

### 3. Trust lines / holder picture
```bash
python3 -m scripts.xrpl_tools trustlines rISSUER <HEX_OR_3CHAR>
```
Extract: number of returned lines (note pagination limits — public nodes cap responses; report "at least N" not "N"), balance distribution among returned lines, largest-holder share of what is visible. For full holder counts use an explorer API (XRPSCAN, xrpl.to, Bithomp) and **name the source and timestamp**; if no API is reachable, holder count is *unavailable*.

### 4. Issuer obligations (supply)
Explorer obligations endpoints (e.g. XRPSCAN `account/{issuer}/obligations`) give outstanding supply. Cross-check against the trust-line sample. Keyed by on-ledger currency code.

### 5. Liquidity — AMM and DEX
```bash
# AMM pool, live:
python3 -m scripts.xrpl_tools amm-info XRP <HEX_OR_SYMBOL>:rISSUER
# DEX order book, both sides:
python3 -m scripts.xrpl_tools book-offers <HEX>:rISSUER XRP
python3 -m scripts.xrpl_tools book-offers XRP <HEX>:rISSUER
```
Extract: pool exists or not, pool sizes both sides, trading fee, top-of-book depth, spread, and how much XRP it takes to move the price 5%. Thin or one-sided books are the single most common rug vector — quantify, don't adjective.

### 6. Transfer rate and tick size
From the issuer `account` output (`TransferRate`, `TickSize`). A transfer rate of e.g. `1020000000` = 2% fee on third-party transfers — material for any trading strategy.

### 7. Recent activity
```bash
python3 -m scripts.xrpl_tools account-tx rISSUER 50
```
Extract: first-seen age (older = more history to judge), recent issuance bursts, large outbound payments to exchanges, freeze transactions, clawbacks. Date-stamp the window covered.

### 8. Metadata sources
xrpl.to, XRPLMeta (`api.xrplmeta.org/token/{currency}+{issuer}` — on-ledger code form), XRPSCAN, Bithomp. Use them for names/logos/KYC labels and **say which one said what**. Metadata is claims, not ledger truth.

---

## Risk flags (each must cite its evidence)

- Issuer holds master key with no regular key/signer list (single-key risk)
- No domain, or domain TOML does not list the issuer
- `lsfGlobalFreeze` active; or freeze history in recent transactions
- Clawback enabled without a stated compliance purpose
- Transfer rate set without disclosure
- Top visible holder owns a dominant share
- One-sided or near-empty order book; no AMM pool
- Supply minted recently in bursts to few accounts
- Issuer account younger than the token's marketing claims

---

## Confidence scoring

| Level | Criteria |
|---|---|
| **High** | ≥8 checklist items from live data, holder + liquidity data from at least one named external source, no failed lookups on material items |
| **Medium** | 5–7 live items; holder distribution or obligations unavailable but ledger-side data complete |
| **Low** | <5 live items, or liquidity/issuer-flags unavailable — **no buy/snipe recommendation may be issued at Low** |

---

## Report template

```markdown
# Token Intelligence: <NAME> (<on-ledger code>) — <network>
Generated: <UTC timestamp> · Confidence: High/Medium/Low

## Identity
Issuer: r... · Domain: ... (TOML verified: yes/no) · Flags: ...

## Supply & Holders
Obligations: ... (source, time) · Visible trust lines: at least N · Largest visible holder: ...%

## Liquidity
AMM: pool sizes / fee, or "no pool" · DEX: top-of-book both sides, spread, depth-to-5%

## Issuer Controls
Freeze: ... · Clawback: ... · TransferRate: ... · RequireAuth: ...

## Recent Activity (window: last N tx / dates)
...

## Risk flags
- <flag> — evidence: <command/source>

## Missing data
- <item>: unavailable — <endpoint or command that failed>

## Assessment
<conclusion tied to the evidence above. If confidence is Low: state that no
trade recommendation can be made and what data would raise confidence.>
```

---

## Related files
`21-xrpl-token-model.md` (mechanics) · `25-xrpl-audit-security.md` (issuer security) · `07-xrpl-clawback.md` (freeze/clawback) · `05-xrpl-amm.md` (pool math) · `20-xrpl-data-api.md` (external APIs) · `65-agent-freshness-and-source-policy.md` (sourcing rules)
