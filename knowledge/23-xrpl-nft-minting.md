# XRPL NFT Minting: Step by Step

## Overview

XRPL supports native NFTs via the NFToken standard (NFTokenV1 amendment). NFTs are stored in NFTokenPage objects, with up to 32 per page. This guide covers metadata hosting, minting, offers, royalties, and batch operations.

---

## 1. Metadata Preparation

NFT metadata is stored off-chain. The URI in the NFT points to the metadata.

### Recommended Metadata Format (OpenSea-compatible)

```json
{
  "name": "My NFT #001",
  "description": "A unique digital asset on the XRPL",
  "image": "ipfs://QmXXX.../image.png",
  "external_url": "https://myproject.com/nft/001",
  "attributes": [
    { "trait_type": "Background", "value": "Blue" },
    { "trait_type": "Rarity", "value": "Rare" },
    { "trait_type": "Power", "value": 85, "max_value": 100 }
  ]
}
```

### Hosting Options

| Platform | Cost | Permanence | IPFS CID |
|----------|------|-----------|----------|
| IPFS + Pinata | Free tier | Until unpinned | ✅ |
| Arweave | One-time fee ~$0.01/kb | Permanent | ❌ (has own ID) |
| NFT.storage | Free | Permanent via Filecoin | ✅ |
| Your server | Free | As long as server runs | ❌ |

```python
# Upload to IPFS via Pinata
import httpx
import json

async def upload_to_ipfs(metadata: dict, pinata_jwt: str) -> str:
    """Returns IPFS CID."""
    headers = {
        "Authorization": f"Bearer {pinata_jwt}",
        "Content-Type": "application/json"
    }
    payload = {
        "pinataContent": metadata,
        "pinataMetadata": {"name": metadata.get("name", "nft_metadata")}
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.pinata.cloud/pinning/pinJSONToIPFS",
            json=payload,
            headers=headers
        )
        resp.raise_for_status()
        ipfs_hash = resp.json()["IpfsHash"]
        return f"ipfs://{ipfs_hash}"
```

---

## 2. NFT Flags

```python
# NFToken flags (bitfield)
TF_BURNABLE        = 0x00000001  # Creator can burn even if owned by someone else
TF_ONLY_XRP        = 0x00000002  # Can only be traded for XRP (no tokens)
TF_TRUSTLINE       = 0x00000004  # Create trust line if needed for royalties
TF_TRANSFERABLE    = 0x00000008  # Can be transferred to 3rd parties
                                  # If NOT set: only creator can transfer

# Common production flags:
TRANSFERABLE_XRP_ONLY = TF_TRANSFERABLE | TF_ONLY_XRP  # 0x0000000A
FULL_FLAGS = TF_BURNABLE | TF_ONLY_XRP | TF_TRANSFERABLE  # 0x0000000B
```

---

## 3. NFTokenMint Transaction

> ⚠️ **URI MUST BE HEX-ENCODED.** The `uri` field in NFTokenMint requires a hex string, not a plain URL.
> `xrpl-py` does **not** auto-encode it. Passing a raw `"ipfs://..."` string will fail or store garbage.
>
> Use `xrpl.utils.str_to_hex("ipfs://...")` or `binascii.hexlify(uri.encode()).decode().upper()`:
> ```python
> from xrpl.utils import str_to_hex
> uri_hex = str_to_hex("ipfs://QmXXX...")  # correct
> # uri = "ipfs://QmXXX..."               # WRONG — do not pass raw string
> ```

```python
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import NFTokenMint
from xrpl.transaction import autofill_and_sign, submit_and_wait
import binascii

client = JsonRpcClient("https://xrplcluster.com")
wallet = Wallet.from_seed("sn...")

TRANSFER_FEE = 5000  # 5% royalty (max 50000 = 50%)
# TransferFee: fee in 1/100000 units → 5000 = 5%

def encode_uri(uri: str) -> str:
    return binascii.hexlify(uri.encode()).decode().upper()

metadata_uri = "ipfs://QmXXXX..."
taxon = 0  # Token collection ID (your choice of integer)

tx = NFTokenMint(
    account=wallet.address,
    nftoken_taxon=taxon,
    flags=0x0000000B,      # Burnable | OnlyXRP | Transferable
    transfer_fee=TRANSFER_FEE,
    uri=encode_uri(metadata_uri),
    fee="12"
)

signed = autofill_and_sign(tx, wallet, client)
result = submit_and_wait(signed, client)

# Extract NFToken ID from metadata
nftoken_id = None
for node in result.result["meta"]["AffectedNodes"]:
    if node.get("ModifiedNode", {}).get("LedgerEntryType") == "NFTokenPage":
        final = node["ModifiedNode"]["FinalFields"]
        prev = node["ModifiedNode"]["PreviousFields"]
        new_tokens = [
            t for t in final.get("NFTokens", [])
            if t not in prev.get("NFTokens", [])
        ]
        if new_tokens:
            nftoken_id = new_tokens[0]["NFToken"]["NFTokenID"]

print(f"Minted NFT ID: {nftoken_id}")
```

