# Xaman Platform — External API Boundary

## Certification posture

**Payload creation is implemented but remains an external dependency.** A credentialed production acceptance run, expiry/reject handling and final-ledger verification remain required before calling an application integration certified end-to-end.

`xaman-payload` is denied over MCP because it creates a real external signing request. It never accepts wallet seeds/private keys.

## Required behavior

- HTTP and application errors become top-level failures.
- Response must contain a valid UUID and trusted HTTPS Xaman signing URL.
- Output declares whether an external side effect was created.
- Raw provider responses and credentials are not echoed.
- Incomplete, signed, secret-bearing, Xahau or non-XRPL payloads are rejected locally.

## Integration workflow

1. create a developer application directly with Xaman;
2. store API credentials in a secret manager/environment outside client code;
3. build and review an unsigned XRPL L1 Payment intent (the only currently certified payload type);
4. create payload with explicit user action;
5. handle signed, rejected, expired and failed provider states;
6. verify network and validated XRPL transaction independently;
7. compare actual transaction fields with the original intent.

Provider callbacks/websockets are untrusted inputs until authenticated and reconciled against the ledger.

Official source: https://docs.xaman.dev/

Reviewed: **2026-07-26**.
