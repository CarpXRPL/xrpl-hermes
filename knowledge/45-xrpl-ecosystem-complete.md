# Complete XRPL Ecosystem Map

## Network Layers

```
┌─────────────────────────────────────────────────────────────┐
│  XRPL Mainnet L1 (XRP Ledger)                               │
│  Consensus: RPCA / UNL voting | ~3-5s finality              │
│  Features: DEX, AMM, NFTs, Escrow, Channels, MPTs, DIDs     │
├──────────────┬──────────────────┬───────────────────────────┤
│ **EVM Sidechain**│  **Xahau Network**   │  **Flare Network**            │
│ (wXRP, EVM)    │  (Hooks, XAH)    │  (FLR, FTSO, EVM)        │
│ Chain: 1440000 │ Fork of XRPL    │  EVM + state connector   │
├──────────────┴──────────────────┴───────────────────────────┤
│  Bridges & Interop                                           │
│  XRPL↔EVM: Federated bridge (~3 min)                        │
│  XRPL↔Flare: State connector (native, ~3 min)               │
│  EVM↔Cosmos/ETH: Axelar GMP (variable)                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Trusted Token Issuers (Mainnet Gateways)

| Gateway | Classic Address | Currencies | Reputation | Notes |
|---------|----------------|------------|------------|-------|
| **Bitstamp** | `rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B` | USD, EUR, GBP, BTC, ETH | 10+ years | Most trusted; used in most DEX pairs |
| **GateHub** | `rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh` | USD, EUR, BTC | 8+ years | Multi-currency; KYC required |
| **GateHub (5th)** | `rB9zqP39p8uVr4VqKcTRvPtsaRxzPjrXh4` | USD, EUR | Established | Backup gateway; same KYC |
| **Sologenic** | `rsoLo2S1kiGeCcn6hCUXVrCpGMWLrRrLZz` | SOLO, tokenized stocks | 3+ years | First tokenized-assets DEX |
| **Stably** | `rMH4UxPrbuMa1spCBR98hLLyNJp4d8p4tM` | USDS (stablecoin) | 2+ years | US-regulated stablecoin |

### Verifying Gateway Trust

```python
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountInfo, AccountLines, GatewayBalances

client = JsonRpcClient("https://xrplcluster.com")

def gateway_summary(gateway_address: str) -> dict:
    """Return obligations and assets for a gateway issuer."""
    resp = client.request(GatewayBalances(
        account=gateway_address,
        ledger_index="validated",
        hotwallet=[],  # Add hot wallets if known
    ))
    return {
        "obligations": resp.result.get("obligations", {}),  # Tokens issued
        "assets": resp.result.get("assets", {}),            # Tokens held
        "account_id": gateway_address,
    }

bitstamp = gateway_summary("rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B")
print(f"Bitstamp obligations: {bitstamp['obligations']}")
# {'USD': '12345678.90', 'EUR': '5432100.00', ...}
```

---

## DEX & AMM Ecosystem

### Orderbook DEX (Native XRPL)

The XRPL has the world's oldest on-chain DEX (since 2012). All tokens can trade against each other via the orderbook.

```python
from xrpl.models.requests import BookOffers

def get_orderbook_depth(client, base_currency, base_issuer, quote="XRP", depth=10):
    """Get best N offers on both sides of a trading pair."""
    base = {"currency": base_currency, "issuer": base_issuer}
    quote_spec = {"currency": "XRP"} if quote == "XRP" else {"currency": quote}

    bids = client.request(BookOffers(
        taker_pays=base,
        taker_gets=quote_spec,
        limit=depth,
        ledger_index="validated",
    )).result.get("offers", [])

    asks = client.request(BookOffers(
        taker_pays=quote_spec,
        taker_gets=base,
        limit=depth,
        ledger_index="validated",
    )).result.get("offers", [])

    return {"bids": bids, "asks": asks}
