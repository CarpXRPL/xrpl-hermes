# XRPL NFTs (XLS-20)

## Overview

The XLS-20 amendment introduced native Non-Fungible Tokens (NFTs) to the XRP Ledger. Unlike issued currencies on trust lines, NFTs are unique tokens with their own ledger entries (NFToken objects). Each NFT can have metadata, transfer fees, and various flags controlling its behavior. NFTs are stored in "pages" on the account, with each page holding up to 32 NFTs.

## NFToken

An NFToken is the core object representing a single NFT on the ledger. It is stored within an NFTokenPage, which in turn is owned by the issuing account (or the current holder).

### NFToken Fields

| Field | Type | Description |
|---|---|---|
| `NFTokenID` | Hash256 | Unique identifier for the NFT (derived from issuer, taxon, sequence) |
| `URI` | Blob | Optional metadata URI (max 256 bytes) |
| `Flags` | UInt32 | Token-level flags |
| `Issuer` | AccountID | The account that minted the NFT |
| `NFTokenTaxon` | UInt32 | Taxon identifier for grouping NFTs into collections |
| `TransferFee` | UInt16 | Fee paid to issuer on secondary sales (in 1/1000 units, max 500 = 50%) |

### NFTokenID Derivation

The NFTokenID is a 256-bit hash composed of:
- Bits 0-15: Flags
- Bits 16-47: TransferFee
- Bits 48-79: Reserved
- Bits 80-111: NFTokenTaxon (sequence number)
- Bits 112-143: NFTokenSequence
- Bits 144-255: AccountID (issuer)

## NFTokenMint Transaction

Mints (creates) a new NFT.

### Fields

| Field | Required | JSON Type | Description |
|---|---|---|---|
| `NFTokenTaxon` | ✅ | UInt32 | Taxon for grouping (0-4294967295) |
| `Issuer` | ❌ | String | If minting on behalf of another account |
| `TransferFee` | ❌ | UInt16 | Secondary sale royalty (0-50000, but max recommended 5000 = 5%) |
| `URI` | ❌ | String | Metadata URI (hex-encoded, max 256 bytes) |
| `Flags` | ❌ | UInt32 | Token flags |

### NFT Flags

| Flag | Hex | Decimal | Description |
|---|---|---|---|
| `tfBurnable` | 0x0001 | 1 | The issuer can burn the NFT even after it's sold |
| `tfOnlyXRP` | 0x0002 | 2 | NFT can only be bought/sold for XRP (not tokens) |
| `tfTrustLine` | 0x0004 | 4 | Requires a trust line for the token used to buy/sell |
| `tfTransferable` | 0x0008 | 8 | NFT can be transferred to other holders |

### Example: Mint NFT

```json
{
  "TransactionType": "NFTokenMint",
  "Account": "rIssuerAddress",
  "NFTokenTaxon": 0,
  "TransferFee": 250,  // 2.5% royalty
  "URI": "697066733A2F2F...",  // hex-encoded IPFS URI
  "Flags": 9,  // tfBurnable (1) + tfTransferable (8)
  "Fee": "10",
  "Sequence": 10
}
```

### Python Example

```python
from xrpl.transaction import submit_and_wait
from xrpl.models.transactions import NFTokenMint

mint_tx = NFTokenMint(
    account="rIssuerAddress",
    nftoken_taxon=0,
    transfer_fee=250,
    uri="697066733A2F2F626166796265696764...",
    flags=1,  # tfBurnable
)
response = submit_and_wait(mint_tx, client, wallet)
```

### Minting for Another Account

```json
{
  "TransactionType": "NFTokenMint",
  "Account": "rAuthorizedIssuer",
  "Issuer": "rActualIssuer",
  "NFTokenTaxon": 0,
  "URI": "697066733A2F2F...",
  "Flags": 8  // tfTransferable
}
```

## NFTokenCreateOffer Transaction

