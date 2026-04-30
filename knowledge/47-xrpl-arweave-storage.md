# Arweave Permanent Storage — XRPL Integration

## Overview

Arweave is a decentralized permanent data storage network built on a novel "blockweave" structure. Unlike traditional cloud storage or IPFS (which requires pinning), data stored on Arweave is stored **once, forever**, funded by a single upfront fee. This makes it ideal for storing XRPL NFT metadata, legal documents, compliance records, and dApp frontends that must remain accessible indefinitely.

**Key properties:**
- Permanent: data cannot be deleted after upload
- Decentralized: no single point of failure
- Content-addressed: data accessed by transaction ID hash
- Single payment: one fee covers perpetual storage
- Permaweb: full web hosting with static sites and apps

**Native token:** AR (used for storage fees and mining rewards)

---

## Architecture

### Blockweave vs Blockchain

```
Standard Blockchain:        Arweave Blockweave:
Block N ← Block N-1        Block N ← Block N-1
                               ↕ Recall Block (random prev)
```

Each new block must include data from a random previous block (Proof of Access). Miners must store historical data to mine new blocks — incentivizing full archival storage across the network.

### Storage Endowment Model

```
User pays fee → Endowment fund
                    ↓
         Fee invested conservatively
         Returns fund ongoing storage
         indefinitely into the future
```

The storage fee is calculated to fund ongoing replication as storage costs decline over time. Arweave's economic model assumes storage costs drop ~30% per year, so the endowment generates enough returns to cover all future storage.

### Data Access Flow

```
Upload: Client → Arweave node → broadcast → miners replicate
Access: User → Gateway (arweave.net) → fetch from miners → serve
```

Gateways (arweave.net, g8way.io) serve as HTTP interfaces to Arweave data. Data is accessed via transaction ID:
```
https://arweave.net/{transaction_id}
```

---

## Bundlr Network (irys.xyz)

Bundlr (now rebranding to Irys) is an Arweave scaling layer that:
1. Accepts many small uploads and bundles them into a single Arweave transaction
2. Accepts multiple payment tokens (ETH, SOL, MATIC, AR, AVAX)
3. Provides fast optimistic confirmations (< 8 seconds)
4. Significantly cheaper for many small uploads

```
Client → Bundlr node → bundle many uploads → single Arweave tx
```

---

## Python: Upload Data to Arweave

### Basic Upload with arweave-python-client

```python
import arweave
from arweave.arweave_lib import Wallet, Transaction

def upload_to_arweave(
    wallet_jwk_path: str,
    data: bytes,
    content_type: str = "application/json",
    tags: dict = None
) -> str:
    """
    Upload data to Arweave. Returns transaction ID.
    Requires AR tokens in the wallet for fees.
    """
    wallet = Wallet(wallet_jwk_path)

    transaction = Transaction(wallet, data=data)
    transaction.add_tag("Content-Type", content_type)

    if tags:
        for key, value in tags.items():
            transaction.add_tag(key, value)

    transaction.sign()
    transaction.send()

    tx_id = transaction.id
    print(f"Uploaded to Arweave: https://arweave.net/{tx_id}")
    return tx_id

# Upload XRPL NFT metadata
metadata = {
    "name": "My XRPL NFT",
    "description": "An NFT on the XRP Ledger",
    "image": "https://arweave.net/some_image_tx_id",
    "attributes": [
        {"trait_type": "Rarity", "value": "Rare"},
        {"trait_type": "Series", "value": "Genesis"}
    ]
}

import json
tx_id = upload_to_arweave(
    wallet_jwk_path="./arweave-wallet.json",
    data=json.dumps(metadata).encode(),
    content_type="application/json",
    tags={
        "App-Name": "XRPL-NFT-Metadata",
        "NFT-Standard": "XLS-20",
        "XRPL-Network": "mainnet"
    }
)
arweave_uri = f"https://arweave.net/{tx_id}"
```

### Upload via Bundlr (Irys) with ETH/SOL/MATIC Payment