```

### AMM Pools (XLS-30)

AMM pools exist alongside the DEX. XRPL pathfinding uses both simultaneously for best execution.

```python
from xrpl.models.requests import AMMInfo

def list_amm_pools(client, assets: list[tuple]) -> list[dict]:
    """Query multiple AMM pools."""
    pools = []
    for asset1, asset2 in assets:
        try:
            resp = client.request(AMMInfo(asset=asset1, asset2=asset2))
            amm = resp.result.get("amm", {})
            pools.append({
                "asset1": asset1,
                "asset2": asset2,
                "xrp_depth": int(amm.get("amount", "0")) / 1e6 if isinstance(amm.get("amount"), str) else 0,
                "trading_fee_bps": amm.get("trading_fee", 0),
                "lp_token": amm.get("lp_token", {}).get("value"),
            })
        except Exception:
            pass
    return pools

# Check major pools
POOLS_TO_TRACK = [
    ({"currency": "XRP"}, {"currency": "USD", "issuer": "rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B"}),
    ({"currency": "XRP"}, {"currency": "EUR", "issuer": "rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B"}),
    ({"currency": "XRP"}, {"currency": "SOLO", "issuer": "rsoLo2S1kiGeCcn6hCUXVrCpGMWLrRrLZz"}),
]
```

---

## Wallets Compatibility Matrix

| Wallet | L1 | EVM | Xahau | Hooks | AMM | NFTs | Hardware |
|--------|----|----|-------|-------|-----|------|----------|
| **Xaman (XUMM)** | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ Tangem |
| **Crossmark** | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ |
| **Joey** | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **MetaMask** | ❌ | ✅ | ❌ | ❌ | ❌ | ERC-1155 | ✅ Ledger |
| **GemWallet** | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ |
| **Privy** | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ |
| **Trust Wallet** | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |

### Wallet Integration via XUMM SDK

```javascript
import { Xumm } from "xumm";

const xumm = new Xumm("your-api-key");

// Sign a payment request
const request = await xumm.payload.create({
  txjson: {
    TransactionType: "Payment",
    Destination: "rRecipient...",
    Amount: "1000000",  // 1 XRP in drops
  },
  options: {
    submit: true,
    multisign: false,
  },
});

console.log("QR:", request.refs.qr_png);   // Show QR to user
console.log("Deep link:", request.next.always);

// Wait for signing
const result = await request.resolved;
console.log("Signed:", result.txid);
```

### Crossmark SDK

```javascript
import sdk from "@crossmarkio/sdk";

// Connect
await sdk.connect();

// Sign and submit
const { response } = await sdk.signAndSubmitAndWait({
  TransactionType: "Payment",
  Account: sdk.session.address,
  Destination: "rRecipient...",
  Amount: "1000000",
});
console.log(response.data.meta.isSuccess);
```

---

## Explorers & API Services

### Block Explorers

| Explorer | URL | Strengths |
|----------|-----|-----------|
| XRPSCAN | `xrpscan.com` | Most data-rich: amendments, validators, rich charts |
| Bithomp | `bithomp.com` | Good for account history, username lookup |
| XRPl.org | `livenet.xrpl.org` | Official Ripple explorer |
| XRPview | `xrpview.info` | Simple, clean interface |
| XRPL-EVM Explorer | `evm-sidechain.xrpl.org` | EVM sidechain block explorer |

### Data APIs

```python
import requests

# XRPSCAN — free tier available
def xrpscan_account_info(address: str) -> dict:
    return requests.get(f"https://api.xrpscan.com/api/v1/account/{address}").json()

def xrpscan_nfts(address: str) -> list:
    return requests.get(f"https://api.xrpscan.com/api/v1/account/{address}/nfts").json()

def xrpscan_transactions(address: str, marker: str = None) -> dict:
    url = f"https://api.xrpscan.com/api/v1/account/{address}/transactions"
    if marker:
        url += f"?marker={marker}"
    return requests.get(url).json()

