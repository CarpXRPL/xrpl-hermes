# XRPL Data APIs — Certification Registry

## Release status

**XRPL JSON-RPC/Clio is the default supported data surface. Third-party token/market endpoint recipes are quarantined until contract-tested.**

The former article contained endpoint tables and aggregation code whose routes had drifted:

- some XRPSCAN account/transaction routes still answered;
- the documented xrpl.to single-token and quote routes returned `404`;
- an XRPLMeta hostname had a TLS mismatch and another route shape returned `400`;
- a documented OnTheDEX route returned an application-level invalid-path response.

A mixed result is not a stable integration contract. The stale runnable snippets were removed.

## Certified default

Use current XRPL JSON-RPC or Clio methods for ledger-native evidence:

- `account_info`
- `account_lines`
- `account_objects`
- `account_tx`
- `book_offers`
- `amm_info`
- `ledger`
- `tx`
- `server_info`

Always record network, endpoint, validated ledger where applicable, fetch time, request method and missing data.

## Third-party acceptance gate

Before adding or restoring any external API route, pin:

1. provider and official API documentation;
2. exact endpoint/method and authentication mode;
3. request and response schema fixtures;
4. TLS/hostname validation;
5. pagination and rate limits;
6. error/application-status semantics;
7. source timestamp and freshness limits;
8. license/attribution and redistribution terms;
9. deterministic tests for success, missing, malformed and rate-limited responses;
10. a current live probe date.

Until then, classify the provider as an **external dependency**, not a working XRPL-Hermes integration.

## Token intelligence boundary

`token-intel` is an XRPL ledger snapshot. Even when all five RPC categories succeed, confidence is capped at **Medium**. It does not establish identity, legal status, full holder concentration, external liquidity, social control or a buy/sell recommendation.

## Official sources

- https://xrpl.org/docs/references/http-websocket-apis/
- https://xrpl.org/docs/references/http-websocket-apis/api-conventions/

Source review date: **2026-07-26**.