```python
# pip install irys-sdk or bundlr-sdk (check latest npm/pip packages)
# Most use the JS SDK; Python wraps via httpx to the Bundlr node

import httpx
import json
import base64

BUNDLR_NODE = "https://node1.bundlr.network"

async def upload_via_bundlr_node(
    data: bytes,
    content_type: str,
    tags: dict
) -> str:
    """
    Upload to Bundlr node. In production use the official SDK for signing.
    This shows the HTTP layer.
    """
    headers = {
        "Content-Type": content_type,
        "x-tag-App-Name": tags.get("App-Name", "XRPL-App")
    }
    async with httpx.AsyncClient() as client:
        # Check price first
        price_resp = await client.get(
            f"{BUNDLR_NODE}/price/arweave/{len(data)}"
        )
        price_winston = price_resp.json()  # price in Winston (1e-12 AR)
        print(f"Upload cost: {price_winston / 1e12:.8f} AR")

        # Upload (requires signed bundle in production)
        # Full signing requires JS SDK or py-bundlr
        response = await client.post(
            f"{BUNDLR_NODE}/tx/arweave",
            content=data,
            headers=headers
        )
        return response.json()["id"]
```

---

## Python: Read and Verify Arweave Data

```python
import httpx
import json

ARWEAVE_GATEWAY = "https://arweave.net"

async def fetch_arweave_data(tx_id: str) -> bytes:
    """Fetch raw data from Arweave by transaction ID."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{ARWEAVE_GATEWAY}/{tx_id}")
        response.raise_for_status()
        return response.content

async def fetch_arweave_tx_metadata(tx_id: str) -> dict:
    """Fetch transaction metadata (tags, owner, data_size) without fetching data."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ARWEAVE_GATEWAY}/graphql",
            json={
                "query": """
                query GetTx($id: ID!) {
                  transaction(id: $id) {
                    id
                    owner { address }
                    data { size type }
                    block { height timestamp }
                    tags { name value }
                  }
                }
                """,
                "variables": {"id": tx_id}
            }
        )
        return response.json()["data"]["transaction"]

async def query_nft_metadata_uploads(xrpl_issuer: str, limit: int = 20) -> list:
    """
    Query Arweave GraphQL for all NFT metadata uploads tagged with an XRPL issuer.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ARWEAVE_GATEWAY}/graphql",
            json={
                "query": """
                query GetNFTUploads($issuer: String!, $limit: Int!) {
                  transactions(
                    first: $limit
                    tags: [
                      { name: "App-Name", values: ["XRPL-NFT-Metadata"] }
                      { name: "XRPL-Issuer", values: [$issuer] }
                    ]
                  ) {
                    edges {
                      node {
                        id
                        block { height timestamp }
                        tags { name value }
                      }
                    }
                  }
                }
                """,
                "variables": {"issuer": xrpl_issuer, "limit": limit}
            }
        )
        edges = response.json()["data"]["transactions"]["edges"]
        return [edge["node"] for edge in edges]

# Fetch NFT metadata from Arweave URI stored in XLS-20 NFT
async def resolve_nft_metadata(arweave_uri: str) -> dict:
    """
    Resolve NFT metadata from an Arweave URI.
    URI format: https://arweave.net/{tx_id}
    """
    tx_id = arweave_uri.split("/")[-1]
    data = await fetch_arweave_data(tx_id)
    return json.loads(data)
```

---

## JSON: Arweave Transaction Structure

```json
{
  "format": 2,
  "id": "abc123def456ghi789",
  "last_tx": "previous_block_hash",
  "owner": "RSA_public_key_base64url",
  "tags": [
    {
      "name": "Content-Type",
      "value": "application/json"
    },
    {
      "name": "App-Name",
      "value": "XRPL-NFT-Metadata"
    },
    {
      "name": "NFT-Standard",
      "value": "XLS-20"
    },
    {
      "name": "XRPL-Token-ID",
      "value": "000800004B9A9E67..."
    },
    {
      "name": "XRPL-Issuer",
      "value": "rIssuerXRPLAddress"
    }
  ],
  "target": "",
  "quantity": "0",
  "data_root": "merkle_root_of_data",
  "data_size": "1024",
  "reward": "114950000",
  "signature": "RSA_signature"
}
```