# XRPL.to — market data
def xrplio_price(currency: str, issuer: str) -> dict:
    return requests.get(
        f"https://data.xrpl.to/api/v1/token/{currency}.{issuer}/price"
    ).json()

# OnTheDex — DEX analytics
def onthedex_pair(base_currency: str, base_issuer: str) -> dict:
    return requests.get(
        f"https://api.onthedex.live/public/v1/pair/XRP/{base_currency}.{base_issuer}"
    ).json()
```

---

## Node Infrastructure

### Public Nodes (No Auth Required)

| Node | JSON-RPC URL | WebSocket URL | Notes |
|------|-------------|---------------|-------|
| XRPLCluster | `https://xrplcluster.com` | `wss://xrplcluster.com` | Load-balanced cluster |
| Ripple s1 | `https://s1.ripple.com:51234` | `wss://s1.ripple.com:51233` | Full history |
| Ripple s2 | `https://s2.ripple.com:51234` | `wss://s2.ripple.com:51233` | Full history |
| XRPL.ws | `https://xrpl.ws` | `wss://xrpl.ws` | Community node |
| **Testnet** | `https://testnet.xrpl-labs.com` | `wss://testnet.xrpl-labs.com` | Development |
| **Devnet** | `https://s.devnet.rippletest.net:51234` | — | Feature testing |

### Self-Hosted Node Stack

```yaml
# docker-compose.yml for rippled + Clio
version: '3.8'
services:
  rippled:
    image: xrpllabsofficial/xrpld:latest
    ports:
      - "51235:51235"  # Peer protocol
      - "5005:5005"    # JSON-RPC (admin)
    volumes:
      - ./config/rippled.cfg:/etc/opt/ripple/rippled.cfg
      - rippled-data:/var/lib/rippled
    restart: unless-stopped

  clio:
    image: ghcr.io/xrplf/clio:latest
    ports:
      - "51234:51234"  # JSON-RPC (public)
      - "51233:51233"  # WebSocket
    depends_on:
      - rippled
      - postgres
    environment:
      - CLIO_CONFIG=/etc/clio/config.json

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: clio
      POSTGRES_USER: clio
      POSTGRES_PASSWORD_FILE: /run/secrets/pg_password
    volumes:
      - postgres-data:/var/lib/postgresql/data

volumes:
  rippled-data:
  postgres-data:
```

---

## NFT Marketplace Ecosystem

| Platform | Type | Chain | Notes |
|----------|------|-------|-------|
| **XRP NFT** | Aggregator | L1 | Lists NFTs from all XRPL collections |
| **onXRP** | Marketplace | L1 | Largest volume; launchpad + secondary |
| **Sologenic NFT** | Marketplace | L1 | SOLO ecosystem NFTs |
| **NFT Master** | Marketplace | L1 | Creator-focused |
| **xSPECTAR** | 3D Metaverse | L1 | VR assets as NFTs |
| **Equilibrium** | Marketplace | L1 | Community-run |

### Indexing NFT Collections

```python
from xrpl.models.requests import AccountNFTs

def index_collection(client, issuer: str, taxon: int) -> list[dict]:
    """Get all NFTs in a collection (issuer + taxon combination)."""
    all_nfts = []
    marker = None

    while True:
        params = {
            "account": issuer,
            "limit": 400,
        }
        if marker:
            params["marker"] = marker

        resp = client.request(AccountNFTs(**params))
        for nft in resp.result.get("account_nfts", []):
            if nft.get("nft_taxon") == taxon:
                all_nfts.append({
                    "id": nft["NFTokenID"],
                    "uri": bytes.fromhex(nft.get("URI", "")).decode("utf-8", errors="replace"),
                    "taxon": nft["nft_taxon"],
                    "sequence": nft["nft_serial"],
                    "transfer_fee": nft.get("transfer_fee", 0),
                    "flags": nft.get("flags", 0),
                })

        marker = resp.result.get("marker")
        if not marker:
            break

    return all_nfts
```

---

## DeFi Protocol Map

### L1 DeFi (Native XRPL)

