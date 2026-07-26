# XRPL treasury operations

Treasury workflows combine account policy, multisignature configuration, time locks, payment controls, and validated-ledger monitoring. XRPL-Hermes builds unsigned intent only.

## Account policy

```bash
xrpl-hermes build-account-set --from rTREASURY --domain treasury.example
xrpl-hermes build-deposit-preauth --from rTREASURY --authorize rAPPROVED
xrpl-hermes build-set-regular-key --from rTREASURY --regular-key rREGULAR
```

Master-key, regular-key, and deposit-policy changes can lock or expose an account when sequenced incorrectly. Review current account flags and signer policy before authorization.

## Multisignature configuration

```bash
xrpl-hermes build-signer-list-set \
  --from rTREASURY --quorum 2 \
  --signers rSIGNER1:1,rSIGNER2:1,rSIGNER3:1
```

XRPL-Hermes does not collect signatures or submit multisigned transactions. Each signer uses an independent wallet/HSM/KMS workflow outside Hermes.

## Time-locked reserves

```bash
xrpl-hermes build-escrow-create \
  --from rTREASURY --to rDESTINATION \
  --amount 100000000 --finish-after RIPPLE_TIME
```

Confirm finish/cancel conditions, destination, amount, and time conversion before authorization.

## High-frequency disbursement setup

```bash
xrpl-hermes build-paychannel-create \
  --from rTREASURY --to rDESTINATION \
  --amount 100000000 --settle-delay 86400 --public-key PUBLIC_KEY
```

Payment-channel claim signing is a separate cryptographic workflow and is not implemented by XRPL-Hermes.

## Monitoring

```bash
xrpl-hermes account rTREASURY
xrpl-hermes account_objects rTREASURY
xrpl-hermes account-tx rTREASURY 50
xrpl-hermes subscribe streams=accounts accounts=rTREASURY duration=300
```

Alert on signing-policy changes, unexpected destination/tag, large balance movement, new owner objects, failed transactions that consume fee/sequence, and reserve pressure.

## Receipt requirements

For every authorized treasury operation, retain the reviewed unsigned intent, wallet handoff, transaction hash, validated ledger index, engine result, fees, and post-transaction state. Never treat a signature request or submitted hash as settlement.