---

## Arweave GraphQL API

The Arweave network exposes a GraphQL endpoint at `https://arweave.net/graphql` for querying transactions by tags, owner, block height, etc.

```python
async def search_arweave_by_tags(tags: dict, limit: int = 10) -> list:
    """Generic Arweave GraphQL tag search."""
    tag_filter = [{"name": k, "values": [v]} for k, v in tags.items()]

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://arweave.net/graphql",
            json={
                "query": """
                query Search($tags: [TagFilter!]!, $limit: Int!) {
                  transactions(first: $limit, tags: $tags) {
                    edges {
                      node {
                        id
                        owner { address }
                        data { size type }
                        block { height timestamp }
                        tags { name value }
                      }
                    }
                  }
                }
                """,
                "variables": {"tags": tag_filter, "limit": limit}
            }
        )
        return [e["node"] for e in response.json()["data"]["transactions"]["edges"]]

# Find all data anchored for a specific XRPL transaction hash
results = asyncio.run(search_arweave_by_tags({
    "App-Name": "XRPL-Anchor",
    "XRPL-TX-Hash": "your_xrpl_tx_hash"
}))
```

---

## API Endpoints and Usage

| Endpoint | Method | Description |
|----------|--------|-------------|
| `https://arweave.net/{tx_id}` | GET | Fetch data by transaction ID |
| `https://arweave.net/tx/{tx_id}` | GET | Transaction metadata |
| `https://arweave.net/tx/{tx_id}/status` | GET | Confirmation status |
| `https://arweave.net/price/{bytes}` | GET | Cost to upload N bytes (in Winston) |
| `https://arweave.net/graphql` | POST | GraphQL query interface |
| `https://arweave.net/info` | GET | Network info |

```python
async def get_upload_price(data_size_bytes: int) -> dict:
    """Get the cost to store data on Arweave."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://arweave.net/price/{data_size_bytes}"
        )
        winston = int(response.text)
        return {
            "winston": winston,
            "ar": winston / 1e12,
            "bytes": data_size_bytes
        }

async def get_tx_status(tx_id: str) -> dict:
    """Check if an Arweave transaction is confirmed."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://arweave.net/tx/{tx_id}/status"
        )
        if response.status_code == 200:
            data = response.json()
            return {
                "confirmed": True,
                "block_height": data.get("block_height"),
                "block_indep_hash": data.get("block_indep_hash"),
                "number_of_confirmations": data.get("number_of_confirmations")
            }
        elif response.status_code == 202:
            return {"confirmed": False, "status": "pending"}
        else:
            return {"confirmed": False, "status": "not_found"}
```

---

## XRPL NFT Metadata Storage Workflow

The canonical workflow for storing XLS-20 NFT metadata on Arweave:

