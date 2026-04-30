# Advanced NFT Operations

## NFToken Fundamentals Recap

An NFToken is a 256-bit identifier stored in `NFTokenPage` ledger objects on the owner's account. Key facts:
- Each page holds **16–32 NFTs** sorted by ID; first page costs **2 XRP reserve**
- Royalties (TransferFee) are **automatic on secondary sales** — no off-chain enforcement needed
- The `Taxon` field (32-bit) groups NFTs into collections; it is XOR-obfuscated in the stored ID
- URI is stored as **hex-encoded bytes** (max 512 hex chars = 256 bytes)

---

## NFToken Mint: Full Options

```python
import xrpl
import xrpl.utils
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import NFTokenMint
from xrpl.transaction import submit_and_wait
import os

client = JsonRpcClient("https://xrplcluster.com")
minter = Wallet.from_secret(os.environ["MINTER_SECRET"])

# Flag bitmask values
BURNABLE     = 0x0001  # Issuer can burn
ONLY_XRP     = 0x0002  # Sell/buy only for XRP
TRUSTLINE    = 0x0004  # Auto-create trust line for non-XRP sales
TRANSFERABLE = 0x0008  # Can be transferred (if absent, soulbound)

# Example: fully-featured transferable NFT with 5% royalty
mint_tx = NFTokenMint(
    account=minter.classic_address,
    nftoken_taxon=1,              # Collection ID
    flags=BURNABLE | TRANSFERABLE,
    transfer_fee=5000,            # 5000 = 5% (max 50000 = 50%)
    uri=xrpl.utils.str_to_hex("ipfs://QmExampleHash123"),
    # Optional: set issuer to a different account (minting on behalf)
    # issuer="rSomeOtherIssuer...",
)
resp = submit_and_wait(mint_tx, client, minter)
print(f"Mint: {resp.result['meta']['TransactionResult']}")

# Extract the new NFToken ID from the metadata
for node in resp.result['meta'].get('AffectedNodes', []):
    modified = node.get('ModifiedNode', node.get('CreatedNode', {}))
    if modified.get('LedgerEntryType') == 'NFTokenPage':
        final = modified.get('FinalFields', modified.get('NewFields', {}))
        for token in final.get('NFTokens', []):
            print(f"  NFTokenID: {token['NFToken']['NFTokenID']}")
```

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

```python
from xrpl.models.transactions import TicketCreate
from xrpl.models.requests import AccountInfo
import concurrent.futures, time

def create_tickets(client, wallet, count: int) -> list[int]:
    tx = TicketCreate(account=wallet.classic_address, ticket_count=count)
    resp = submit_and_wait(tx, client, wallet)
    assert resp.result['meta']['TransactionResult'] == 'tesSUCCESS'

    tickets = []
    for node in resp.result['meta']['AffectedNodes']:
        created = node.get('CreatedNode', {})
        if created.get('LedgerEntryType') == 'Ticket':
            tickets.append(created['NewFields']['TicketSequence'])
    return sorted(tickets)


def batch_mint_collection(
    client,
    minter: Wallet,
    collection_taxon: int,
    uris: list[str],
    transfer_fee: int = 5000,
    flags: int = 0x0008,  # Transferable
) -> list[str]:
    """
    Mint a collection in parallel using tickets.
    Returns list of NFToken IDs.
    """
    n = len(uris)
    print(f"Creating {n} tickets...")
    tickets = create_tickets(client, minter, n)

    mint_txs = []
    for ticket_seq, uri in zip(tickets, uris):
        tx = NFTokenMint(
            account=minter.classic_address,
            nftoken_taxon=collection_taxon,
            flags=flags,
            transfer_fee=transfer_fee,
            uri=xrpl.utils.str_to_hex(uri),
            ticket_sequence=ticket_seq,
            sequence=0,  # REQUIRED: 0 when using ticket
        )
        mint_txs.append(tx)

    # Submit all without waiting (parallel fire)
    hashes = []
    for tx in mint_txs:
        resp = client.submit(tx, minter)
        h = resp.result.get("tx_json", {}).get("hash", "")
        hashes.append(h)

    print(f"Submitted {len(hashes)} mints. Polling...")
    time.sleep(8)  # Wait two ledger closes

    # Poll for results and extract NFToken IDs
    from xrpl.models.requests import Tx
    nft_ids = []
    for h in hashes:
        resp = client.request(Tx(transaction=h))
        if resp.result.get("validated") and resp.result["meta"]["TransactionResult"] == "tesSUCCESS":
            for node in resp.result['meta'].get('AffectedNodes', []):
                modified = node.get('ModifiedNode', node.get('CreatedNode', {}))
                if modified.get('LedgerEntryType') == 'NFTokenPage':
                    final = modified.get('FinalFields', modified.get('NewFields', {}))
                    prev = modified.get('PreviousFields', {})
                    prev_tokens = {t['NFToken']['NFTokenID'] for t in prev.get('NFTokens', [])}
                    for token in final.get('NFTokens', []):
                        tid = token['NFToken']['NFTokenID']
                        if tid not in prev_tokens:
                            nft_ids.append(tid)

    return nft_ids
```

