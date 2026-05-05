# 62 — XRPL NFT Marketplace Flow

This file covers the complete XLS-20 marketplace lifecycle: mint, create offer, discover offers, accept offer, cancel offer, and burn.
It also covers royalties, transfer fees, taxon grouping, brokered offers, and auction mechanics.

## Mint

```bash
python3 -m scripts.xrpl_tools build-nft-mint --from rMINTER --taxon 1001 --uri ipfs://bafy... --transfer-fee 500 --flags 8
```

The command prints signer-ready JSON. Send that JSON to a wallet, multisig process, or `xaman-payload`.

## Create Sell Offer

```bash
python3 -m scripts.xrpl_tools build-nft-create-offer --from rOWNER --nftoken-id NFT_ID --amount 25000000 --flags 1
```

The command prints signer-ready JSON. Send that JSON to a wallet, multisig process, or `xaman-payload`.

## Discover Offers

```bash
python3 -m scripts.xrpl_tools nft-offers NFT_ID sell
```

The command prints signer-ready JSON. Send that JSON to a wallet, multisig process, or `xaman-payload`.

## Accept Offer

```bash
python3 -m scripts.xrpl_tools build-nft-accept-offer --from rBUYER --sell-offer OFFER_INDEX
```

The command prints signer-ready JSON. Send that JSON to a wallet, multisig process, or `xaman-payload`.

## Cancel Offer

```bash
python3 -m scripts.xrpl_tools build-nft-cancel-offer --from rOWNER --offers OFFER_INDEX
```

The command prints signer-ready JSON. Send that JSON to a wallet, multisig process, or `xaman-payload`.

## Burn

```bash
python3 -m scripts.xrpl_tools build-nft-burn --from rOWNER --nftoken-id NFT_ID
```

The command prints signer-ready JSON. Send that JSON to a wallet, multisig process, or `xaman-payload`.

## End-to-End Testnet Workflow

```bash
OWNER=rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe
BUYER=rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh
python3 -m scripts.xrpl_tools build-nft-mint --from $OWNER --taxon 777 --uri https://example.com/nft/777.json --transfer-fee 500 --flags 8
python3 -m scripts.xrpl_tools build-nft-create-offer --from $OWNER --nftoken-id $NFT_ID --amount 25000000 --flags 1
python3 -m scripts.xrpl_tools nft-offers $NFT_ID sell
python3 -m scripts.xrpl_tools build-nft-accept-offer --from $BUYER --sell-offer $OFFER_INDEX
```

## Royalty Handling

`transfer_fee` is stored on the NFT at mint time. It is measured in thousandths of a percent, so 500 means 0.5 percent and 50000 means 50 percent.

Implementation checklist:

- Validate ownership before showing a sell flow.
- Display amounts in XRP and drops so users can audit the JSON.
- Show the NFT ID, issuer, taxon, URI, and transfer fee before signing.
- Re-query ledger state after every accepted or canceled offer.

## Taxon Grouping

`NFTokenTaxon` groups NFTs for collection logic. Use a stable taxon per collection or per subcollection.

Implementation checklist:

- Validate ownership before showing a sell flow.
- Display amounts in XRP and drops so users can audit the JSON.
- Show the NFT ID, issuer, taxon, URI, and transfer fee before signing.
- Re-query ledger state after every accepted or canceled offer.

## Broker Fees

A broker can accept matching buy and sell offers in one NFTokenAcceptOffer and include `nftoken_broker_fee`.

Implementation checklist:

- Validate ownership before showing a sell flow.
- Display amounts in XRP and drops so users can audit the JSON.
- Show the NFT ID, issuer, taxon, URI, and transfer fee before signing.
- Re-query ledger state after every accepted or canceled offer.

## Auction Mechanics

XRPL NFT auctions are application-level patterns built from offers, expirations, and off-ledger bidding rules.

Implementation checklist:

- Validate ownership before showing a sell flow.
- Display amounts in XRP and drops so users can audit the JSON.
- Show the NFT ID, issuer, taxon, URI, and transfer fee before signing.
- Re-query ledger state after every accepted or canceled offer.

## Offer Expiration

Set expiration for time-boxed offers. Expired offers still need cleanup if your UI wants a tidy order book.

Implementation checklist:

- Validate ownership before showing a sell flow.
- Display amounts in XRP and drops so users can audit the JSON.
- Show the NFT ID, issuer, taxon, URI, and transfer fee before signing.
- Re-query ledger state after every accepted or canceled offer.

## Destination-Locked Offers

Set `Destination` when only one account should be allowed to accept the offer.

Implementation checklist:

- Validate ownership before showing a sell flow.
- Display amounts in XRP and drops so users can audit the JSON.
- Show the NFT ID, issuer, taxon, URI, and transfer fee before signing.
- Re-query ledger state after every accepted or canceled offer.

## Metadata

Store heavy metadata off-ledger and place a URI on-ledger. Arweave and IPFS are common choices.

Implementation checklist:

- Validate ownership before showing a sell flow.
- Display amounts in XRP and drops so users can audit the JSON.
- Show the NFT ID, issuer, taxon, URI, and transfer fee before signing.
- Re-query ledger state after every accepted or canceled offer.

## Custody

Marketplaces can be non-custodial: users sign offer and accept transactions from their own wallets.

Implementation checklist:

- Validate ownership before showing a sell flow.
- Display amounts in XRP and drops so users can audit the JSON.
- Show the NFT ID, issuer, taxon, URI, and transfer fee before signing.
- Re-query ledger state after every accepted or canceled offer.

### Marketplace Production Note 1

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 2

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 3

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 4

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 5

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 6

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 7

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 8

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 9

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 10

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 11

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 12

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 13

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 14

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 15

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 16

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 17

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 18

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 19

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 20

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 21

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 22

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 23

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 24

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 25

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 26

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 27

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 28

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 29

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 30

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 31

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 32

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 33

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 34

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 35

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 36

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 37

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 38

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 39

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 40

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 41

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 42

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 43

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 44

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 45

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 46

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 47

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 48

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 49

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 50

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 51

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 52

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 53

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 54

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 55

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 56

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 57

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 58

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 59

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 60

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 61

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 62

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 63

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 64

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 65

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 66

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 67

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 68

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 69

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 70

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 71

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 72

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 73

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 74

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 75

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 76

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 77

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 78

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 79

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 80

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 81

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 82

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 83

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 84

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 85

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 86

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 87

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 88

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 89

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

### Marketplace Production Note 90

- Treat ledger state as authoritative and your database as a cache.
- Index offers by `NFTokenID`, owner, amount, destination, expiration, and ledger index.
- Reconcile cached listings with `nft-offers` before showing a buy button.

## Related Files

- [06-xrpl-nfts](knowledge/06-xrpl-nfts.md)
- [23-xrpl-nft-minting](knowledge/23-xrpl-nft-minting.md)
- [39-xrpl-nft-ops](knowledge/39-xrpl-nft-ops.md)