Creates a buy or sell offer for an NFT.

### Fields

| Field | Required | JSON Type | Description |
|---|---|---|---|
| `NFTokenID` | ✅ | String | The NFT to create an offer for |
| `Amount` | ✅ | String or Object | Price (XRP or token) |
| `Owner` | ❌ | String | Owner of the NFT (required for buy offers) |
| `Expiration` | ❌ | UInt32 | Ledger sequence when offer expires |
| `Destination` | ❌ | String | Only this account can accept the offer |
| `Flags` | ❌ | UInt32 | Offer flags |

### Sell Offer

```json
{
  "TransactionType": "NFTokenCreateOffer",
  "Account": "rOwnerAddress",
  "NFTokenID": "000B013A95F42B...",
  "Amount": "10000000",  // 10 XRP
  "Expiration": 80000000,
  "Flags": 0
}
```

### Buy Offer

```json
{
  "TransactionType": "NFTokenCreateOffer",
  "Account": "rBuyerAddress",
  "NFTokenID": "000B013A95F42B...",
  "Amount": {
    "currency": "USD",
    "issuer": "rIssuerAddress",
    "value": "100"
  },
  "Owner": "rOwnerAddress",
  "Flags": 0
}
```

The `Owner` field identifies who holds the NFT you're making an offer on.

### Offer Flags

| Flag | Hex | Decimal | Description |
|---|---|---|---|
| `tfSellNFToken` | 0x0001 | 1 | This is a sell offer (default = buy offer) |

## NFTokenAcceptOffer Transaction

Accepts an existing buy or sell offer to transfer ownership of an NFT.

### Fields

| Field | Required | JSON Type | Description |
|---|---|---|---|
| `NFTokenSellOffer` | ❌ | String | Index of the sell offer to accept |
| `NFTokenBuyOffer` | ❌ | String | Index of the buy offer to accept |
| `NFTokenBrokerFee` | ❌ | String or Object | Fee for broker matching |

### Accepting a Sell Offer (Buying)

```json
{
  "TransactionType": "NFTokenAcceptOffer",
  "Account": "rBuyerAddress",
  "NFTokenSellOffer": "ABCDEF0123456789..."
}
```

### Accepting a Buy Offer (Selling)

```json
{
  "TransactionType": "NFTokenAcceptOffer",
  "Account": "rSellerAddress",
  "NFTokenBuyOffer": "ABCDEF0123456789..."
}
```

### Broker-Mediated Trade

```json
{
  "TransactionType": "NFTokenAcceptOffer",
  "Account": "rBrokerAddress",
  "NFTokenSellOffer": "ABCDEF0123456789...",
  "NFTokenBuyOffer": "FEDCBA9876543210...",
  "NFTokenBrokerFee": "1000000"  // 1 XRP broker fee
}
```

## NFTokenBurn Transaction

Destroys an NFT. Can only be done by the holder or the issuer (if `tfBurnable` is set).

```json
{
  "TransactionType": "NFTokenBurn",
  "Account": "rHolderAddress",
  "NFTokenID": "000B013A95F42B..."
}
```

## NFTokenCancelOffer Transaction

Cancels an offer that hasn't been accepted yet.

```json
{
  "TransactionType": "NFTokenCancelOffer",
  "Account": "rOfferCreator",
  "NFTokenOffers": [
    "ABCDEF0123456789...",
    "FEDCBA9876543210..."
  ]
}
```

## NFTokenPage

NFTokens are stored in NFTokenPage objects on the ledger. Each page can hold up to 32 NFTs. The page structure is optimized for efficient storage and management.

### Page Structure

```
NFTokenPage
├── Flags
├── PreviousPage (link to previous page)
├── NextPage (link to next page)
└── NFTokens[] (up to 32 NFToken objects)
```

### Reserve Cost

