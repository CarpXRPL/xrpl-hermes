# Changelog

## v1.9.1 — 2026-07-26

### Changed

- Replaced the public documentation with direct installation, capability, safety, and activation guidance.
- Removed generated audit reports, document tombstones, placeholder examples, and repeated remediation notes from the shipped repository.
- Removed legacy wallet-generation, seed-import, and transaction-broadcast commands from the CLI instead of registering them as disabled.
- Reduced the command surface to 68 local commands: 67 read/unsigned-builder commands over MCP plus local-only Xaman Payment handoff.
- Separated XRPL server amendment status from XRPL-Hermes product capability.

### Fixed

- WebSocket book subscriptions now parse and send the documented `books=ASSET/ASSET` request instead of silently ignoring it.

## v1.9.0 — 2026-07-26

- Packaged the complete knowledge, reference, and workflow corpus in wheel and source distributions.
- Added Python 3.10–3.12 CI and clean-install acceptance.
- Enforced a positive MCP allowlist and signer-separated transaction workflow.
- Added live network reserve derivation and transaction autofill where appropriate.
- Added privacy, seed, command-matrix, compilation, and Markdown-link checks.
- Published reproducible wheel and source artifacts with SHA-256 checksums.

## v1.8.3 — 2026-07-24

- Introduced the default-deny MCP command boundary.
- Removed Batch/XLS-56 from the registered command surface.
- Added regression coverage for MCP command classification and sensitive-operation denial.

## v1.8.2 — 2026-07-09

- Added product-building playbooks for payments, tokens, NFTs, AMMs, treasury, compliance, and monitoring.
- Expanded transaction verification and failure-diagnosis guidance.

## v1.7.0 — 2026-07-09

- Added decision-layer routing and workflow safety guidance.
- Expanded signer-separated transaction planning and validation patterns.

## v1.6.x — 2026-06-16 to 2026-06-17

- Added Python and xrpl.js unsigned-build examples.
- Added agentic XRP and RLUSD payment workflows.
- Added safe on-ledger receipt patterns and model-agnostic developer guidance.
- Expanded amendment and dependency freshness checks.

## v1.5.x — 2026-06-10 to 2026-06-11

- Added MCP client setup, workflow indexes, token intelligence, AMM lookup, and external status-read helpers.
- Added executable examples and stronger regression gates.

## v1.4.x — 2026-06-09 to 2026-06-10

- Introduced the MCP server and packaged knowledge access.
- Corrected currency, issuer, RLUSD, EVM-sidechain, amendment, and bot guidance.
- Added systematic command and documentation verification.

## v1.3.x — 2026-04-30 to 2026-06-08

- Split the original tool suite into domain modules.
- Expanded XRPL reads and unsigned builders across accounts, payments, DEX, AMM, NFTs, escrow, checks, payment channels, MPTs, credentials, oracles, and amendments.
- Added CI, tests, examples, references, and maintenance tooling.

## v1.2 — 2026-04-30

- Added xrpl.js, Xahau, MPT, AMM, DID, and Hooks reference material.

## v1.1 — 2026-04-29

- Improved installation, examples, and documentation consistency.

## v1.0

- Initial XRPL-Hermes knowledge and tool release.