| Protocol | TVL Tier | Type | Key Feature |
|----------|----------|------|-------------|
| **XRPL AMM** | High | Native AMM | Constant product, on-chain |
| **XRPL DEX** | Highest | Orderbook | World's oldest on-chain DEX |
| **Sologenic DEX** | Medium | Token DEX | Tokenized stocks + crypto |
| **XRP Casino** | Low | Gaming | NFT-based gaming |

### EVM DeFi (Sidechain)

| Protocol | Type | Status |
|----------|------|--------|
| **xBridge liquidity** | AMM | Live |
| **Uniswap V2 forks** | AMM | Deployed |
| **Lending protocols** | Lend/borrow | Early stage |

---

## Compliance & Regulatory Tools

### Travel Rule Solutions

| Tool | Purpose | VASP Integration |
|------|---------|-----------------|
| **Notabene** | Travel rule messages | REST API |
| **Sygna Bridge** | VASP-to-VASP comms | SDK |
| **Veriscope** | Open-source TR protocol | Self-hosted |
| **CipherTrace** | AML monitoring (Mastercard) | Enterprise |

```python
# XRPL travel rule integration pattern
# Sender VASP attaches beneficiary info to tx memo before sending

import json, base64
from xrpl.models.transactions import Payment

def payment_with_travel_rule(
    sender_wallet,
    destination: str,
    amount_drops: int,
    beneficiary_info: dict,
) -> Payment:
    """
    Embed travel rule data in transaction memo (encrypted in production).
    Format: TRISA-compliant JSON, base64-encoded.
    """
    tr_data = {
        "originator": {"name": "Alice Smith", "account_number": sender_wallet.classic_address},
        "beneficiary": beneficiary_info,
    }
    memo_data = base64.b64encode(json.dumps(tr_data).encode()).hex().upper()

    return Payment(
        account=sender_wallet.classic_address,
        destination=destination,
        amount=str(amount_drops),
        memos=[{
            "Memo": {
                "MemoData": memo_data,
                "MemoType": "5452415645525552554C45",  # "TRAVELRULE"
                "MemoFormat": "6170706C69636174696F6E2F6A736F6E",  # "application/json"
            }
        }],
    )
```

---

## Regulatory Landscape

| Jurisdiction | XRP Status | Token Issuance | VASP Rules |
|-------------|-----------|----------------|------------|
| **USA** | Not a security (2023 Ripple ruling) | SEC oversight varies by token | FinCEN MSB registration |
| **EU** | Crypto-asset (MiCA applies) | MiCA Art. 17 whitepaper required | AMLD5/6 compliance |
| **Singapore** | Digital payment token | MAS PSA license for exchanges | MAS Travel Rule mandatory |
| **Japan** | Crypto asset | FSA registration | FATF Travel Rule |
| **Dubai (VARA)** | Virtual asset | VARA license tiers | Tailored DLT framework |
| **UK** | Cryptoasset | FCA registration required | Crypto Travel Rule (Jan 2024) |
| **Switzerland** | DLT token | FINMA guidance | AMLA compliance |

---

## Open Source Projects

### Core Infrastructure

| Project | Language | Purpose | Repo |
|---------|----------|---------|------|
| rippled | C++ | Core XRPL node | XRPLF/rippled |
| Clio | C++ | History API server | XRPLF/clio |
| xrpld-hooks | C++ | Hooks-enabled rippled fork | XRPL-Labs/xrpld-hooks |
| Ripple Data API | JavaScript | Historical data aggregator | ripple/ripple-data-api |

### SDKs

| SDK | Language | Maturity | Repo |
|-----|----------|---------|------|
| xrpl-py | Python | Stable | XRPLF/xrpl-py |
| xrpl.js | JavaScript | Stable | XRPLF/xrpl.js |
| xrpl4j | Java | Stable | XRPLF/xrpl4j |
| xrpl-dev-portal | Docs | Reference | XRPLF/xrpl-dev-portal |
| XUMM SDK | JS/TS | Stable | XRPL-Labs/xumm-sdk |
| Crossmark SDK | JS | Beta | crossmarkio/sdk |

