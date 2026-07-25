# ☤ xrpl-hermes

Open-source XRPL tooling for AI agents and Python users. It combines a 65-file XRPL knowledge base with 72 CLI commands — plus an MCP server that exposes the agent-safe subset of them, and the whole knowledge base, to any MCP client — for live ledger queries, signer-ready transaction JSON, amendment checks, token intelligence, and ecosystem workflows across XRPL L1, issued tokens, NFTs, AMMs, MPTs, Xaman, Xahau, Flare, Axelar, Arweave, and the XRPL EVM Sidechain.

**Custody boundary:** all 72 commands run locally. Over MCP, an agent gets 67 of them — read-only queries and unsigned builders. The five that touch key material, broadcast, or create an external signing request (`wallet-generate`, `wallet-from-seed`, `submit`, `submit-multisigned`, `xaman-payload`) are refused over MCP and stay in your local CLI. See [MCP agent boundary](#mcp-agent-boundary).

**Staying current:** xrpl-hermes ships with markdown knowledge, but agents are instructed to verify live ledger state and current official docs before making claims (`knowledge/65-agent-freshness-and-source-policy.md`). Stale-able facts in the knowledge base are date-stamped where they appear.

[![GitHub stars](https://img.shields.io/github/stars/CarpXRPL/xrpl-hermes?style=social)](https://github.com/CarpXRPL/xrpl-hermes)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
[![CI](https://github.com/CarpXRPL/xrpl-hermes/actions/workflows/ci.yml/badge.svg)](https://github.com/CarpXRPL/xrpl-hermes/actions/workflows/ci.yml)

## What this is

xrpl-hermes is a practical builder kit. The agent/MCP flow never accepts wallet seeds or broadcasts transactions, and it does not pretend draft features are live. Optional key and broadcast utilities remain local-CLI-only and outside the agent boundary. The normal flow is:

1. read the relevant knowledge file,
2. check live network/amendment status when the feature depends on one,
3. build signer-ready JSON,
4. let the user sign with their own wallet or signing stack.

It also includes **Product Builder Mode** for product-altitude work: when the user wants an app,
dashboard, launchpad, paid API, treasury tool, token intelligence product, or self-hosted XRPL agent
stack, the skill routes through intake → architecture → XRPL primitive map → MVP → testnet demo →
mainnet-safe launch gates before emitting transaction JSON. Canonical flow:
[`skills/build-xrpl-product-flow.md`](skills/build-xrpl-product-flow.md); human hub:
[`docs/PRODUCT-BUILDER.md`](docs/PRODUCT-BUILDER.md).

## Who this is for — and what it is not

**For:** XRPL and agent builders who want AI-assisted research, unsigned transaction construction,
token intelligence, and payment / x402 flows — in Python (`xrpl-py`) or JavaScript/TypeScript
(`xrpl.js`), from a Hermes skill or any MCP client. **Not:** a wallet or seed-custody service, an
auto-signer that moves funds on its own, or a "self-evolving" hype demo. The agent prepares,
verifies, explains, and monitors; your wallet/signing stack signs. Keys stay with you.

**Three ways to use it:** as **MCP tools** in any MCP client ([`docs/MCP-CLIENTS.md`](docs/MCP-CLIENTS.md)),
as a **Python** CLI/library (`xrpl-py`), or alongside your **JavaScript/TypeScript** app code
(`xrpl.js`) — see *Choose your stack* below.

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
- **Keys stay yours.** Builders and MCP tools emit signer-ready JSON without accepting or storing a seed. Optional local-only wallet utilities are never exposed to agents.
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
| Treasury & escrow | Multisig, tickets, checks, escrow, payment channels (`build-*`, `submit-multisigned`) | CLI |
| EVM Sidechain | Balance, contract-deploy JSON, bridge status (`evm-balance`, `evm-contract`, `evm-bridge`) | live tool + ref |
| Xahau Hooks | HookOn bitmask calculator + hooks lookup (`hooks-bitmask`, `hooks-info`) | CLI + live tool |
| Flare price context | On-chain FTSOv2 oracle reads + a public price fallback (`flare-ftso`, `flare-price`) | live tool |
| Axelar bridge | Route/registration status and transfer tracking (`bridge-status`, `bridge-tx`) | live tool |
| Arweave storage | Permanent-storage cost estimates, never uploads (`arweave-cost`) | live tool |
| Token intelligence | One-shot live token report with risk flags + missing-data honesty (`token-intel`) | live tool |
| Attention bridge / social cards | Product framing for "bring eyes to XRPL" / discovery ideas (`references/xrpl-attention-bridge.md`) | ref |
| Agent / skill receipts | Record what an agent did, or how a skill improved (v1→v2), as an unsigned on-chain `NFTokenMint` — provenance, timestamp, public verifiability; no seed, no autonomous signing (`build-nft-mint` + `skills/agent-receipt-flow.md` + `examples/js/agent-receipt-nft.js`) | CLI + pattern |

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
| [`docs/PRODUCT-BUILDER.md`](docs/PRODUCT-BUILDER.md) | Product Builder Mode — app/platform/dashboard archetypes, 5-box architecture, and links to product playbooks |
| [`docs/MCP-CLIENTS.md`](docs/MCP-CLIENTS.md) | Hooking the MCP server into Claude Code, Cursor, Codex, Hermes, or any MCP client |
| [`docs/DEVELOPERS.md`](docs/DEVELOPERS.md) | Architecture, adding commands, MCP internals, testing, release flow |
| [`docs/MAINTENANCE.md`](docs/MAINTENANCE.md) | Freshness cadence and the exact verification commands that keep the repo current |
| [`STANDALONE.md`](STANDALONE.md) | In-depth CLI usage for the common commands (full 72-command list: `SKILL.md` tool table) |
| [`SECURITY.md`](SECURITY.md) · [`LIMITATIONS.md`](LIMITATIONS.md) | Safety model and honest scope |
| [`AUDIT-tool-matrix.md`](AUDIT-tool-matrix.md) | Generated verification matrix — safe commands exercised, side-effect commands explicitly skipped, zero failures |
| [`docs/BUILD-BENCHMARK.md`](docs/BUILD-BENCHMARK.md) | Build-proof benchmark — L1→L3 + adversarial safety tasks proving an agent builds on XRPL safely (complements the tool matrix) |
| [`skills/agent-receipt-flow.md`](skills/agent-receipt-flow.md) · [`references/track-agent-behavior.md`](references/track-agent-behavior.md) | Agent provenance: record a run as an unsigned on-chain receipt, and attribute/monitor behavior (SourceTag · Memos · WebSocket) |

## Command coverage

72 commands are split across focused Python modules in `scripts/tools/`. All 72 run locally; 67 of them are also reachable over MCP (see [MCP agent boundary](#mcp-agent-boundary)).

| Ecosystem | Count | Commands |
|---|---:|---|
| XRPL L1 core and ops | 41 | `account`, `balance`, `account_objects`, `account-tx`, `trustlines`, `build-payment`, `build-trustset`, `build-offer`, `book-offers`, `path-find`, `ledger`, `ledger-entry`, `server-info`, `tx-info`, `decode`, `submit`, `submit-multisigned`, `build-account-set`, `build-account-delete`, `build-set-regular-key`, `build-deposit-preauth`, `build-signer-list-set`, `build-ticket-create`, `build-escrow-create`, `build-escrow-finish`, `build-escrow-cancel`, `build-check-create`, `build-check-cash`, `build-check-cancel`, `build-paychannel-create`, `build-paychannel-fund`, `build-paychannel-claim`, `build-clawback`, `build-cross-currency-payment`, `build-set-oracle`, `build-credential-create`, `build-credential-accept`, `build-credential-delete`, `build-mpt-issuance-create`, `build-mpt-authorize`, `subscribe` |
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

`build-batch` is retired and unregistered because XLS-56 Batch is not enabled on XRPL mainnet. MPT, Credential, and Oracle builders check the live amendment state before emitting JSON.

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

`scripts/mcp_server.py` is a dependency-free stdio MCP server exposing four tools: `xrpl_list_commands`, `xrpl_run` (the 67 agent-safe commands), `xrpl_knowledge_index`, and `xrpl_knowledge`.

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

Commands run in a subprocess with a 90s timeout; knowledge reads are sandboxed to `knowledge/`, `references/`, and `skills/`. The server never asks for or stores secret keys.

## MCP agent boundary

`xrpl_run` is a **positive allowlist with default-deny**. The 72 local CLI commands partition
exactly into 67 that an agent may run and 5 that it may not:

| Surface | Count | What it covers |
|---|---:|---|
| **Local CLI** — `python3 -m scripts.xrpl_tools` | **72** | Every registered command |
| **MCP-safe** — `xrpl_run` / `xrpl_list_commands` | **67** | Read-only live queries and unsigned, signer-ready builders |
| **Denied over MCP** — local CLI only | **5** | `wallet-generate`, `wallet-from-seed`, `submit`, `submit-multisigned`, `xaman-payload` |

Those five are the custody and broadcast surface: two touch secret key material
(`wallet-generate` emits a seed, `wallet-from-seed` consumes one), two broadcast to a live
network, and one creates a real external wallet signing request. They still work exactly as
before when *you* run them locally — they are simply not something an agent can reach.

- A denied command is refused **before any subprocess is spawned**, so it never executes and no
  MCP response can carry a seed. The refusal names the local CLI invocation to use instead.
- `xrpl_list_commands` lists only the agent-safe set, so a client cannot discover a denied
  command and try it.
- The allowlist is positive: any command not on it — **including commands added in future
  releases** — is denied until a maintainer classifies it. New key-touching commands are safe by
  default rather than exposed by accident.

`tests/test_mcp_server.py` enforces this as an invariant: the allowlist and deny-list must be
disjoint and must exactly cover the dispatcher, so a new command cannot ship unclassified.

## Safety model

- No hardcoded wallet seeds or private keys.
- Transaction builders output JSON for external signing.
- Key-management, broadcast, and Xaman signing-request commands are local-CLI-only and denied over MCP.
- `submit` exists for advanced users with signed blobs only.
- Amendment-dependent builders check live XRPL mainnet status or emit build-only warnings.
- Flare price output is labeled by source: `flare-price` is a public price fallback, while `flare-ftso` performs live read-only FTSOv2 `eth_call` lookups.

## Development checks

```bash
python3 -m pytest -q
python3 scripts/dev_test_matrix.py
```

The dev-test matrix writes `AUDIT-tool-matrix.md`, exercises the safe registered commands without sending real transactions, and explicitly records commands skipped to prevent seed generation or external signing requests.

## Contributing

Use the module pattern in `scripts/tools/`: each module exposes a `COMMANDS` dict and emits JSON through shared helpers. Add or update focused pytest coverage when changing command output.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`CHANGELOG.md`](CHANGELOG.md).

## License

MIT. Free to use, fork, and build with.