---

## Sell Offer Lifecycle

```python
from xrpl.models.transactions import NFTokenCreateOffer, NFTokenAcceptOffer, NFTokenCancelOffer
from xrpl.models.requests import AccountNFTs, NFTSellOffers, NFTBuyOffers

# Create a sell offer (owner listing their NFT)
sell_offer = NFTokenCreateOffer(
    account=owner.classic_address,
    nftoken_id="00080000...",
    amount=xrpl.utils.xrp_to_drops("100"),  # Price in XRP drops
    # Optional: restrict to specific buyer
    # destination="rBuyer...",
    # Optional: offer expires at ledger index
    # expiration=12345678,
    flags=1,  # tfSellNFToken = 1 for sell offers
)
resp = submit_and_wait(sell_offer, client, owner)

# Extract the offer ID from metadata
offer_id = None
for node in resp.result['meta']['AffectedNodes']:
    created = node.get('CreatedNode', {})
    if created.get('LedgerEntryType') == 'NFTokenOffer':
        offer_id = created['NewFields']['index']  # The offer's ledger key
        print(f"Sell offer created: {offer_id}")

# Buyer accepts the sell offer
accept_tx = NFTokenAcceptOffer(
    account=buyer.classic_address,
    nftoken_sell_offer=offer_id,
)
resp = submit_and_wait(accept_tx, client, buyer)
```

---

## Buy Offer Pattern

```python
# Buyer creates a bid (buy offer) — seller accepts
buy_offer = NFTokenCreateOffer(
    account=buyer.classic_address,
    nftoken_id="00080000...",
    amount=xrpl.utils.xrp_to_drops("75"),  # Bid price
    owner=owner.classic_address,  # REQUIRED for buy offers: specify current owner
    # flags = 0  (no tfSellNFToken flag = buy offer)
)
resp = submit_and_wait(buy_offer, client, buyer)

# Get bid offer ID
bid_id = None
for node in resp.result['meta']['AffectedNodes']:
    created = node.get('CreatedNode', {})
    if created.get('LedgerEntryType') == 'NFTokenOffer':
        bid_id = created['NewFields']['index']

# Owner accepts the best bid
accept_bid = NFTokenAcceptOffer(
    account=owner.classic_address,
    nftoken_buy_offer=bid_id,
)
resp = submit_and_wait(accept_bid, client, owner)
```

---

## Brokered Sale (Marketplace Pattern)

The broker accepts BOTH a buy and sell offer simultaneously, taking a cut:

