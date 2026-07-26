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
| Arweave | Query the live network/gateway quote for the exact byte size | Permanent | ❌ (has own ID) |
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

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


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

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## 6. Create Sell Offer

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## 7. Accept Sell Offer (Buy)

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


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

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


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

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## 12. Reserve Impact

NFTs are stored in pages of up to 32. Each owned page can add one incremental owner-reserve unit; page split/merge behavior and the unit's XRP value come from current validated network state. The account must have enough spendable XRP under those live values before page creation.

---

## Related Files

- `knowledge/06-xrpl-nfts.md` — NFT model overview
- `knowledge/36-xrpl-xls-standards.md` — XLS-20 spec
- `knowledge/39-xrpl-nft-ops.md` — ops patterns for NFT collections