Each NFTokenPage consumes 1 owner reserve unit (0.2 XRP). So:
- 1-32 NFTs = 1 page = 0.2 XRP reserve
- 33-64 NFTs = 2 pages = 4 XRP reserve
- Etc.

The issuer pays the reserve for the first page (when minting), but subsequent holders pay the reserve if they hold NFTs in their own pages.

## Querying NFTs

### account_nfts RPC

```json
{
  "method": "account_nfts",
  "params": [{
    "account": "r9cZA1mLK5R5Am25ArfXFmqgN1sV5f3gQR"
  }]
}
```

Response:

```json
{
  "result": {
    "account": "r9cZA1mLK5R5Am25ArfXFmqgN1sV5f3gQR",
    "account_nfts": [
      {
        "Flags": 9,
        "Issuer": "rIssuerAddress",
        "NFTokenID": "000B013A95F42B...",
        "NFTokenTaxon": 0,
        "URI": "697066733A2F2F...",
        "nft_serial": 1
      }
    ],
    "ledger_current_index": 12345678,
    "validated": true
  }
}
```

### nft_info RPC (Clio/some servers)

```json
{
  "method": "nft_info",
  "params": [{
    "nft_id": "000B013A95F42B..."
  }]
}
```

### Checking Offers on an NFT

Use `account_objects` with `type: "nft_offer"`:

```json
{
  "method": "account_objects",
  "params": [{
    "account": "rOfferCreator",
    "type": "nft_offer"
  }]
}
```

## Royalties

The `TransferFee` field enforces royalties on secondary sales. When an NFT with `TransferFee` > 0 is sold:

1. Buyer pays the full price
2. TransferFee percentage is automatically sent to the original issuer
3. Seller receives the remaining amount

### Royalty Calculation

```
TransferFee = 250 (means 2.50%)
Sale Price = 10,000 XRP
Royalty = 10,000 * 0.025 = 250 XRP (sent to issuer)
Seller Receives = 9,750 XRP
```

### Important Notes

- Royalties are enforced at the protocol level during `NFTokenAcceptOffer`
- Max TransferFee is 50000 (50%)
- Common values: 250 (2.5%), 500 (5%), 1000 (10%), 5000 (50%)

## Taxon and Collections

The `NFTokenTaxon` field groups NFTs into collections. All NFTs with the same taxon from the same issuer form a collection.

### Best Practices

- Use `NFTokenTaxon = 0` for a single collection
- Use incrementing taxa (1, 2, 3...) for multiple collections from the same issuer
- Taxon is combined with the issuer address to uniquely identify a collection
- Tools like XRPSCAN use taxon to display collections

## Buying and Selling Flow

### Complete Purchase Flow

1. **Seller**: Creates a sell offer with `NFTokenCreateOffer` and `tfSellNFToken`
2. **Buyer**: Finds the offer via `account_objects` or index
3. **Buyer**: Accepts with `NFTokenAcceptOffer`
4. **Protocol**: Transfers NFT, enforces royalties, settles payment

### Complete Bid Flow

1. **Buyer**: Creates a buy offer with `NFTokenCreateOffer` (no tfSellNFToken)
2. **Seller**: Finds the offer
3. **Seller**: Accepts with `NFTokenAcceptOffer`
4. **Protocol**: Transfers NFT, enforces royalties, settles payment

## NFT Marketplaces

Popular XRPL NFT marketplaces that you can interact with programmatically:
- **xrp.cafe**: Largest marketplace, supports all XLS-20 features
- **Onnix**: NFT marketplace
- **xrplbids.com**: Auction-based NFT trading
- **Mynth**: NFT + token marketplace

All are built on the same XLS-20 protocol and can be interacted with directly via the base layer transactions described above.

---

## Related Files

- `knowledge/23-xrpl-nft-minting.md` — minting workflows and metadata
- `knowledge/36-xrpl-xls-standards.md` — XLS-20 NFT spec
- `knowledge/39-xrpl-nft-ops.md` — operational NFT patterns
