# Token operations

This page covers ongoing operations after an issued-currency or MPT launch. Initial issuance is documented in `knowledge/22-xrpl-token-issuance.md`.

## Inventory and holder evidence

```bash
xrpl-hermes account rISSUER
xrpl-hermes trustlines rISSUER TOKEN
xrpl-hermes account-tx rISSUER 25
xrpl-hermes token-intel TOKEN rISSUER
```

`trustlines` returns the visible ledger relationships for the queried account. It is not a complete off-ledger ownership, identity, or legal registry.

## Distribution

Build one unsigned Payment per recipient:

```bash
xrpl-hermes build-payment \
  --from rDISTRIBUTOR --to rHOLDER \
  --amount 100 --cur TOKEN --iss rISSUER
```

Before creating a distribution batch outside Hermes:

- pin the validated ledger used for eligibility;
- use decimal arithmetic, not floats;
- verify every recipient trust line;
- deduplicate destination/tag combinations;
- cap total and per-recipient amounts;
- preserve one receipt per wallet-authorized transaction.

XRPL-Hermes does not ship an airdrop executor or batch broadcaster.

## Liquidity

```bash
xrpl-hermes build-offer \
  --from rDISTRIBUTOR --sell TOKEN:rISSUER:100 --buy XRP:1000000

xrpl-hermes build-amm-deposit \
  --from rDISTRIBUTOR \
  --asset1 XRP --asset2 TOKEN:rISSUER \
  --amount1 1000000 --amount2 TOKEN:rISSUER:100
```

Read current pool and order-book state immediately before authorization:

```bash
xrpl-hermes amm-info XRP TOKEN:rISSUER
xrpl-hermes book-offers XRP TOKEN:rISSUER
```

## Freeze and clawback

```bash
xrpl-hermes build-clawback \
  --from rISSUER --destination rHOLDER \
  --currency TOKEN --amount 10
```

The issuer must have configured the required policy before the trust line existed. Individual trust-line freeze operations are not exposed by the current builder surface.

## Verification

Require `validated: true` from `tx-info`, then re-read balances, trust lines, pool state, and offers. Never treat a submitted hash or external wallet callback as finality.