---

## 4. NFToken ID Structure

```
NFToken ID = 32 bytes (64 hex chars)

Bytes 0-1:   Flags (uint16)
Bytes 2-3:   TransferFee (uint16)
Bytes 4-23:  Issuer Account ID (20 bytes)
Bytes 24-27: NFTokenTaxon (uint32, scrambled)
Bytes 28-31: Sequence Number (uint32)
```

Parsing an NFToken ID:
```python
def parse_nftoken_id(nft_id: str) -> dict:
    b = bytes.fromhex(nft_id)
    flags = int.from_bytes(b[0:2], 'big')
    transfer_fee = int.from_bytes(b[2:4], 'big')
    issuer_account_id = b[4:24].hex()
    taxon = int.from_bytes(b[24:28], 'big')
    sequence = int.from_bytes(b[28:32], 'big')
    
    return {
        "flags": flags,
        "transfer_fee_pct": transfer_fee / 1000,
        "issuer_account_id": issuer_account_id,
        "taxon": taxon,
        "sequence": sequence,
        "burnable": bool(flags & 0x0001),
        "only_xrp": bool(flags & 0x0002),
        "transferable": bool(flags & 0x0008)
    }
```

---

## 5. Batch Minting

Use tickets for parallel batch minting:

```python
import asyncio
from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.models.transactions import TicketCreate, NFTokenMint
from xrpl.asyncio.transaction import autofill_and_sign, submit_and_wait
from xrpl.models.requests import AccountObjects

async def batch_mint(
    wallet: Wallet,
    metadata_uris: list,
    taxon: int = 0,
    transfer_fee: int = 5000,
    flags: int = 0x0000000B
) -> list:
    client = AsyncJsonRpcClient("https://xrplcluster.com")
    n = len(metadata_uris)
    
    # Create tickets
    ticket_tx = TicketCreate(
        account=wallet.address,
        ticket_count=n,
        fee="12"
    )
    signed = await autofill_and_sign(ticket_tx, wallet, client)
    await submit_and_wait(signed, client)
    
    # Get ticket sequences
    resp = await client.request(AccountObjects(account=wallet.address, type="ticket"))
    ticket_seqs = sorted([t["TicketSequence"] for t in resp.result["account_objects"]])
    
    # Mint all in parallel
    async def mint_one(uri: str, ticket_seq: int) -> str:
        tx = NFTokenMint(
            account=wallet.address,
            nftoken_taxon=taxon,
            flags=flags,
            transfer_fee=transfer_fee,
            uri=encode_uri(uri),
            sequence=0,
            ticket_sequence=ticket_seq,
            fee="12"
        )
        signed = await autofill_and_sign(tx, wallet, client)
        result = await submit_and_wait(signed, client)
        
        # Extract NFToken ID
        for node in result.result["meta"]["AffectedNodes"]:
            modified = node.get("ModifiedNode") or node.get("CreatedNode")
            if modified and modified.get("LedgerEntryType") == "NFTokenPage":
                tokens = (modified.get("FinalFields") or modified.get("NewFields", {})).get("NFTokens", [])
                if tokens:
                    return tokens[-1]["NFToken"]["NFTokenID"]
        return None
    
    tasks = [mint_one(uri, seq) for uri, seq in zip(metadata_uris, ticket_seqs)]
    nft_ids = await asyncio.gather(*tasks)
    
    await client.close()
    return nft_ids

# Usage
uris = [f"ipfs://QmXXX.../metadata/{i}.json" for i in range(10)]
nft_ids = asyncio.run(batch_mint(wallet, uris))
print(f"Minted {len(nft_ids)} NFTs")
```

---

## 6. Create Sell Offer

