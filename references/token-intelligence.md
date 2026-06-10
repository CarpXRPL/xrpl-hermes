# Token Intelligence — Quick Reference

Condensed from `knowledge/64-token-intelligence-reports.md` — read that file before producing a report.

## Non-negotiables
- ≥5 verified live data points before any buy/snipe/risk call; at Low confidence, no trade recommendation at all.
- Every number cites a tool run or named API + timestamp. Failed lookup → "unavailable — <endpoint>", never a guess.
- Currency codes >3 chars are queried in 160-bit hex form.

## Gathering order
1. `validate-address` → `account rISSUER` (flags, domain, transfer rate)
2. Domain TOML check (`/.well-known/xrp-ledger.toml` lists issuer?)
3. `trustlines rISSUER <code>` (visible holders — report "at least N")
4. Explorer obligations (supply, named source)
5. `book-offers` both sides + AMM pool (depth, spread, fee)
6. `account-tx rISSUER 50` (age, bursts, freezes, clawbacks)

## Output
Use the report template in `knowledge/64`: Identity / Supply & Holders / Liquidity / Issuer Controls / Recent Activity / Risk flags (with evidence) / **Missing data** / Assessment + confidence (High ≥8 items · Medium 5–7 · Low <5).
