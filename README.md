# ☤ xrpl-hermes

Open-source XRPL tooling for AI agents and Python users. It combines a 65-file XRPL knowledge base with 73 CLI commands — plus an MCP server that exposes all of it to any MCP client — for live ledger queries, signer-ready transaction JSON, amendment checks, token intelligence, and ecosystem workflows across XRPL L1, issued tokens, NFTs, AMMs, MPTs, Xaman, Xahau, Flare, Axelar, Arweave, and the XRPL EVM Sidechain.

**Staying current:** xrpl-hermes ships with markdown knowledge, but agents are instructed to verify live ledger state and current official docs before making claims (`knowledge/65-agent-freshness-and-source-policy.md`). Stale-able facts in the knowledge base are date-stamped where they appear.

[![GitHub stars](https://img.shields.io/github/stars/CarpXRPL/xrpl-hermes?style=social)](https://github.com/CarpXRPL/xrpl-hermes)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
[![CI](https://github.com/CarpXRPL/xrpl-hermes/actions/workflows/ci.yml/badge.svg)](https://github.com/CarpXRPL/xrpl-hermes/actions/workflows/ci.yml)

## What this is

xrpl-hermes is a practical builder kit. It does not ask for wallet seeds, it does not submit transactions for you by default, and it does not pretend draft features are live. The normal flow is:

1. read the relevant knowledge file,
2. check live network/amendment status when the feature depends on one,
3. build signer-ready JSON,
4. let the user sign with their own wallet or signing stack.

## Choose your stack — Python *or* TypeScript/JavaScript

The XRPL-Hermes **CLI and MCP server run on Python (`xrpl-py`)** — that's the engine that
emits signer-ready JSON, checks live amendments, and runs token intelligence. The code **you**
build for your own project can be either language; both are first-class:

| Stack | SDK | Install | First-class for | Deep file |
|---|---|---|---|---|
| **Python** | `xrpl-py` | `pip install xrpl-py` | FastAPI services, scripts, data jobs, server-side bots, the Hermes CLI itself | [`knowledge/30-xrpl-xrplpy.md`](knowledge/30-xrpl-xrplpy.md) |
| **TypeScript / JavaScript** | `xrpl.js` | `npm install xrpl` | web apps, dashboards, wallet UX, browser dApps, Node bots, x402 services, AI-agent CLIs | [`knowledge/31-xrpl-xrpljs.md`](knowledge/31-xrpl-xrpljs.md) · [`examples/js/`](examples/js/) |

The builders emit the same signer-ready JSON either way — pick the SDK that matches your codebase
and **don't introduce a second language** just to use this kit. Runnable, build-only payment
examples for both stacks live in [`examples/`](examples/) (Python) and [`examples/js/`](examples/js/)
(xrpl.js). The signer-separated model is the same in both:
[`references/agentic-payments.md`](references/agentic-payments.md).

## Run your own XRPL agent

XRPL-native agents — pre-trained on the ledger, able to launch tokens, deploy sites, and run bots — exist today as hosted platforms. xrpl-hermes is not a pitch against any of them. It is the open-source path for people who want to run that kind of agent themselves:

- **Bring your own runtime.** Works as a Hermes Agent skill, or in OpenClaw, Claude Code, Cursor, and anything else that speaks MCP.
- **Bring your own infrastructure.** Your machine, your VPS, or your own rippled/Clio node — public endpoints work out of the box.
- **Keys stay yours.** Builders emit signer-ready JSON for your wallet; nothing here asks for or stores a seed.
- **MIT licensed.** Use it, fork it, ship it inside your own product.

If a hosted platform fits you better, use it — this repo exists so that self-hosting is a real option, not a compromise.

## Build anything on XRPL with AI agents

A practical map of what you can build, with an **honest label** for how far XRPL-Hermes takes you:
**CLI** = shipped command(s); **live tool** = makes a live network read; **ref** = reference card +
knowledge file; **pattern** = integration pattern / runnable example; **roadmap** = documented design,
not a shipped feature.

| Build | What XRPL-Hermes gives you | Label |
|---|---|---|
| Issued token launch | Issuer flags, trust lines, domain, transfer rate, freeze/clawback, supply flow (`build-account-set`, `build-trustset`, `build-clawback`) + `skills/token-launch-flow.md` | CLI + flow |
| NFT marketplace | Mint, create/accept/cancel offers, discover offers, burn (7 `nft`/`build-nft-*` commands) | CLI + live tool |
| AMM / DEX | Create pools, deposit/withdraw, vote fees, auction-slot bids, live pool + orderbook reads (`build-amm-*`, `amm-info`, `book-offers`, `path-find`) | CLI + live tool |
| Payments (XRP) | Signer-ready `Payment` JSON with `SourceTag`/`DestinationTag`/`Memos`, reserve-aware (`build-payment`) — Python + xrpl.js examples | CLI |
| RLUSD / issued-currency | Dollar-denominated payments with 160-bit currency codes + trust-line and compliance guidance (`references/rlusd.md`, `knowledge/58`) | CLI + ref |
| x402 / HTTP-402 paid APIs | The XRPL Payment that settles a 402 charge + the t54-facilitator flow | ref + roadmap |
| Bots & monitors | Treasury/AMM monitor playbooks, Telegram/Discord examples, WebSocket `subscribe` | CLI + pattern |
| Wallets & auth | Xaman/Joey/Privy/MetaMask login + signer handoff (`xaman-payload`, `knowledge/53`) | live tool + ref |
| MPT operations | MPT issuance/authorization payloads with live amendment checks (`build-mpt-*`) | CLI |
| Treasury & escrow | Multisig, tickets, checks, escrow, payment channels, batch (`build-*`, `submit-multisigned`) | CLI |
| EVM Sidechain | Balance, contract-deploy JSON, bridge status (`evm-balance`, `evm-contract`, `evm-bridge`) | live tool + ref |
| Xahau Hooks | HookOn bitmask calculator + hooks lookup (`hooks-bitmask`, `hooks-info`) | CLI + live tool |
| Flare price context | On-chain FTSOv2 oracle reads + a public price fallback (`flare-ftso`, `flare-price`) | live tool |
| Axelar bridge | Route/registration status and transfer tracking (`bridge-status`, `bridge-tx`) | live tool |
| Arweave storage | Permanent-storage cost estimates, never uploads (`arweave-cost`) | live tool |
| Token intelligence | One-shot live token report with risk flags + missing-data honesty (`token-intel`) | live tool |
| Attention bridge / social cards | Product framing for "bring eyes to XRPL" / discovery ideas (`references/xrpl-attention-bridge.md`) | ref |

Both stacks are first-class for the code you write on top — see **Choose your stack** above.

## Quick start

```bash
pip install -r requirements.txt
python3 -m scripts.xrpl_tools ledger
```

Useful first commands:

```bash
python3 -m scripts.xrpl_tools server-info
python3 -m scripts.xrpl_tools amendments
python3 -m scripts.xrpl_tools amendment MPTokensV1
python3 -m scripts.xrpl_tools account rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe
python3 -m scripts.xrpl_tools build-payment --from rSRC --to rDST --amount 10000000
```

## Documentation

| Guide | For |
|---|---|
| [`QUICKSTART.md`](QUICKSTART.md) | Install and first commands in 5 minutes |
| [`docs/BEGINNERS.md`](docs/BEGINNERS.md) | New to XRPL and agent CLIs — concepts, safety, first session |
| [`docs/WORKFLOWS.md`](docs/WORKFLOWS.md) | Ecosystem workflow index — commands, knowledge, and honest coverage labels per ecosystem |
| [`docs/MCP-CLIENTS.md`](docs/MCP-CLIENTS.md) | Hooking the MCP server into Claude Code, Cursor, Codex, Hermes, or any MCP client |
| [`docs/DEVELOPERS.md`](docs/DEVELOPERS.md) | Architecture, adding commands, MCP internals, testing, release flow |
| [`STANDALONE.md`](STANDALONE.md) | In-depth CLI usage for the common commands (full 73-command list: `SKILL.md` tool table) |
| [`SECURITY.md`](SECURITY.md) · [`LIMITATIONS.md`](LIMITATIONS.md) | Safety model and honest scope |
| [`AUDIT-tool-matrix.md`](AUDIT-tool-matrix.md) | Generated verification matrix — every command, live-tested |

## Command coverage

73 commands are split across focused Python modules in `scripts/tools/`.

| Ecosystem | Count | Commands |
|---|---:|---|
| XRPL L1 core and ops | 42 | `account`, `balance`, `account_objects`, `account-tx`, `trustlines`, `build-payment`, `build-trustset`, `build-offer`, `book-offers`, `path-find`, `ledger`, `ledger-entry`, `server-info`, `tx-info`, `decode`, `submit`, `submit-multisigned`, `build-account-set`, `build-account-delete`, `build-set-regular-key`, `build-deposit-preauth`, `build-signer-list-set`, `build-ticket-create`, `build-escrow-create`, `build-escrow-finish`, `build-escrow-cancel`, `build-check-create`, `build-check-cash`, `build-check-cancel`, `build-paychannel-create`, `build-paychannel-fund`, `build-paychannel-claim`, `build-clawback`, `build-cross-currency-payment`, `build-batch`, `build-set-oracle`, `build-credential-create`, `build-credential-accept`, `build-credential-delete`, `build-mpt-issuance-create`, `build-mpt-authorize`, `subscribe` |
| Amendment status | 3 | `amendments`, `amendment`, `amendment-status` |
| NFT marketplace | 7 | `nft-info`, `nft-offers`, `build-nft-mint`, `build-nft-create-offer`, `build-nft-accept-offer`, `build-nft-cancel-offer`, `build-nft-burn` |
| AMM liquidity | 6 | `amm-info`, `build-amm-create`, `build-amm-deposit`, `build-amm-withdraw`, `build-amm-vote`, `build-amm-bid` |
| Token intelligence | 1 | `token-intel` |
| EVM Sidechain | 3 | `evm-balance`, `evm-contract`, `evm-bridge` |
| Xahau Hooks | 2 | `hooks-bitmask`, `hooks-info` |
| Flare / price context | 2 | `flare-price`, `flare-ftso` |
| Axelar / Arweave | 3 | `bridge-status`, `bridge-tx`, `arweave-cost` |
| Wallet utils | 3 | `wallet-generate`, `wallet-from-seed`, `validate-address` |
| Xaman Platform | 1 | `xaman-payload` |

`build-batch` now warns when Batch is not enabled on XRPL mainnet. MPT, Credential, and Oracle builders also check the live amendment state before emitting JSON.

## Knowledge map

| Range | Topics |
|---|---|
| `01`-`15` | XRPL accounts, payments, trust lines, DEX, AMM, NFTs, clawback, MPTs, escrow, checks, channels, multisig, tickets, consensus, transaction format |
| `16`-`25` | Clio, private nodes, rate limits, costs, Data API, token model, issuance, NFT minting, deployment, security |
| `26`-`35` | Xaman, wallets, Privy, MetaMask, xrpl-py, xrpl.js, Hooks, EVM, AMM bots, interop |
| `36`-`45` | XLS standards, live amendments, minting ops, NFT ops, monitoring, bot patterns, treasury, advanced hooks/EVM, ecosystem map |
| `46`-`55` | Axelar, Arweave, TX ecosystem, Flare, EVM Sidechain, Xahau, L1 reference, wallet auth, Evernode, sidechain interop |
| `56`-`63` | Telegram bots, Discord bots, RLUSD, RWA tokenization, AccountSet flags, WebSocket streams, NFT marketplaces, Xaman Platform |
| `64`-`65` | Token intelligence reports, agent freshness and source policy |

## Hermes Agent installation

```bash
git clone https://github.com/CarpXRPL/xrpl-hermes.git
cd xrpl-hermes
pip install -r requirements.txt

# Install as a local Hermes skill. Use the path your Hermes profile loads from.
mkdir -p ~/.hermes/skills
cp -r . ~/.hermes/skills/xrpl-hermes
```

Activate with:

```text
activate xrpl-hermes
```

## MCP server (Claude Code, OpenClaw, Cursor, any MCP client)

`scripts/mcp_server.py` is a dependency-free stdio MCP server exposing four tools: `xrpl_list_commands`, `xrpl_run` (any of the 73 commands), `xrpl_knowledge_index`, and `xrpl_knowledge`.

```bash
# Claude Code
claude mcp add xrpl-hermes -- python3 /path/to/xrpl-hermes/scripts/mcp_server.py
```

Generic MCP client config:

```json
{
  "mcpServers": {
    "xrpl-hermes": {
      "command": "python3",
      "args": ["/path/to/xrpl-hermes/scripts/mcp_server.py"]
    }
  }
}
```

Commands run in a subprocess with a 90s timeout; knowledge reads are sandboxed to `knowledge/` and `references/`. The server never asks for or stores secret keys.

## Safety model

- No hardcoded wallet seeds or private keys.
- Transaction builders output JSON for external signing.
- `submit` exists for advanced users with signed blobs only.
- Amendment-dependent builders check live XRPL mainnet status or emit build-only warnings.
- Flare price output is labeled by source: `flare-price` is a public price fallback, while `flare-ftso` performs live read-only FTSOv2 `eth_call` lookups.

## Development checks

```bash
python3 -m pytest -q
python3 scripts/dev_test_matrix.py
```

The dev-test matrix writes `AUDIT-tool-matrix.md` and verifies all registered commands without sending real transactions.

## Contributing

Use the module pattern in `scripts/tools/`: each module exposes a `COMMANDS` dict and emits JSON through shared helpers. Add or update focused pytest coverage when changing command output.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`CHANGELOG.md`](CHANGELOG.md).

## License

MIT. Free to use, fork, and build with.
