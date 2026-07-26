# XRPL Private Node — External Operations Boundary

Running rippled or Clio is an external infrastructure operation, not a certified XRPL-Hermes deployment workflow.

## Current status

- XRPL-Hermes does not ship node installation, images, packages, peer lists, validator configuration, hardware sizing, or hosting guidance.
- A self-hosted node still has CPU, disk, network and configured API limits. Do not claim “unlimited” access or “no rate limits.”
- Never expose admin RPC/gRPC/WebSocket interfaces publicly.
- Never disable TLS verification.
- Validator operation is materially different from running a stock API node and needs a dedicated, current security review.

## Acceptance required before deployment

1. Use current first-party instructions from [XRPL.org](https://xrpl.org/docs/infrastructure/installation/) and the current rippled/Clio release notes.
2. Pin and verify exact package/image versions and signatures.
3. Bind admin interfaces to localhost or an authenticated private network; separate public read endpoints.
4. Enable TLS verification, firewalling, authentication, request limits and monitoring.
5. Verify storage growth, online deletion, backup/recovery and ledger-history requirements in staging.
6. Record observed `server_info`, network identity, build version and validated-ledger freshness.
7. Independently penetration-test any externally reachable API.

## Hermes use

A private RPC may be supplied through `XRPL_PRIVATE_RPC` only after the operator completes that acceptance. Hermes treats it as an external dependency and does not certify the server merely because a request succeeds.
