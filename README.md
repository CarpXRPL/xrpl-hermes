# ☤ xrpl-hermes

Open-source XRPL tooling for AI agents and Python users. It combines a curated XRPL knowledge base with **72 local CLI commands**. The MCP server exposes only the default-deny agent-safe subset (currently 67). XRPL L1 reads and unsigned builders are the certified core; adjacent-network/provider tools are narrowly labeled as experimental reads, external side effects, or quarantined workflows.

**Custody boundary:** the dispatcher registers 72 commands. Over MCP, an agent gets 67—read-only queries and unsigned builders. Five sensitive registrations are refused before execution; legacy key/broadcast surfaces are quarantined, while guarded `xaman-payload` is a local Payment-only external side effect. See [MCP agent boundary](#mcp-agent-boundary).

**Staying current:** xrpl-hermes ships with markdown knowledge, but agents are instructed to verify live ledger state and current official docs before making claims (`knowledge/65-agent-freshness-and-source-policy.md`). Stale-able facts in the knowledge base are date-stamped where they appear.

[![GitHub stars](https://img.shields.io/github/stars/CarpXRPL/xrpl-hermes?style=social)](https://github.com/CarpXRPL/xrpl-hermes)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
[![CI](https://github.com/CarpXRPL/xrpl-hermes/actions/workflows/ci.yml/badge.svg)](https://github.com/CarpXRPL/xrpl-hermes/actions/workflows/ci.yml)

## What this is

xrpl-hermes is a practical builder kit. The agent/MCP flow never accepts wallet seeds or broadcasts transactions, and it does not pretend draft features are live. Legacy key and broadcast registrations are quarantined and MCP-denied. The normal flow is:

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

XRPL-Hermes is an open-source XRPL infrastructure layer for people who want to run an agent with explicit custody, network and certification boundaries:

- **Bring your own runtime.** Works as a Hermes Agent skill, or in OpenClaw, Claude Code, Cursor, and anything else that speaks MCP.
- **Bring your own infrastructure.** Your machine, VPS, or separately operated rippled/Clio node. Public endpoints are convenient external dependencies, not availability guarantees.
- **Keys stay yours.** Builders and MCP tools emit signer-ready JSON without accepting or storing a seed. Legacy key utilities are quarantined and never exposed to agents.
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
| x402 / HTTP-402 paid APIs | Experimental external integration plan around an unsigned XRPL Payment; no provider/package certified | ref + roadmap |
| Bots & monitors | Treasury/AMM monitor playbooks, Telegram/Discord examples, WebSocket `subscribe` | CLI + pattern |
| Wallets & auth | External wallet boundaries; Xaman payload creation is local-only and requires configured app credentials | external dependency + guarded tool |
| MPT operations | MPT issuance/authorization payloads with live amendment checks (`build-mpt-*`) | CLI |
| Treasury & escrow | Unsigned multisig, ticket, check, escrow and payment-channel builders; external authorization/broadcast | CLI build + external signer |
| EVM Sidechain | Validated balance/network reads; experimental contract intent; no bridge certification (`evm-balance`, `evm-contract`, `evm-bridge`) | experimental read/build |
| Xahau Hooks | Legacy HookOn calculator + validated Mainnet/Testnet chain lookup; no compile/build/sign/deploy (`hooks-bitmask`, `hooks-info`) | CLI + live read |
| Flare price context | Chain-ID/freshness-checked FTSOv2 reads; CoinGecko fallback is market context only (`flare-ftso`, `flare-price`) | narrow live read |
| Axelar | Axelarscan registration lookup and GMP-index search; no route/transfer certification (`bridge-status`, `bridge-tx`) | narrow/partial read |
| Arweave storage | Point-in-time base-network cost estimate; never uploads or guarantees retrieval (`arweave-cost`) | narrow live read |
| Token intelligence | Five-query XRPL ledger snapshot; confidence capped at Medium and no recommendation (`token-intel`) | partial live read |
| Attention bridge / social cards | Product framing for "bring eyes to XRPL" / discovery ideas (`references/xrpl-attention-bridge.md`) | ref |
| Agent / skill receipts | Record what an agent did, or how a skill improved (v1→v2), as an unsigned on-chain `NFTokenMint` — provenance, timestamp, public verifiability; no seed, no autonomous signing (`build-nft-mint` + `skills/agent-receipt-flow.md` + `examples/js/agent-receipt-nft.js`) | CLI + pattern |

Both stacks are first-class for the code you write on top — see **Choose your stack** above.

## Quick start

```bash
git clone https://github.com/CarpXRPL/xrpl-hermes.git
cd xrpl-hermes
bash setup.sh
. .venv/bin/activate
xrpl-hermes ledger
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
| [`STANDALONE.md`](STANDALONE.md) | Retirement notice for the former duplicated standalone bundle; use canonical docs instead |
| [`SECURITY.md`](SECURITY.md) · [`LIMITATIONS.md`](LIMITATIONS.md) | Safety model and honest scope |
| [`AUDIT-tool-matrix.md`](AUDIT-tool-matrix.md) | Generated verification matrix — safe commands exercised, side-effect commands explicitly skipped, zero failures |
| [`docs/BUILD-BENCHMARK.md`](docs/BUILD-BENCHMARK.md) | Build-proof benchmark — L1→L3 + adversarial safety tasks proving an agent builds on XRPL safely (complements the tool matrix) |
| [`skills/agent-receipt-flow.md`](skills/agent-receipt-flow.md) · [`references/track-agent-behavior.md`](references/track-agent-behavior.md) | Agent provenance: record a run as an unsigned on-chain receipt, and attribute/monitor behavior (SourceTag · Memos · WebSocket) |

## Command coverage

72 commands are registered across focused Python modules in `scripts/tools/`. The supported agent surface is the MCP allowlist with 67 entries; legacy sensitive registrations are classified and quarantined (see [MCP agent boundary](#mcp-agent-boundary)).

| Ecosystem | Count | Commands |
|---|---:|---|
| XRPL L1 core and ops | 41 | 39 read/build commands (`account` through `subscribe`) plus 2 registered legacy broadcast surfaces that are quarantined and MCP-denied; see `SKILL.md` for the safe catalog |
| Amendment status | 3 | `amendments`, `amendment`, `amendment-status` |
| NFT marketplace | 7 | `nft-info`, `nft-offers`, `build-nft-mint`, `build-nft-create-offer`, `build-nft-accept-offer`, `build-nft-cancel-offer`, `build-nft-burn` |
| AMM liquidity | 6 | `amm-info`, `build-amm-create`, `build-amm-deposit`, `build-amm-withdraw`, `build-amm-vote`, `build-amm-bid` |
| Token intelligence | 1 | `token-intel` |
| EVM Sidechain | 3 | `evm-balance`, `evm-contract`, `evm-bridge` |
| Xahau Hooks | 2 | `hooks-bitmask`, `hooks-info` |
| Flare / price context | 2 | `flare-price`, `flare-ftso` |
| Axelar / Arweave | 3 | `bridge-status`, `bridge-tx`, `arweave-cost` |
| Address/key compatibility | 3 | `validate-address` plus two legacy quarantined key registrations |
| Xaman Platform | 1 | `xaman-payload` |

`build-batch` is security-retired and unregistered; protocol amendment status does not re-enable it. MPT, Credential, and Oracle builders check the live amendment state before emitting JSON.

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
bash setup.sh

# Optional native skill copy (knowledge/instructions)
mkdir -p ~/.hermes/skills/xrpl-hermes
cp -r SKILL.md knowledge references skills ~/.hermes/skills/xrpl-hermes/
```

Activate with:

```bash
hermes -s xrpl-hermes

# Recommended: connect the isolated venv MCP runtime too
hermes mcp add xrpl-hermes --command "$PWD/.venv/bin/xrpl-hermes-mcp"
hermes mcp test xrpl-hermes
```

## MCP server (Claude Code, OpenClaw, Cursor, any MCP client)

`scripts/mcp_server.py` is a dependency-free stdio MCP server exposing four tools: `xrpl_list_commands`, `xrpl_run` (the 67 agent-safe commands), `xrpl_knowledge_index`, and `xrpl_knowledge`.

```bash
# Claude Code, using the installed console entry point
claude mcp add xrpl-hermes -- /path/to/xrpl-hermes/.venv/bin/xrpl-hermes-mcp
```

Generic MCP client config:

```json
{
  "mcpServers": {
    "xrpl-hermes": {
      "command": "/path/to/xrpl-hermes/.venv/bin/xrpl-hermes-mcp"
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
| **Registered local dispatcher** | **72** | Complete compatibility catalog; not every registration is a supported workflow |
| **MCP-safe** — `xrpl_run` / `xrpl_list_commands` | **67** | Read-only live queries and unsigned, signer-ready builders |
| **Denied over MCP** | **5** | two legacy key registrations, two legacy broadcast registrations, and guarded Payment-only `xaman-payload` |

Those five are outside the agent boundary: two legacy registrations touch key material, two
legacy registrations broadcast, and one creates a guarded external Xaman request for a reviewed
XRPL L1 Payment only. Legacy key/broadcast surfaces are quarantined from supported workflows.

- A denied command is refused **before any subprocess is spawned**, so it never executes and no
  MCP response can carry a seed or trigger an external side effect.
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
- Legacy key-management and broadcast registrations are quarantined and denied over MCP.
- Guarded `xaman-payload` is Payment-only, denied over MCP, and never proves signing or settlement.
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
