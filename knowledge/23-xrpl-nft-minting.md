# XRPL NFT minting

XRPL-Hermes ships two live NFT reads and five unsigned XLS-20 builders.

## Mint

```bash
xrpl-hermes build-nft-mint \
  --from rMINTER \
  --taxon 1001 \
  --uri ipfs://CID/metadata.json \
  --transfer-fee 500 \
  --flags 8
```

- `--uri` encodes UTF-8 text to the ledger’s hex field.
- Use `--uri-hex` only for already encoded bytes.
- Review immutable URI, taxon, transfer fee, issuer, and flags before authorization.

## Read NFT state

```bash
xrpl-hermes nft-info NFT_ID
xrpl-hermes nft-offers NFT_ID sell
xrpl-hermes nft-offers NFT_ID buy
```

## Sell offer

```bash
xrpl-hermes build-nft-create-offer \
  --from rOWNER --nftoken-id NFT_ID --amount 25000000 --flags 1
```

Optional fields include destination and expiration. Amount can be XRP drops or `CODE:ISSUER:VALUE`.

## Accept, cancel, or burn

```bash
xrpl-hermes build-nft-accept-offer \
  --from rBUYER --sell-offer OFFER_INDEX

xrpl-hermes build-nft-cancel-offer \
  --from rOWNER --offers OFFER_INDEX

xrpl-hermes build-nft-burn \
  --from rOWNER --nftoken-id NFT_ID
```

Brokered acceptance can include matching buy/sell offers and a broker fee.

## Verification

1. Read current ownership and offers.
2. Build and inspect unsigned JSON.
3. Authorize in the user-controlled wallet.
4. Verify the hash with `tx-info` and require `validated: true`.
5. Re-read NFT ownership and offers before updating application state.

No batch mint, wallet, signing, marketplace API, metadata upload, or transaction broadcast command is shipped.
