# XRPL-Hermes — Complete CLI Reference

All 48 tools available via `python3 scripts/xrpl_tools.py <command> [args]`.

---

## L1 — Account & Ledger

### `account`
Fetch account info, balance, reserve, and flags.

```bash
python3 scripts/xrpl_tools.py account rADDRESS
# alias: balance
python3 scripts/xrpl_tools.py balance rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe
```

Sample output:
```json
{
  "Account": "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe",
  "BalanceDrops": "25123456",
  "BalanceXRP": "25.123456",
  "ReserveXRP": "2.0",
  "OwnerCount": 5,
  "SpendableXRP": "23.123456",
  "Sequence": 4821,
  "Domain": null,
  "Flags": 0,
  "FlagDescriptions": []
}
```

---

### `trustlines`
List all trust lines for an account, optionally filtered by currency.

```bash
python3 scripts/xrpl_tools.py trustlines rADDRESS [CURRENCY]
python3 scripts/xrpl_tools.py trustlines rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe USD
```

---

### `account_objects`
List on-ledger objects owned by an account (offers, escrows, checks, channels, etc.).

```bash
python3 scripts/xrpl_tools.py account_objects rADDRESS [type]
python3 scripts/xrpl_tools.py account_objects rADDRESS offer
python3 scripts/xrpl_tools.py account_objects rADDRESS escrow
```

---

### `ledger`
Fetch the latest validated ledger or a specific one by index.

```bash
python3 scripts/xrpl_tools.py ledger
python3 scripts/xrpl_tools.py ledger 88000000
```

---

### `server-info`
Show connected node info: version, ledger, uptime, load.

```bash
python3 scripts/xrpl_tools.py server-info
```

---

### `tx-info`
Fetch a transaction by hash and display its metadata.

```bash
python3 scripts/xrpl_tools.py tx-info A7CCD11455E47602D4B4FECF2A2A37CF...
```

---

### `decode`
Decode a signed transaction blob to human-readable JSON.

```bash
python3 scripts/xrpl_tools.py decode 1200002200000000...
```

---

## L1 — Transaction Building (all output raw JSON for Xaman/Crossmark)

### `build-payment`
Build a Payment transaction (XRP drops or issued token).

```bash
# XRP payment (amount in drops: 1 XRP = 1,000,000 drops)
python3 scripts/xrpl_tools.py build-payment \
  --from rSENDER --to rDEST --amount 1000000

# Token payment (use --cur and --iss flags)
python3 scripts/xrpl_tools.py build-payment \
  --from rSENDER --to rDEST \
  --amount 100 --cur USD --iss rISSUER
```

---

### `build-trustset`
Set or modify a trust line for an issued currency.

```bash
python3 scripts/xrpl_tools.py build-trustset \
  --from rACCOUNT \
  --currency USD \
  --issuer rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh \
  --value 1000000000
```

---

### `build-offer`
Create a DEX offer (limit order).

```bash
# Sell 100 XRP (in drops) for 50 USD
python3 scripts/xrpl_tools.py build-offer \
  --from rACCOUNT \
  --sell XRP:100000000 \
  --buy USD:rISSUER:50
```

---

### `build-clawback`
Issuer reclaims tokens from a holder (requires AllowTrustLineClawback flag set on issuer).

```bash
python3 scripts/xrpl_tools.py build-clawback \
  --from rISSUER \
  --destination rHOLDER \
  --currency USD \
  --amount 100
```

Sample output:
```json
{
  "Account": "rISSUER...",
  "TransactionType": "Clawback",
  "Amount": {
    "currency": "USD",
    "issuer": "rHOLDER...",
    "value": "100"
  }
}
```

---

### `build-deposit-preauth`
Pre-authorize or de-authorize a sender for your account (used when DepositAuth is enabled).

```bash
python3 scripts/xrpl_tools.py build-deposit-preauth \
  --from rACCOUNT --authorize rSENDER

python3 scripts/xrpl_tools.py build-deposit-preauth \
  --from rACCOUNT --unauthorize rSENDER
```

