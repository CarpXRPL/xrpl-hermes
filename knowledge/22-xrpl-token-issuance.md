# XRPL token issuance

XRPL-Hermes builds unsigned transactions for a signer-separated issuer workflow.

## Account model

Use separate accounts:

- **Issuer:** creates the currency and holds policy flags.
- **Distributor:** holds issued supply, manages liquidity, and sends operational payments.

Keep the issuer offline except for reviewed configuration and issuance actions.

## 1. Configure the issuer

```bash
xrpl-hermes build-account-set --from rISSUER --domain issuer.example
xrpl-hermes build-account-set --from rISSUER --set-flag 8
```

Optional policy:

```bash
# Permit clawback on future trust lines
xrpl-hermes build-account-set --from rISSUER --set-flag 16

# Set a 1.5% transfer rate
xrpl-hermes build-account-set --from rISSUER --transfer-rate 1015000000
```

The current trust-line builder does not expose issuer authorization flags, so this guide does not support a `RequireAuth` issuance flow.

## 2. Create the distributor trust line

```bash
xrpl-hermes build-trustset \
  --from rDISTRIBUTOR --currency TOKEN --issuer rISSUER --value 1000000
```

## 3. Issue tokens

An issued-currency Payment from issuer to distributor creates the balance:

```bash
xrpl-hermes build-payment \
  --from rISSUER --to rDISTRIBUTOR \
  --amount 1000000 --cur TOKEN --iss rISSUER
```

For currency codes longer than three characters, use the required 160-bit hexadecimal currency representation.

## 4. Add liquidity

```bash
xrpl-hermes build-amm-create \
  --from rDISTRIBUTOR \
  --amount1 XRP:100000000 \
  --amount2 TOKEN:rISSUER:10000 \
  --fee 500

xrpl-hermes build-offer \
  --from rDISTRIBUTOR \
  --sell TOKEN:rISSUER:100 \
  --buy XRP:1000000
```

## 5. Verify

After every wallet-authorized transaction:

```bash
xrpl-hermes tx-info TX_HASH
xrpl-hermes account rISSUER
xrpl-hermes trustlines rDISTRIBUTOR TOKEN
xrpl-hermes amm-info XRP TOKEN:rISSUER
```

Require `validated: true` before advancing. Explorer listings and metadata providers are optional external services, not ledger proof.

Do not disable the master key or surrender freeze capability until replacement signing policy, final supply, holder policy, and recovery procedures have been independently verified.
