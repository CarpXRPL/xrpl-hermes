# Deployment Templates Retired

The former rippled/Clio Docker stack in this directory is **retired and removed** as of XRPL-Hermes v1.9.0.

XRPL-Hermes certifies its own package, CLI, default-deny MCP boundary and signer-separated XRPL workflows. It does **not** certify or maintain:

- rippled/Clio/PostgreSQL container images or configuration;
- validator/UNL, storage, firewall, TLS, backup or upgrade policy;
- cloud-vendor sizing, prices or sync-time estimates;
- public exposure of node RPC/WebSocket ports;
- production node availability or historical-ledger retention.

A stale node template is worse than no template: image names, database schemas, signing keys, protocol defaults, resource needs and network hardening guidance change independently of this project.

If you operate XRPL infrastructure, start from current first-party [XRPL infrastructure documentation](https://xrpl.org/docs/infrastructure) and the exact release notes for the rippled/Clio versions you select. Pin and verify artifacts, keep RPC private by default, require TLS/auth at any boundary, test restore/upgrade procedures, and monitor validated-ledger freshness.

XRPL-Hermes may read from an endpoint you separately operate via `XRPL_PRIVATE_RPC`; that configuration does not certify the node behind it. New flows remain Testnet-first.
