# ☤ XRPL-Hermes

Open-source XRPL knowledge, live reads, and unsigned transaction builders for AI agents and Python users.

**You choose the model. XRPL-Hermes provides the XRPL layer. Your wallet keeps the keys and signs. Hermes verifies the validated result.**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
[![CI](https://github.com/CarpXRPL/xrpl-hermes/actions/workflows/ci.yml/badge.svg)](https://github.com/CarpXRPL/xrpl-hermes/actions/workflows/ci.yml)

## Install

```bash
git clone https://github.com/CarpXRPL/xrpl-hermes.git
cd xrpl-hermes
bash setup.sh
. .venv/bin/activate
xrpl-hermes server-info
```

Build an unsigned payment:

```bash
xrpl-hermes build-payment \
  --from rSOURCE \
  --to rDESTINATION \
  --amount 1000000
```

The result is unsigned JSON. Review it, authorize it in your own wallet or signing system, and verify the returned transaction hash:

```bash
xrpl-hermes tx-info TRANSACTION_HASH
```

Never paste a seed, private key, or mnemonic into Hermes, an MCP client, or a CLI argument.

## Available now

| Area | Available capability | Surface |
|---|---|---|
| XRPL accounts and ledger | Account, balance, objects, transaction history, ledger entries, server state, transaction lookup and decoding | CLI + MCP |
| Payments and DEX | XRP/issued-currency payments, path finding, trust lines, offers and order books | CLI + MCP |
| Tokens | Issuer settings, clawback, MPT issuance/authorization, credentials and token-intelligence reads | CLI + MCP |
| NFTs | Mint, burn, offer discovery, create/accept/cancel offers | CLI + MCP |
| AMM | Pool reads plus create/deposit/withdraw/vote/bid unsigned builders | CLI + MCP |
| Account operations | AccountSet, regular key, DepositPreauth, signer lists, tickets and AccountDelete builders | CLI + MCP |
| Escrow, checks and channels | Unsigned create/finish/cancel/cash/fund/claim builders | CLI + MCP |
| XRPL amendments | Live enabled/supported/vetoed status from public XRPL Mainnet servers | CLI + MCP |
| Xahau | HookOn calculation and validated installed-Hook lookup | CLI + MCP |
| XRPL EVM Sidechain | Available balance/network reads and unsigned contract intent; deployment requires external setup | CLI + MCP |
| Flare | Read-only FTSOv2 calls and separately labeled market-price context | CLI + MCP |
| Axelar | Registration and GMP-index lookups; no transfer execution | CLI + MCP |
| Arweave | Point-in-time base-network storage cost estimate; no upload | CLI + MCP |
| Xaman | Payment-only wallet request after local validation | Local CLI with Xaman credentials |

The dispatcher contains **68 commands**. **67** are read-only or unsigned and available through MCP. `xaman-payload` is local-only because calling it creates a real external wallet request.

List the exact installed surface:

```bash
xrpl-hermes-mcp  # use xrpl_list_commands from your MCP client
python3 -m scripts.xrpl_tools  # prints CLI usage and commands
```

## External setup

### MCP

After installation, point any stdio MCP client at the environment’s executable:

```text
/path/to/xrpl-hermes/.venv/bin/xrpl-hermes-mcp
```

See [`docs/MCP-CLIENTS.md`](docs/MCP-CLIENTS.md) for client configurations.

### Xaman

Xaman request creation is deliberately local rather than autonomous MCP behavior. Configure application credentials in the local process environment:

```bash
export XUMM_API_KEY='...'
export XUMM_API_SECRET='...'
xrpl-hermes xaman-payload '{"TransactionType":"Payment","Account":"rSOURCE","Destination":"rDESTINATION","Amount":"1000000"}'
```

A payload URL is not proof of signing or settlement. Verify the final transaction independently with `tx-info`.

### Private XRPL infrastructure

Public XRPL endpoints are used by default. To use infrastructure you operate or separately trust:

```bash
export XRPL_PRIVATE_RPC='https://your-rpc.example'
```

## Not shipped

These are intentionally absent—not hidden features waiting to be enabled:

- wallet generation, seed import, private-key handling, signing, or transaction broadcast;
- XRPL Batch/XLS-56 construction;
- XRPL↔EVM or Axelar transfer execution;
- Xahau Hook compilation, serialization, signing, or deployment;
- Arweave uploads;
- an x402 facilitator or settlement service;
- node hosting or managed infrastructure.

`amendment` reports public XRPL Mainnet server state. A server may know a protocol amendment that Mainnet has not activated. That describes the server/network, not an XRPL-Hermes feature. A command exists only when it appears in the CLI or `xrpl_list_commands`.

## Knowledge and workflows

The package includes 65 knowledge files, 15 reference cards, and focused operation/product workflows. Current ledger facts—fees, reserves, amendments, balances, liquidity and transaction state—must come from live tools or current official sources, not a dated Markdown snapshot.

Start here:

- [`QUICKSTART.md`](QUICKSTART.md) — first reads and unsigned build
- [`docs/BEGINNERS.md`](docs/BEGINNERS.md) — XRPL concepts and safe first session
- [`docs/WORKFLOWS.md`](docs/WORKFLOWS.md) — capability-to-command map
- [`docs/MCP-CLIENTS.md`](docs/MCP-CLIENTS.md) — MCP client setup
- [`SECURITY.md`](SECURITY.md) — custody and reporting policy
- [`LIMITATIONS.md`](LIMITATIONS.md) — exact boundaries
- [`SKILL.md`](SKILL.md) — Hermes skill instructions and command catalog

## Development

```bash
python3 -m pytest -q
python3 scripts/dev_test_matrix.py
python3 scripts/audit_project_quality.py
python3 -m scripts.package_acceptance
```

The matrix prints machine-readable results. Set `XRPL_HERMES_MATRIX_REPORT=/path/report.md` only when you want a local detailed report; generated audit output is not committed as product documentation.

## License

MIT. See [`LICENSE`](LICENSE).