---

### `build-set-regular-key`
Set or clear a regular key for an account.

```bash
python3 scripts/xrpl_tools.py build-set-regular-key \
  --from rACCOUNT --regular-key rNEW_KEY

# Clear regular key (omit --regular-key)
python3 scripts/xrpl_tools.py build-set-regular-key --from rACCOUNT
```

---

### `build-account-delete`
Delete an account and sweep remaining XRP to destination.

```bash
python3 scripts/xrpl_tools.py build-account-delete \
  --from rACCOUNT --to rDEST
```

---

## L1 — AMM

### `build-amm-create`
Create an AMM pool with two assets.

```bash
# XRP + USD pool with 0.6% trading fee
python3 scripts/xrpl_tools.py build-amm-create \
  --from rACCOUNT \
  --amount1 XRP:10000000 \
  --amount2 USD:rISSUER:100 \
  --fee 600
```

---

### `build-amm-deposit`
Deposit into an AMM pool. `--mode` is `two-asset` (default), `single-asset`, or `lp-token`.

```bash
python3 scripts/xrpl_tools.py build-amm-deposit \
  --from rACCOUNT \
  --asset1 XRP --asset2 USD:rISSUER \
  --amount1 XRP:1000000 --amount2 USD:rISSUER:100
```

---

### `build-amm-withdraw`
Withdraw from an AMM pool. `--mode` is `two-asset`, `single-asset`, `lp-token`, or `withdraw-all`.

```bash
python3 scripts/xrpl_tools.py build-amm-withdraw \
  --from rACCOUNT \
  --asset1 XRP --asset2 USD:rISSUER \
  --amount1 XRP:500000
```

---

### `build-amm-vote`
Vote on the AMM trading fee (0–1000 = 0–1%).

```bash
python3 scripts/xrpl_tools.py build-amm-vote \
  --from rACCOUNT \
  --asset1 XRP --asset2 USD:rISSUER \
  --trading-fee 600
```

---

### `build-amm-bid`
Bid for the 24-hour AMM auction slot (fee discount).

```bash
python3 scripts/xrpl_tools.py build-amm-bid \
  --from rACCOUNT \
  --asset1 XRP --asset2 USD:rISSUER \
  --bid-min LPT:rAMMPOOL:50
```

---

## L1 — Multi-sig

### `build-signer-list-set`
Configure a SignerList for multi-sig accounts. Comma-separated `rADDR:WEIGHT` pairs.

```bash
python3 scripts/xrpl_tools.py build-signer-list-set \
  --from rACCOUNT \
  --quorum 2 \
  --signers rA:1,rB:1,rC:1
```

---

## L1 — MPT (XLS-33)

### `build-mpt-issuance-create`
Create a Multi-Purpose Token issuance. Auto-sets `tfMPTCanTransfer` if `--transfer-fee` is given.

```bash
python3 scripts/xrpl_tools.py build-mpt-issuance-create \
  --from rISSUER \
  --maximum-amount 1000000000000000 \
  --asset-scale 6 \
  --transfer-fee 200
```

---

### `build-mpt-authorize`
Authorize an MPT holder. Issuers pass `--holder rADDR`; holders omit it (self-auth).

```bash
python3 scripts/xrpl_tools.py build-mpt-authorize \
  --from rISSUER \
  --mpt-issuance-id 00000001ABCDEF... \
  --holder rHOLDER
```

---

## L1 — Oracle (XLS-47)

### `build-set-oracle`
Publish a price oracle update. `--price-data` is a comma-separated list of `BASE/QUOTE:PRICE:SCALE`.

```bash
python3 scripts/xrpl_tools.py build-set-oracle \
  --from rORACLE \
  --oracle-doc-id 1 \
  --provider 5052494345 \
  --asset-class 554e434c \
  --last-update-time 2000000000 \
  --price-data XRP/USD:50000:6,BTC/USD:65000000:2
```