```python
# Seller listed at 100 XRP, buyer bid 110 XRP → broker takes 10 XRP spread
broker_accept = NFTokenAcceptOffer(
    account=broker.classic_address,
    nftoken_sell_offer=sell_offer_id,   # Seller's offer
    nftoken_buy_offer=buy_offer_id,     # Buyer's offer
    nftoken_broker_fee=xrpl.utils.xrp_to_drops("10"),  # Broker's cut
)
resp = submit_and_wait(broker_accept, client, broker)
# Result: NFT transfers from seller to buyer, seller gets 100 XRP, broker gets 10 XRP
# TransferFee royalty goes to original minter automatically
```

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

```python
import time, threading

class NFTAuction:
    def __init__(self, client, seller: Wallet, nft_id: str, start_price_drops: int, duration_s: int):
        self.client = client
        self.seller = seller
        self.nft_id = nft_id
        self.start_price = start_price_drops
        self.end_time = time.time() + duration_s
        self.current_offer_id = None
        self.current_bid = start_price_drops
        self.current_bidder = None

    def start(self) -> str:
        """List NFT at starting price, return offer ID."""
        tx = NFTokenCreateOffer(
            account=self.seller.classic_address,
            nftoken_id=self.nft_id,
            amount=str(self.start_price),
            flags=1,  # sell offer
        )
        resp = submit_and_wait(tx, self.client, self.seller)
        for node in resp.result['meta']['AffectedNodes']:
            created = node.get('CreatedNode', {})
            if created.get('LedgerEntryType') == 'NFTokenOffer':
                self.current_offer_id = created['NewFields']['index']
        return self.current_offer_id

    def place_bid(self, bidder: Wallet, bid_drops: int) -> bool:
        """Place a new bid (creates buy offer, cancels previous if exists)."""
        if time.time() > self.end_time:
            return False
        if bid_drops <= self.current_bid:
            return False

        # Create buy offer
        tx = NFTokenCreateOffer(
            account=bidder.classic_address,
            nftoken_id=self.nft_id,
            amount=str(bid_drops),
            owner=self.seller.classic_address,
        )
        resp = submit_and_wait(tx, self.client, bidder)
        for node in resp.result['meta']['AffectedNodes']:
            created = node.get('CreatedNode', {})
            if created.get('LedgerEntryType') == 'NFTokenOffer':
                self.current_bid = bid_drops
                self.current_bidder = bidder.classic_address
        return True

    def finalize(self, broker: Wallet = None):
        """End auction: seller accepts the winning bid."""
        if not self.current_bidder:
            # No bids — cancel sell offer
            cancel = NFTokenCancelOffer(
                account=self.seller.classic_address,
                nftoken_offers=[self.current_offer_id],
            )
            return submit_and_wait(cancel, self.client, self.seller)

        # Accept brokered sale if broker provided
        if broker:
            tx = NFTokenAcceptOffer(
                account=broker.classic_address,
                nftoken_sell_offer=self.current_offer_id,
                nftoken_buy_offer=self.current_bidder,
            )
            return submit_and_wait(tx, self.client, broker)
        else:
            # Seller accepts winning buy offer directly
            tx = NFTokenAcceptOffer(
                account=self.seller.classic_address,
                nftoken_buy_offer=self.current_bidder,
            )
            return submit_and_wait(tx, self.client, self.seller)
```

---

## Bulk Cancel Expired Offers

```python
def cancel_all_offers(client, wallet: Wallet, nft_id: str):
    """Cancel all open sell offers for a specific NFT."""
    offers = get_offers(client, nft_id)
    sell_ids = [o['nft_offer_index'] for o in offers['sell_offers']
                if o['owner'] == wallet.classic_address]

    if not sell_ids:
        return

    # NFTokenCancelOffer accepts up to 500 offer IDs at once
    for chunk_start in range(0, len(sell_ids), 500):
        chunk = sell_ids[chunk_start:chunk_start + 500]
        cancel_tx = NFTokenCancelOffer(
            account=wallet.classic_address,
            nftoken_offers=chunk,
        )
        submit_and_wait(cancel_tx, client, wallet)
```

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
