# Token Intelligence Product Flow

Use this product playbook when the user wants to build a token safety dashboard, holder dashboard, risk API, Telegram/Discord bot, alerting tool, or research product.

## Product promise

A read-only XRPL intelligence product that reports what it can verify live and labels everything else as missing/unavailable.

## Triggers

- "build a token safety dashboard"
- "holder dashboard"
- "rug checker"
- "token analytics API"
- "Telegram bot for token alerts"
- "monitor issuer flags/liquidity/holders"

## Target user

Community safety teams, token communities, dashboards, trading-research tools, bots, and open-source analysts.

## XRPL primitives

Read-only only:

- issuer account flags/domain
- trust lines and balances
- DEX order books
- AMM pools
- recent issuer/account transactions
- amendment/state context where relevant

## Read first

- `skills/build-xrpl-product-flow.md`
- `knowledge/64-token-intelligence-reports.md`
- `references/token-intelligence.md`
- `knowledge/25-xrpl-security-audit.md`
- `knowledge/40-xrpl-monitoring.md`
- `knowledge/56-telegram-xrpl-bots.md` / `knowledge/57-discord-xrpl-bots.md` when building bots
- `knowledge/61-xrpl-websocket-streams.md`

## Commands/tools

- `token-intel CURRENCY rISSUER [TX_LIMIT] [TRUSTLINE_LIMIT]`
- `account rISSUER`
- `trustlines rISSUER CUR`
- `book-offers XRP CUR:rISSUER`
- `amm-info XRP CUR:rISSUER`
- `account-tx rISSUER LIMIT`
- `subscribe streams=transactions`

## MVP deliverable

A read-only report endpoint/page:

```text
GET /token/:currency/:issuer
```

It returns:

- normalized token identity
- issuer flags/domain
- trustline sample/holder evidence
- DEX/AMM liquidity evidence
- recent activity
- risk flags
- confidence level
- missing-data list
- source/command labels
- cache timestamp / ledger context

## Product rules

- A score without data is worse than no score.
- If fewer than five live datapoints are available, say confidence is low and list what is missing.
- Every report must include source labels and cache freshness.
- No financial advice or guaranteed safety language.

## Testnet demo checklist

- Render a complete-ish token report.
- Render a token with missing liquidity/holder data and make the honesty path visible.
- Trigger one alert from a known account/issuer change if available, or simulate only at the app layer while labeling it simulated.

## Mainnet-safe checklist

- Cache TTLs are explicit.
- Endpoint/rate-limit failures are visible, not swallowed.
- Public reports say "not financial advice".
- The UI separates live facts from derived opinions.
- Alert thresholds are tuned to avoid spam/fatigue.

## Common failure modes

- Fabricated holder counts, ages, liquidity, or risk scores.
- Calling something a rug detector when it is a risk-signal reporter.
- Stale cache shown as live.
- One failed endpoint causing silent false confidence.
- Mixing paid/private API data with public data without source labels.
