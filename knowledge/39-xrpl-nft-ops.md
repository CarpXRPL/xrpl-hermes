# NFT operations

This is the operational companion to `knowledge/23-xrpl-nft-minting.md`.

## Read before acting

```bash
xrpl-hermes nft-info NFT_ID
xrpl-hermes nft-offers NFT_ID sell
xrpl-hermes nft-offers NFT_ID buy
```

Use validated ownership and offers as the source of truth. Application listings are caches.

## Offer lifecycle

```bash
# Create a sell offer
xrpl-hermes build-nft-create-offer \
  --from rOWNER --nftoken-id NFT_ID --amount 25000000 --flags 1

# Accept a sell offer
xrpl-hermes build-nft-accept-offer \
  --from rBUYER --sell-offer OFFER_INDEX

# Cancel one or more offers
xrpl-hermes build-nft-cancel-offer \
  --from rOWNER --offers OFFER_INDEX
```

Use destination-locked offers for private sales. Show the decoded NFT ID, owner, amount, currency, destination, expiration, transfer fee, and broker fee before external authorization.

## Brokered sales

A brokered acceptance requires matching buy and sell offer indexes. The broker fee must be denominated consistently with the offers and must not exceed the available spread.

## Burn

```bash
xrpl-hermes build-nft-burn --from rOWNER --nftoken-id NFT_ID
```

Burn is irreversible. Verify ownership and any delegated issuer/owner fields before authorization.

## Batch and auction boundary

XRPL-Hermes does not ship batch minting, auction settlement, marketplace indexing, metadata upload, or a transaction broadcaster. Build individual unsigned intents and keep application-level scheduling, bidding, retries, and wallet authorization outside Hermes.

## Receipt

For every wallet-authorized transaction:

```bash
xrpl-hermes tx-info TX_HASH
```

Require `validated: true`, inspect the engine result, and re-read ownership/offers before updating user-visible state.