```python
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import NFTokenMint
from xrpl.wallet import Wallet
from xrpl.transaction import submit_and_wait
import json
import asyncio

async def mint_nft_with_arweave_metadata(
    wallet: Wallet,
    metadata: dict,
    royalty_percent: float = 5.0,
    is_transferable: bool = True
) -> dict:
    """
    Full workflow: upload metadata to Arweave, then mint XLS-20 NFT with URI.
    """
    # 1. Upload metadata to Arweave
    print("Uploading metadata to Arweave...")
    arweave_tx_id = upload_to_arweave(
        wallet_jwk_path="./arweave-wallet.json",
        data=json.dumps(metadata).encode(),
        content_type="application/json",
        tags={
            "App-Name": "XRPL-NFT-Metadata",
            "NFT-Standard": "XLS-20"
        }
    )
    metadata_uri = f"https://arweave.net/{arweave_tx_id}"
    print(f"Metadata URI: {metadata_uri}")

    # 2. Wait for Arweave confirmation (usually 10-30 min for finality)
    # For production, wait for confirmation before minting
    # For testing, proceed immediately

    # 3. Mint XLS-20 NFT with Arweave URI
    client = JsonRpcClient("https://s1.ripple.com:51234")

    transfer_fee = int(royalty_percent * 1000)  # 5% = 5000 in 1/1000 units
    flags = 8 if is_transferable else 0  # 8 = transferable

    # Encode URI as hex
    uri_hex = metadata_uri.encode().hex().upper()

    mint_tx = NFTokenMint(
        account=wallet.classic_address,
        nftoken_taxon=0,
        transfer_fee=transfer_fee,
        flags=flags,
        uri=uri_hex
    )

    result = submit_and_wait(mint_tx, client, wallet)
    nft_id = None

    # Extract the NFT token ID from the transaction metadata
    for affected in result.result.get("meta", {}).get("AffectedNodes", []):
        created = affected.get("CreatedNode", {})
        if created.get("LedgerEntryType") == "NFTokenPage":
            nfts = created.get("NewFields", {}).get("NFTokens", [])
            if nfts:
                nft_id = nfts[-1]["NFToken"]["NFTokenID"]

    return {
        "nft_id": nft_id,
        "arweave_tx": arweave_tx_id,
        "metadata_uri": metadata_uri,
        "xrpl_tx_hash": result.result["hash"],
        "status": result.result["meta"]["TransactionResult"]
    }
```

---

## XRPL Transaction Anchoring on Arweave

Store XRPL transaction hashes on Arweave for permanent audit trails:

```python
async def anchor_xrpl_tx_on_arweave(
    xrpl_tx_hash: str,
    xrpl_network: str = "mainnet",
    arweave_wallet_path: str = "./arweave-wallet.json"
) -> dict:
    """
    Permanently anchor an XRPL transaction hash on Arweave.
    Useful for compliance, legal records, audit trails.
    """
    # Fetch the full XRPL tx for anchoring
    async with httpx.AsyncClient() as client:
        tx_response = await client.post(
            "https://s1.ripple.com:51234",
            json={
                "method": "tx",
                "params": [{"transaction": xrpl_tx_hash}]
            }
        )
        xrpl_tx = tx_response.json()["result"]

    anchor_data = {
        "xrpl_tx_hash": xrpl_tx_hash,
        "xrpl_network": xrpl_network,
        "ledger_index": xrpl_tx.get("ledger_index"),
        "timestamp": xrpl_tx.get("date"),
        "transaction_type": xrpl_tx.get("TransactionType"),
        "full_tx": xrpl_tx,
        "anchored_at_iso": "2026-04-29T00:00:00Z"
    }

    arweave_tx_id = upload_to_arweave(
        wallet_jwk_path=arweave_wallet_path,
        data=json.dumps(anchor_data).encode(),
        content_type="application/json",
        tags={
            "App-Name": "XRPL-Anchor",
            "XRPL-TX-Hash": xrpl_tx_hash,
            "XRPL-Network": xrpl_network,
            "Anchor-Type": "transaction"
        }
    )

    return {
        "arweave_tx_id": arweave_tx_id,
        "permanent_url": f"https://arweave.net/{arweave_tx_id}",
        "xrpl_tx_hash": xrpl_tx_hash
    }
```

---

## Error Handling Patterns

