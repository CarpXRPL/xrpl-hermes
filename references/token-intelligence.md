# Token Intelligence — Quick Reference

Condensed from `knowledge/64-token-intelligence-reports.md` — read that file before producing a report.

## Non-negotiables
- `token-intel` is a five-query XRPL ledger snapshot, caps confidence at Medium, and provides no buy/snipe/sell recommendation.
- Every number cites a tool run or named API + timestamp. Failed lookup → "unavailable — <endpoint>", never a guess.
- Currency codes >3 chars are queried in 160-bit hex form.

## Gathering order
0. `token-intel <code> rISSUER` — five-query ledger snapshot (issuer flags/domain, limited trustline window, DEX book vs XRP, AMM, recent issuer activity, risk flags, confidence scope, missing-data list). Then deepen with:
1. `validate-address` → `account rISSUER` (flags, domain, transfer rate)
2. Domain TOML check (`/.well-known/xrp-ledger.toml` lists issuer?)
3. `trustlines rISSUER <code>` (visible holders — report "at least N")
4. Explorer obligations (supply, named source)
5. `book-offers` both sides + `amm-info XRP <code>:rISSUER` (depth, spread, fee)
6. `account-tx rISSUER 50` (age, bursts, freezes, clawbacks)

## Output
Use the report template in `knowledge/64`: Identity / Supply & Holders / Liquidity / Issuer Controls / Recent Activity / Risk flags (with evidence) / **Missing data** / Assessment + evidence-coverage confidence. Confidence is not a trade recommendation.
