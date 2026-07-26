# Deployment and Hosting Boundary

**Status: external dependency / operational guidance only.**

XRPL-Hermes ships a local package, CLI, default-deny MCP boundary, knowledge corpus, XRPL L1 reads, and unsigned builders. It does **not** ship or certify hosting infrastructure, node packages, bot frameworks, process supervisors, firewall policies, prices, or production deployment configurations.

## Supported installation boundary

From a reviewed clone:

```bash
bash setup.sh
. .venv/bin/activate
python -m scripts.package_acceptance
```

This verifies the local Python environment, CLI registration, MCP allow/deny partition, and packaged knowledge files. It does not establish production readiness for an application built on top.

## Production acceptance checklist

Before operating an XRPL application:

1. Pin and review the application and dependency versions.
2. Use a dedicated non-root service identity and least-privilege filesystem/network access.
3. Keep wallet keys, mnemonics, recovery material and signing credentials outside the agent and application logs.
4. Use a separately accepted user-controlled wallet, HSM, KMS or audited signing system.
5. Select the exact XRPL network explicitly; prove new transaction flows on Testnet first.
6. Validate unsigned intent before authorization and verify the returned transaction on a validated ledger.
7. Set request timeouts, bounded retries, provider-aware rate limits and circuit breakers.
8. Protect RPC, metrics and administrative interfaces; do not expose privileged node interfaces publicly.
9. Configure structured logs without secrets or full sensitive payloads, plus health checks and alerting.
10. Test restart, rollback, backup, recovery and dependency/provider failure behavior.
11. Reproduce the deployment on the selected OS/image rather than copying stale vendor commands.
12. Re-check current first-party documentation for every external provider immediately before deployment.

## XRPL node boundary

A private rippled/Clio deployment is separate infrastructure work. XRPL-Hermes does not certify installation packages, peer/validator settings, storage sizing, pruning policy, amendment voting, Clio ingestion, TLS termination or administrative RPC exposure. See `knowledge/17-xrpl-private-node.md` for the current boundary.

## Third-party hosting and storage

Evernode, Arweave upload/deployment, Bundlr/Irys, IPFS pinning, bridge infrastructure and managed bot hosting remain external dependencies or unimplemented surfaces unless a future release supplies current first-party evidence and reproduced acceptance tests.

**Do not treat old copied deployment snippets, provider prices or screenshots as release evidence.**
