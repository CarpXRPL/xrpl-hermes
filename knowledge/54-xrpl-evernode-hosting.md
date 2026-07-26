# Evernode Hosting — Certification Boundary

## Status

**Not implemented.** XRPL-Hermes does not currently provide a certified Evernode host, tenant, lease, Sashimono/Sashimi, registry, governance, deployment, billing, or Hook integration.

XRPL-Hermes does not implement Evernode host, tenant, lease, wallet, or transaction operations. Use current first-party Evernode documentation and independent Testnet evidence for any integration.

## What may be said safely

Evernode is an ecosystem project associated with decentralized hosting and Xahau-related infrastructure. Its current contracts, governance, network architecture, client software, onboarding process, fees, host requirements, lease semantics, and operational status are volatile and must be verified from current first-party Evernode sources.

Do not infer from this repository that:

- an arbitrary Xahau Payment creates or renews a lease;
- a specific Hook account or state schema is authoritative;
- a particular public endpoint, faucet, registry, token, or governance address is current;
- XRPL-Hermes can deploy a host or workload;
- a lease is enforced by the sample Hook logic formerly shown here;
- wallet seeds should be generated, printed, stored, or passed to an agent;
- historic fees, reserves, hardware requirements, or grant amounts remain valid.

## Safe discovery workflow

1. Identify the current official Evernode website, documentation, source repositories, releases, and network-status channels.
2. Pin source/release commits and verify repository ownership.
3. Determine the exact current network(s), chain/network IDs, endpoints, registry addresses, and token identifiers from first-party sources.
4. Inspect software supply-chain requirements, licenses, container privileges, firewall/port exposure, update mechanism, and secret storage.
5. Reproduce onboarding on an isolated non-production host and Testnet where supported.
6. Keep wallet keys outside Hermes and all application logs.
7. Verify every ledger transaction in decoded unsigned form before user-controlled signing.
8. Record validated transaction hashes, ledger indexes, registry/lease state, host health, workload receipts, and cleanup results.
9. Threat-model tenant isolation, image provenance, denial of service, data persistence, billing disputes, and host compromise.
10. Require explicit approval before production funds, public host registration, DNS changes, or workload exposure.

## Xahau boundary

XRPL-Hermes' certified Xahau capability is limited to:

```bash
python3 scripts/xrpl_tools.py hooks-bitmask TXTYPE...
python3 scripts/xrpl_tools.py hooks-info rACCOUNT [mainnet|testnet]
```

These commands do not compile, serialize, sign, submit, deploy, or manage an Evernode Hook. See `references/xahau-hooks.md`.

## Requirements before implementation

- Current first-party protocol and operator documentation pinned and reviewed.
- Live network identity/endpoints/contracts independently verified.
- Clean isolated installation succeeds from released artifacts.
- No seed/private-key handling by Hermes.
- Host registration and tenant lifecycle proven in a disposable environment.
- Resource isolation and destructive cleanup verified.
- Fees/reserves measured live and labeled with provenance/time.
- Monitoring, upgrades, rollback, incident response, and recovery documented.
- Independent security review accepts the exact release.

Until those gates pass, treat Evernode support as **knowledge discovery only**, not a working integration or product capability.