---

## L1 — Credentials (XLS-70)

### `build-credential-create`
Issuer creates a credential for a subject. `--credential-type` is hex-encoded.

```bash
python3 scripts/xrpl_tools.py build-credential-create \
  --from rISSUER \
  --subject rHOLDER \
  --credential-type 4B5943
```

---

### `build-credential-accept`
Subject accepts a credential issued to them.

```bash
python3 scripts/xrpl_tools.py build-credential-accept \
  --from rHOLDER \
  --issuer rISSUER \
  --credential-type 4B5943
```

---

### `build-credential-delete`
Either party can delete an existing credential.

```bash
python3 scripts/xrpl_tools.py build-credential-delete \
  --from rISSUER \
  --credential-type 4B5943 \
  --subject rHOLDER
```

---

## L1 — Cross-Currency Payments

### `build-cross-currency-payment`
Build a Payment that spends one asset and delivers another via path-finding.

```bash
python3 scripts/xrpl_tools.py build-cross-currency-payment \
  --from rSENDER --to rDEST \
  --deliver USD:rISSUER:100 \
  --send-max XRP:5000000
```

---

## L1 — Batch (XLS-56)

### `build-batch`
Wrap 2–8 inner transactions in a Batch. Inner txs are JSON dicts with their canonical XRPL field names.

```bash
python3 scripts/xrpl_tools.py build-batch --from rACCOUNT --inner-txs '[
  {"TransactionType":"Payment","Account":"rACCOUNT","Destination":"rA","Amount":"1000"},
  {"TransactionType":"Payment","Account":"rACCOUNT","Destination":"rB","Amount":"2000"}
]'
```

---

## L1 — Escrow

### `build-escrow-create`
Create a time-locked or condition-locked escrow.

```bash
python3 scripts/xrpl_tools.py build-escrow-create \
  --from rACCOUNT --to rDEST --amount 10000000 \
  --finish-after 1800000000

# With crypto-condition (PREIMAGE-SHA-256)
python3 scripts/xrpl_tools.py build-escrow-create \
  --from rACCOUNT --to rDEST --amount 10000000 \
  --condition A0258020...
```

---

### `build-escrow-finish`
Finish (release) an escrow, optionally providing fulfillment.

```bash
python3 scripts/xrpl_tools.py build-escrow-finish \
  --from rACCOUNT --owner rESCROW_OWNER --offer-sequence 42

python3 scripts/xrpl_tools.py build-escrow-finish \
  --from rACCOUNT --owner rESCROW_OWNER --offer-sequence 42 \
  --condition A025... --fulfillment A022...
```

---

### `build-escrow-cancel`
Cancel an expired escrow and return funds to creator.

```bash
python3 scripts/xrpl_tools.py build-escrow-cancel \
  --from rACCOUNT --owner rESCROW_OWNER --offer-sequence 42
```

---

## L1 — Checks

### `build-check-create`
Create a check (deferred payment authorization).

```bash
python3 scripts/xrpl_tools.py build-check-create \
  --from rACCOUNT --to rDEST --amount 5000000 \
  --expiry 1900000000
```

---

### `build-check-cash`
Cash (redeem) a check created by another account.

```bash
python3 scripts/xrpl_tools.py build-check-cash \
  --from rACCOUNT \
  --check-id A7CCD11455E47602... \
  --amount 5000000
```

---

### `build-check-cancel`
Cancel a check you created.

```bash
python3 scripts/xrpl_tools.py build-check-cancel \
  --from rACCOUNT --check-id A7CCD11455E47602...
```

---

## L1 — Payment Channels

### `build-paychannel-create`
Open a payment channel for high-frequency micro-payments.

```bash
python3 scripts/xrpl_tools.py build-paychannel-create \
  --from rACCOUNT --to rDEST \
  --amount 10000000 \
  --settle-delay 86400 \
  --public-key ED...
```

