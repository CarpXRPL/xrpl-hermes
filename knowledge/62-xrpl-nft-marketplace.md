# XRPL NFT marketplace flow

XRPL-Hermes ships live NFT/offer reads and unsigned XLS-20 builders.

## Commands

```bash
xrpl-hermes nft-info NFT_ID
xrpl-hermes nft-offers NFT_ID sell
xrpl-hermes nft-offers NFT_ID buy

xrpl-hermes build-nft-mint \
  --from rMINTER --taxon 1001 --uri ipfs://CID/metadata.json \
  --transfer-fee 500 --flags 8

xrpl-hermes build-nft-create-offer \
  --from rOWNER --nftoken-id NFT_ID --amount 25000000 --flags 1

xrpl-hermes build-nft-accept-offer \
  --from rBUYER --sell-offer OFFER_INDEX

xrpl-hermes build-nft-cancel-offer \
  --from rOWNER --offers OFFER_INDEX

xrpl-hermes build-nft-burn \
  --from rOWNER --nftoken-id NFT_ID
```

All builders output unsigned JSON.

## Minting

- `--uri` UTF-8 encodes text to the ledger’s hex field.
- `--uri-hex` accepts an already encoded value; it cannot be combined with `--uri`.
- `--taxon` groups tokens for collection logic.
- `--transfer-fee` is measured in thousandths of one percent.
- Review mint flags and immutable metadata before authorization.

## Offers

- Sell offers normally use flag `1`.
- `--destination` restricts acceptance to one account.
- `--expiration` uses Ripple epoch time.
- Amounts can be drops or `CODE:ISSUER:VALUE`.
- Brokered acceptance requires matching buy/sell offers and a valid broker fee.

## Safe marketplace sequence

1. Read the NFT and current offers from validated ledger state.
2. Build the intended unsigned transaction.
3. Display NFT ID, owner, amount, currency, destination, expiration, and transfer fee.
4. Authorize in the user-controlled wallet.
5. Verify the transaction with `tx-info` and require `validated: true`.
6. Re-read ownership and offers before updating the application cache.

An application database is not ownership proof. Reconcile listings immediately before showing an actionable buy or cancel control.
