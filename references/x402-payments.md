# x402 / HTTP-402 on XRPL — Design Reference

## Status

**Reference only.** XRPL-Hermes does not ship an x402 package, facilitator, header implementation, network adapter, fee service, receipt service, or unattended payment loop.

Hermes can build and inspect an unsigned XRPL L1 Payment that may be used by a separately accepted x402 implementation. It does not sign, submit, retry a paid request or authorize spending.

## Safe architecture

1. Receive a 402 challenge from a separately trusted service.
2. Validate the challenge schema, destination, asset, amount, invoice/memo, network, expiry and facilitator identity.
3. Enforce per-request/session limits and destination/issuer allowlists.
4. Build unsigned Payment JSON with `build-payment`.
5. Present exact intent to a compatible user-owned external wallet/signing policy layer.
6. Compare the authorized transaction with reviewed intent.
7. Verify the returned hash on a validated ledger with `tx-info`.
8. Treat any facilitator receipt as additional external evidence, not a replacement for ledger verification.

## Uncertified claims

Do not assume:

- automatic payment without user/policy authorization;
- a fixed confirmation time;
- any current facilitator URL or service-level agreement;
- specific SDK/package names or method signatures;
- XRP, RLUSD or another asset is accepted by a given merchant;
- receipt replay protection, custody behavior or settlement finality without reproduced evidence.

Testnet acceptance is required before considering a policy-gated Mainnet flow. Mainnet requires explicit authorization, value limits, monitoring and a circuit breaker.

Sources must be rechecked at implementation time:

- [XRPL agentic payments/x402 documentation](https://xrpl.org/docs/agents/agentic-payments-x402/)
- Current first-party documentation for the selected facilitator and merchant implementation