---

### `build-paychannel-fund`
Add XRP to an existing payment channel.

```bash
python3 scripts/xrpl_tools.py build-paychannel-fund \
  --from rACCOUNT \
  --channel-id ABC123... \
  --amount 5000000
```

---

### `build-paychannel-claim`
Claim from a payment channel (receiver or sender closing).

```bash
python3 scripts/xrpl_tools.py build-paychannel-claim \
  --from rACCOUNT \
  --channel-id ABC123... \
  --amount 2000000 \
  --balance 2000000 \
  --signature 3045... \
  --public-key ED...
```

`--balance` is the cumulative XRP delivered through the channel after this
claim is processed (not the per-claim amount). Required when the receiver
posts the claim to the ledger.

---

## L1 — NFTs

### `build-nft-mint`
Mint a new NFT on XRPL (XLS-20).

```bash
python3 scripts/xrpl_tools.py build-nft-mint \
  --from rACCOUNT \
  --taxon 42 \
  --transfer-fee 5000 \
  --uri 697066733A2F2F...
```

---

### `nft-info`
Fetch NFT metadata by NFT ID.

```bash
python3 scripts/xrpl_tools.py nft-info 00080000...
```

---

## L1 — DEX & Paths

### `book-offers`
Fetch current order book between two assets.

```bash
python3 scripts/xrpl_tools.py book-offers XRP USD:rISSUER
python3 scripts/xrpl_tools.py book-offers USD:rISSUER EUR:rISSUER2
```

---

### `path-find`
Find payment paths for cross-currency payments.

```bash
python3 scripts/xrpl_tools.py path-find rSENDER rDEST 100 USD:rISSUER
```

---

## EVM Sidechain (XRPL EVM Compatible)

### `evm-balance`
Fetch EVM-compatible account balance.

```bash
python3 scripts/xrpl_tools.py evm-balance 0xADDRESS mainnet
python3 scripts/xrpl_tools.py evm-balance 0xADDRESS testnet
```

---

### `evm-contract`
Build a raw contract deployment transaction.

```bash
python3 scripts/xrpl_tools.py evm-contract \
  --from 0xACCOUNT \
  --bytecode 6080604052...
```

---

### `evm-bridge`
Show EVM bridge contract addresses and status.

```bash
python3 scripts/xrpl_tools.py evm-bridge mainnet
python3 scripts/xrpl_tools.py evm-bridge testnet
```

---

## Hooks (Xahau)

### `hooks-bitmask`
⚠️ **BROKEN** — Xahau `HookOn` is a 256-bit bitmap indexed by transaction-type
ID, not named events. This tool currently only emits a warning so a developer
isn't misled into shipping a broken hook config. Do not rely on it. See
`knowledge/51-xrpl-xahau-hooks.md` and the upstream
[Xahau hooks docs](https://xrpl-hooks.readthedocs.io/) for the real spec.

```bash
python3 scripts/xrpl_tools.py hooks-bitmask Payment OfferCreate
# emits JSON warning; produces no usable bitmask
```

---

### `hooks-info`
Fetch installed hooks on an account (Xahau network).

```bash
python3 scripts/xrpl_tools.py hooks-info rACCOUNT
```

---

## Flare Network

### `flare-price`
Fetch current FTSOv2 price for one or more symbols.

```bash
python3 scripts/xrpl_tools.py flare-price XRP FLR BTC ETH
```

---

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `XRPL_PRIVATE_RPC` | (none) | Your private rippled/Clio endpoint URL (takes priority over public failover) |
| `XRPL_SEED` | (none) | Testnet wallet seed for example scripts |
| `XRPLSCAN_API_KEY` | (none) | XRPLScan enhanced API access (agent enrichment only) |
| `XRPL_TO_API_KEY` | (none) | XRPL.to API key (agent enrichment only) |

---

## Exit Codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Import error (missing xrpl-py) |
| Validation error printed | Invalid arguments (no exit) |
