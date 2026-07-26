# Advanced NFT Operations

## NFToken Fundamentals Recap

An NFToken is a 256-bit identifier stored in `NFTokenPage` ledger objects on the owner's account. Key facts:
- Each page holds **16–32 NFTs** sorted by ID; owned pages use the network's live incremental reserve
- Royalties (TransferFee) are **automatic on secondary sales** — no off-chain enforcement needed
- The `Taxon` field (32-bit) groups NFTs into collections; it is XOR-obfuscated in the stored ID
- URI is stored as **hex-encoded bytes** (max 512 hex chars = 256 bytes)

---

## NFToken Mint: Full Options

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## Parsing an NFToken ID

```python
def decode_nft_id(nft_id_hex: str) -> dict:
    """
    Fully decode an NFToken ID into human-readable fields.
    NFToken ID structure (256 bits = 32 bytes):
      Bytes  0-1  : Flags (16 bits)
      Bytes  2-3  : TransferFee (16 bits, 0-50000)
      Bytes  4-23 : Issuer account ID (20 bytes / 160 bits)
      Bytes 24-27 : Scrambled taxon (32 bits)
      Bytes 28-31 : Sequence (32 bits)
    """
    from xrpl.core.keypairs.crypto_implementation import get_module
    import xrpl.core.keypairs as kp

    raw = bytes.fromhex(nft_id_hex)
    assert len(raw) == 32, "NFToken ID must be 32 bytes"

    flags = int.from_bytes(raw[0:2], 'big')
    transfer_fee = int.from_bytes(raw[2:4], 'big')
    issuer_id = raw[4:24]
    scrambled_taxon = int.from_bytes(raw[24:28], 'big')
    sequence = int.from_bytes(raw[28:32], 'big')

    # XOR de-obfuscation (XRPL scrambles taxon with sequence)
    CIPHERED_TAXON_MASK = 0x96963E6F
    taxon = scrambled_taxon ^ (CIPHERED_TAXON_MASK * sequence & 0xFFFFFFFF)

    # Decode issuer address
    issuer = kp.encode_classic_address(issuer_id)

    return {
        "flags": {
            "burnable": bool(flags & 0x0001),
            "only_xrp": bool(flags & 0x0002),
            "trustline": bool(flags & 0x0004),
            "transferable": bool(flags & 0x0008),
        },
        "transfer_fee_pct": transfer_fee / 1000.0,
        "issuer": issuer,
        "taxon": taxon,
        "sequence": sequence,
    }

# Example
info = decode_nft_id("00080000B5F762798A53D543A014CAF8B297CFF8F2F937E800000001")
print(info)
# {'flags': {'burnable': False, 'only_xrp': False, 'trustline': False, 'transferable': True},
#  'transfer_fee_pct': 0.0, 'issuer': 'rHb9CJAWy...', 'taxon': 0, 'sequence': 1}
```

---

## Batch Minting with Tickets

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## Sell Offer Lifecycle

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## Buy Offer Pattern

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## Brokered Sale (Marketplace Pattern)

The broker accepts BOTH a buy and sell offer simultaneously, taking a cut:

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## Listing All NFTs for an Account

```python
from xrpl.models.requests import AccountNFTs

def get_all_nfts(client, account: str, taxon: int | None = None) -> list[dict]:
    """Paginate through all NFTs for an account, optionally filtered by taxon."""
    all_nfts = []
    marker = None

    while True:
        req_params = {"account": account, "limit": 400}
        if marker:
            req_params["marker"] = marker
        if taxon is not None:
            # Clio-specific: taxon filtering via nft_info or nfts_by_issuer
            req_params["nftoken_taxon"] = taxon

        resp = client.request(AccountNFTs(**{k: v for k, v in req_params.items() if k in AccountNFTs.__fields__}))
        nfts = resp.result.get("account_nfts", [])
        all_nfts.extend(nfts)

        marker = resp.result.get("marker")
        if not marker:
            break

    return all_nfts


# Example: get all NFTs from a collection (taxon=1)
nfts = get_all_nfts(client, "rMinter...", taxon=1)
for nft in nfts:
    info = decode_nft_id(nft['NFTokenID'])
    print(f"  {nft['NFTokenID']} — {nft.get('URI', 'no uri')}")
```

---

## Querying Open Offers for an NFT

```python
from xrpl.models.requests import NFTSellOffers, NFTBuyOffers

def get_offers(client, nft_id: str) -> dict:
    sell_resp = client.request(NFTSellOffers(nft_id=nft_id))
    buy_resp = client.request(NFTBuyOffers(nft_id=nft_id))
    return {
        "sell_offers": sell_resp.result.get("offers", []),
        "buy_offers": buy_resp.result.get("offers", []),
    }

offers = get_offers(client, "00080000...")
for o in offers["sell_offers"]:
    print(f"  Sell: {int(o['amount']) / 1e6:.2f} XRP from {o['owner']}")
for o in offers["buy_offers"]:
    print(f"  Buy:  {int(o['amount']) / 1e6:.2f} XRP from {o['owner']}")
```

---

## Auction Implementation

XRPL doesn't have native auction logic — implement off-chain with on-chain primitives:

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## Bulk Cancel Expired Offers

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## NFT Metadata Standards

The `URI` field should point to a JSON metadata file following the standard:

```json
{
  "name": "My NFT #1",
  "description": "A unique collectible on XRPL",
  "image": "ipfs://QmImageHash...",
  "animation_url": "ipfs://QmAnimationHash...",
  "external_url": "https://myproject.com/nft/1",
  "attributes": [
    {"trait_type": "Background", "value": "Cosmic Blue"},
    {"trait_type": "Rarity", "value": "Legendary"},
    {"trait_type": "Score", "value": 95, "display_type": "number"}
  ],
  "xrpl": {
    "taxon": 1,
    "sequence": 1,
    "transfer_fee": 5000
  }
}
```

IPFS upload and pin with Pinata or NFT.Storage before minting. Store the `ipfs://QmHash...` as the URI.

---

## Royalty Verification

```python
def verify_royalty(nft_id: str) -> dict:
    """Decode royalty info directly from the NFToken ID."""
    info = decode_nft_id(nft_id)
    return {
        "royalty_pct": info["transfer_fee_pct"],
        "royalty_basis_points": int(info["transfer_fee_pct"] * 1000),
        "issuer": info["issuer"],
        "is_enforced_on_chain": True,  # Always true for XRPL NFTs with transfer_fee
    }

# XRPL royalties are unique: they are enforced at the ledger level,
# not by smart contract. The TransferFee in the NFToken ID is immutable
# and cannot be changed after minting.
```

---

## Related Files
- `knowledge/06-xrpl-nfts.md` — NFT fundamentals
- `knowledge/13-xrpl-tickets.md` — ticket sequence mechanics
- `knowledge/23-xrpl-nft-minting.md` — minting guide
- `knowledge/38-xrpl-minting-ops.md` — IOU/MPT minting operations
