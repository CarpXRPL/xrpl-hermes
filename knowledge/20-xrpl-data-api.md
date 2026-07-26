# XRPL Data APIs — Certification Registry

## Available data surface

XRPL JSON-RPC and Clio are the implemented data surfaces. Third-party token and market APIs are not part of the shipped command set.

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