```python
import asyncio
from typing import Optional

class ArweaveStorageError(Exception):
    pass

class ArweaveUploadError(ArweaveStorageError):
    pass

class ArweaveNotFoundError(ArweaveStorageError):
    pass

async def safe_fetch_arweave(tx_id: str, retries: int = 3) -> Optional[bytes]:
    """Fetch Arweave data with retry on network errors."""
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"https://arweave.net/{tx_id}")

                if response.status_code == 404:
                    raise ArweaveNotFoundError(f"TX {tx_id} not found")
                if response.status_code == 202:
                    # Data pending confirmation — wait and retry
                    await asyncio.sleep(30 * (attempt + 1))
                    continue

                response.raise_for_status()
                return response.content

        except httpx.TimeoutException:
            if attempt < retries - 1:
                await asyncio.sleep(5 * (attempt + 1))
            else:
                raise ArweaveStorageError(f"Timeout fetching {tx_id} after {retries} retries")

    return None

def validate_arweave_tx_id(tx_id: str) -> bool:
    """Arweave TX IDs are 43-character base64url strings."""
    import re
    return bool(re.match(r'^[a-zA-Z0-9_-]{43}$', tx_id))

async def wait_for_arweave_confirmation(
    tx_id: str,
    required_confirmations: int = 25,
    timeout_minutes: int = 60
) -> bool:
    """Wait for an Arweave transaction to reach required confirmations."""
    import time
    deadline = time.time() + timeout_minutes * 60

    while time.time() < deadline:
        status = await get_tx_status(tx_id)
        if status.get("confirmed"):
            confs = status.get("number_of_confirmations", 0)
            print(f"Confirmations: {confs}/{required_confirmations}")
            if confs >= required_confirmations:
                return True
        await asyncio.sleep(60)

    return False
```

---

## Permaweb App Hosting for XRPL dApps

Arweave can host static XRPL dApp frontends permanently:

```bash
# Install arkb CLI for deploying web apps
npm install -g arkb

# Deploy static site to Arweave
arkb deploy ./dist --wallet arweave-wallet.json

# Result: permanent URL like https://arweave.net/{tx_id}
# Can also set up ArNS domain: https://your-domain.arweave.dev
```

```python
async def get_arns_domain_info(domain: str) -> dict:
    """Query ArNS (Arweave Name System) for a domain."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://arweave.net/ar-io/v1/ario/domains/{domain}"
        )
        if response.status_code == 200:
            return response.json()
        return {"error": "domain not found"}
```

---

## Cost Calculator

```python
async def estimate_xrpl_nft_collection_storage(
    num_nfts: int,
    metadata_size_bytes: int = 1000,
    image_size_bytes: int = 500_000  # 500KB per image
) -> dict:
    """Estimate Arweave storage cost for an NFT collection."""
    total_metadata_bytes = num_nfts * metadata_size_bytes
    total_image_bytes = num_nfts * image_size_bytes
    total_bytes = total_metadata_bytes + total_image_bytes

    # Get current price (Winston = 1e-12 AR)
    async with httpx.AsyncClient() as client:
        # Price for 1 byte, then scale
        price_resp = await client.get(f"https://arweave.net/price/{total_bytes}")
        total_winston = int(price_resp.text)

    # Rough AR/USD estimate (check current price)
    ar_price_usd = 15.0  # update with live price

    return {
        "num_nfts": num_nfts,
        "total_bytes": total_bytes,
        "total_ar": total_winston / 1e12,
        "estimated_usd": (total_winston / 1e12) * ar_price_usd,
        "cost_per_nft_ar": (total_winston / 1e12) / num_nfts,
        "note": "One-time fee for permanent storage"
    }
```

---

## Resources

- Arweave network: https://arweave.org
- Primary gateway: https://arweave.net
- Arweave GraphQL: https://arweave.net/graphql
- ViewBlock explorer: https://viewblock.io/arweave
- Bundlr/Irys: https://irys.xyz
- Evernode (XRPL hosting): https://evernode.io
- Python arweave library: https://github.com/MikeHibbert/arweave-python-client
- ArNS name system: https://ar.io

---

## Cross-References

- `54-xrpl-evernode-hosting.md` — Evernode decentralized hosting on XRPL using Arweave
- `52-xrpl-l1-reference.md` — XLS-20 NFT minting reference
- `51-xrpl-xahau-hooks.md` — Hooks can trigger Arweave uploads for audit trails
- `53-xrpl-wallets-auth.md` — Signing transactions to trigger uploads