### Tools & Bots

| Tool | Purpose |
|------|---------|
| XRPL Drip Engine | Token distribution + airdrop tool |
| XRPL Watcher | Balance monitoring alerts |
| XRPL Arbitrage Bot | DEX/AMM spread arbitrage |
| NFT.Storage on XRPL | IPFS pinning for NFT metadata |

---

## Grant Programs & Funding

| Program | Size | Focus | Apply |
|---------|------|-------|-------|
| XRPL Grants (XRPL Foundation) | $5K–$250K | Infrastructure, DeFi, tools | xrplgrants.org |
| Ripple Impact | $250K–$1M | Social impact, CBDCs | ripple.com/impact |
| XRPL EVM Ecosystem Fund | $1M+ pool | EVM ecosystem development | EVM bridge team |
| Xahau Grants | $10K–$100K | Hooks ecosystem | Xahau Foundation |

---

## Complete Routing Guide

```
L1 → EVM Sidechain:    Federated bridge, ~3–5 min, 0.01 XRP fee
L1 → Xahau:            XAH bridge, ~3 min
L1 → Flare:            State connector, native, ~3 min
L1 → Songbird:         State connector (Flare canary), ~3 min
EVM → Ethereum/BSC:    Axelar GMP or LayerZero, ~5–30 min
EVM → Cosmos:          Axelar IBC bridge
EVM → Arweave:         ArDrive / Bundlr (storage only)
L1 → Arweave:          Off-chain: data on Arweave, hash in Memo field
```

### Route Cost Comparison

| Route | Fee | Time | Trust Model |
|-------|-----|------|------------|
| L1 → EVM | ~0.01 XRP + EVM gas | 3–5 min | Federated (N-of-M) |
| L1 → Flare | ~0.01 XRP | 3 min | State connector proofs |
| EVM → ETH (Axelar) | $5–20 gas | 15–30 min | Proof-of-stake validators |
| L1 DEX trade | 0.00001 XRP | Instant (in ledger) | Trustless on-chain |
| L1 AMM swap | 0.00001 XRP + 0.1–1% fee | Instant | Trustless on-chain |

---

## Developer Quick Reference

```bash
# Useful public endpoints
XRPL_MAINNET_RPC="https://xrplcluster.com"
XRPL_MAINNET_WS="wss://xrplcluster.com"
XRPL_TESTNET_RPC="https://testnet.xrpl-labs.com"
XRPL_EVM_RPC="https://rpc.xrplevm.org"
XAHAU_RPC="https://xahau.network"

# Faucets
TESTNET_FAUCET="https://faucet.altnet.rippletest.net/accounts"
DEVNET_FAUCET="https://faucet.devnet.rippletest.net/accounts"
XAHAU_FAUCET="https://xahau-test.net/faucet"
EVM_FAUCET="https://bridge.devnet.xrpl.org"
```

```python
# Get testnet wallet with funds
from xrpl.clients import JsonRpcClient
from xrpl.wallet import generate_faucet_wallet

testnet = JsonRpcClient("https://testnet.xrpl-labs.com")
test_wallet = generate_faucet_wallet(testnet, debug=True)
print(f"Test address: {test_wallet.classic_address}")
print(f"Test seed: {test_wallet.seed}")
```

---

## Related Files
- `references/xrpl-l1.md` — L1 fundamentals
- `references/xrpl-evm-sidechain.md` — EVM sidechain architecture
- `references/xahau-hooks.md` — Xahau and Hooks
- `references/flare-ftso.md` — Flare FTSO price feeds
- `references/axelar-bridge.md` — Axelar cross-chain messaging
- `references/arweave-storage.md` — Arweave permanent storage
- `knowledge/36-xrpl-xls-standards.md` — XLS standard specifications
- `knowledge/37-xrpl-amendments.md` — amendment catalog