```python
from xrpl.models.transactions import NFTokenCreateOffer

# Direct sell offer for 10 XRP
tx_offer = NFTokenCreateOffer(
    account=wallet.address,
    nftoken_id=nftoken_id,
    amount="10000000",  # 10 XRP in drops
    flags=0x00000001,  # tfSellNFToken
    destination=None,  # Anyone can buy; set address to restrict
    expiration=None,   # No expiry; set ripple epoch to restrict
    fee="12"
)
signed = autofill_and_sign(tx_offer, wallet, client)
result = submit_and_wait(signed, client)

# Get offer ID from metadata
offer_id = None
for node in result.result["meta"]["AffectedNodes"]:
    if node.get("CreatedNode", {}).get("LedgerEntryType") == "NFTokenOffer":
        offer_id = node["CreatedNode"]["LedgerIndex"]
print(f"Offer ID: {offer_id}")
```

---

## 7. Accept Sell Offer (Buy)

```python
from xrpl.models.transactions import NFTokenAcceptOffer

# Buyer accepts the sell offer
tx_accept = NFTokenAcceptOffer(
    account=buyer_wallet.address,
    nftoken_sell_offer=offer_id,
    fee="12"
)
signed = autofill_and_sign(tx_accept, buyer_wallet, client)
result = submit_and_wait(signed, client)
print(f"NFT purchased: {result.result['meta']['TransactionResult']}")
```

---

## 8. Verify Royalties

Royalties (TransferFee) are paid automatically on every secondary sale. Verify the transfer fee is set correctly:

```python
from xrpl.models.requests import AccountNFTs

resp = client.request(AccountNFTs(account=wallet.address))
for nft in resp.result["account_nfts"]:
    if nft["NFTokenID"] == nftoken_id:
        tf = nft.get("TransferFee", 0)
        print(f"Transfer fee: {tf / 1000:.1f}%")
        # Decode URI
        uri_hex = nft.get("URI", "")
        uri = bytes.fromhex(uri_hex).decode() if uri_hex else None
        print(f"URI: {uri}")
```

---

## 9. Burn NFT

```python
from xrpl.models.transactions import NFTokenBurn

# Creator burns (requires TF_BURNABLE flag or owner burning their own)
tx_burn = NFTokenBurn(
    account=wallet.address,
    nftoken_id=nftoken_id,
    fee="12"
)
signed = autofill_and_sign(tx_burn, wallet, client)
submit_and_wait(signed, client)
```

---

## 10. Query NFTs

```python
# Get all NFTs owned by an account
from xrpl.models.requests import AccountNFTs

resp = client.request(AccountNFTs(
    account=wallet.address,
    limit=400
))
nfts = resp.result["account_nfts"]
print(f"Account owns {len(nfts)} NFTs")

# Get NFT offers
from xrpl.models.requests import NFTSellOffers, NFTBuyOffers

sell_offers = client.request(NFTSellOffers(nft_id=nftoken_id))
buy_offers = client.request(NFTBuyOffers(nft_id=nftoken_id))
```

---

## 11. Minting with a Different Issuer (Authorized Minting)

```python
# Issuer delegates minting rights to a minter account
from xrpl.models.transactions import AccountSet

# Step 1: Issuer authorizes minter
tx_auth = AccountSet(
    account=issuer_wallet.address,
    nftoken_minter=minter_wallet.address,  # set_flag not needed here
    fee="12"
)
signed = autofill_and_sign(tx_auth, issuer_wallet, client)
submit_and_wait(signed, client)

# Step 2: Minter mints on behalf of issuer
tx_mint = NFTokenMint(
    account=minter_wallet.address,
    nftoken_taxon=0,
    issuer=issuer_wallet.address,  # specify issuer
    flags=0x0000000B,
    transfer_fee=5000,
    uri=encode_uri("ipfs://Qm..."),
    fee="12"
)
signed = autofill_and_sign(tx_mint, minter_wallet, client)
submit_and_wait(signed, client)
```

---

## 12. Reserve Impact

NFTs are stored in pages of up to 32:
```
Owner reserve per NFTokenPage = 0.2 XRP

0–32 NFTs:    1 page  = 0.2 XRP reserve
33–64 NFTs:   2 pages = 4 XRP reserve
65–96 NFTs:   3 pages = 6 XRP reserve
...
```

Account must have enough XRP to cover page creation.
