# XRPL Accounts

## Overview

An XRP Ledger account represents a holder of XRP and a party that can send transactions. Accounts are the fundamental building blocks of the XRPL — all transactions originate from an account and all objects (trust lines, offers, escrows, etc.) are owned by an account.

## Address Format

XRPL addresses use a base58 encoding with a version prefix specific to the XRPL. Addresses are 25-35 characters long, start with an `r` (mainnet) or `t` (testnet), and include a checksum via double SHA-256.

**Example addresses:**
- `r9cZA1mLK5R5Am25ArfXFmqgN1sV5f3gQR` (mainnet)
- `rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh` (mainnet genesis)
- `tHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh` (testnet equivalent)

The base58 encoding uses the following alphabet: `rpshnaf39wBUDNEGHJKLM4PQRST7VWXYZ2bcdeCg65jkm8oFqi1tuvAxyz`

## Account Creation

Accounts are created by sending XRP to a brand new address that doesn't yet exist on the ledger. The payment automatically creates the account if:

1. The destination address is a valid XRPL address
2. The amount sent is at least the **account reserve** (currently 1 XRP base)
3. The destination address does not already exist on the ledger

There is no explicit "create account" transaction — it happens implicitly via a payment to a non-existent address.

### Creating an Account (Python Example)

```python
from xrpl.wallet import Wallet
from xrpl.transaction import submit_and_wait
from xrpl.models.transactions import Payment
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.utils import xrp_to_drops

# Generate a new wallet (offline)
new_wallet = Wallet.create()

# Fund it from an existing account (on-chain)
payment = Payment(
    account=source_wallet.classic_address,
    destination=new_wallet.classic_address,
    amount=xrp_to_drops(20),  # 20 XRP — covers reserve + some buffer
)
response = submit_and_wait(payment, client, source_wallet)
```

## Account Reserve

Every XRPL account must hold a minimum amount of XRP, called the **reserve**. This prevents ledger bloat and is a core part of XRPL's anti-spam mechanism.

| Reserve Component | Current Amount |
|---|---|
| Base Reserve | 1 XRP |
| Owner Reserve (per owned object) | 0.2 XRP |

**Owned objects** include:
- Trust lines
- Offers (both buy and sell)
- Escrows
- Checks
- Payment channels
- Signer lists
- Tickets
- NFT pages (each page holds up to 32 NFTs)

So an account with 5 trust lines and 3 offers would need: 1 + (8 × 0.2) = 2.6 XRP reserved.

The reserve is **not** spent — it's locked. An account cannot send XRP that would drop its balance below the reserve.

## Key Pairs

XRPL supports two key pair types:

### secp256k1 (ECDSA)

- Uses the same elliptic curve as Bitcoin
- Default for most wallets
- Produces 33-byte compressed public keys (prefix 0x02/0x03)
- Uses ECDSA signature scheme

### Ed25519

- More modern and faster than secp256k1
- Shorter 32-byte public keys
- Deterministic signatures (same message + key = same signature)
- Cannot produce an XRPL address starting with `r` directly (the address is derived from Ed25519 public key)
- Uses EdDSA signature scheme

**Key derivation hierarchy:**
```
Seed (16-32 bytes) → Master Key Pair → Account ID → Address
```

A seed can be represented as:
- Raw hex bytes
- Base58 (starting with `s`)
- Mnemonic phrase (via standards like BIP39)

## Account Root Fields

Every account has an **AccountRoot** ledger entry. Here are all the fields:

| Field | Type | Description |
|---|---|---|
| `Account` | AccountID | The address of the account |
| `Balance` | Amount | Account's XRP balance in drops (1 drop = 0.000001 XRP) |
| `Flags` | UInt32 | Bitwise flags for account settings |
| `OwnerCount` | UInt32 | Number of objects owned (affects reserve) |
| `PreviousTxnID` | Hash256 | ID of the last transaction affecting this account |
| `PreviousTxnLgrSeq` | UInt32 | Ledger sequence of the last transaction |
| `Sequence` | UInt32 | Next valid transaction sequence number |
| `RegularKey` | AccountID | Optional regular key address |
| `Domain` | BLob | Optional domain (hex-encoded ASCII) |
| `EmailHash` | Hash128 | Optional email hash (deprecated) |
| `MessageKey` | BLob | Optional encryption key |
| `TickSize` | UInt8 | Exchange rate precision (3-15) |
| `TransferRate` | UInt32 | Transfer fee for tokens issued by this account (1.0 = no fee) |
| `AccountTxnID` | Hash256 | ID of the most recent transaction sent by this account |

### Balance Field

The Balance field stores XRP in **drops** where:
- 1 XRP = 1,000,000 drops
- Minimum non-zero balance = 1 drop
- Maximum balance = 10^17 drops (100 billion XRP)

Balances are stored as UInt64 (unsigned 64-bit integer), but the XRPL caps the max XRP supply at 100 billion (10^17 drops).

### OwnerCount

The `OwnerCount` tracks how many ledger objects the account owns. Each object increases required reserve by the owner reserve amount (0.2 XRP per object).

Max objects per account is typically bounded by the transaction cost — each object creation costs a base fee + the reserve. There's no hard cap, but at some point it becomes economically impractical.

## Account Flags

Account flags are stored in the `Flags` field of the AccountRoot. They can be set or cleared using the `AccountSet` transaction.

### Flag Values

| Flag Name | Hex Value | Decimal | Description |
|---|---|---|---|
| `lsfDefaultRipple` | 0x00800000 | 8388608 | Enables rippling on all trust lines by default |
| `lsfDepositAuth` | 0x01000000 | 16777216 | Requires pre-authorization to receive payments |
| `lsfDisableMasterKey` | 0x00100000 | 1048576 | Disables the master key pair (account can only sign with RegularKey or SignerList) |
| `lsfNoFreeze` | 0x00200000 | 2097152 | Permanently gives up the ability to freeze trust lines |
| `lsfGlobalFreeze` | 0x00400000 | 4194304 | Freezes all tokens issued by this account (no transfers among holders) |
| `lsfRequireAuth` | 0x00040000 | 262144 | Requires authorization for trust lines to this issuer |
| `lsfRequireDestTag` | 0x00020000 | 131072 | Requires a DestinationTag on incoming payments |

### Setting Flags

Use `AccountSet` with the `SetFlag` field:

```json
{
  "TransactionType": "AccountSet",
  "Account": "r9cZA1mLK5R5Am25ArfXFmqgN1sV5f3gQR",
  "SetFlag": 8  // lsfDefaultRipple
}
```

### Clearing Flags

Use `AccountSet` with the `ClearFlag` field:

```json
{
  "TransactionType": "AccountSet",
  "Account": "r9cZA1mLK5R5Am25ArfXFmqgN1sV5f3gQR",
  "ClearFlag": 8  // lsfDefaultRipple
}
```

### Important Notes on Flags

- **lsfDisableMasterKey is IRREVERSIBLE** if no RegularKey or SignerList is set — the account becomes a **blackhole**
- **lsfNoFreeze is IRREVERSIBLE** — you permanently give up freeze capability
- **lsfGlobalFreeze** disables ALL transfers of the issuer's tokens
- **lsfDefaultRipple** is recommended for token issuers but not for regular users
- **lsfRequireDestTag** protects against payments missing the destination tag (common issue with exchanges)

## Account Deletion

**XRPL accounts CANNOT be deleted.** There is no mechanism to remove an AccountRoot from the ledger. XRP held as reserve is permanently locked by the account.

An account can be "blackholed" by:
1. Setting the master key as disabled (`lsfDisableMasterKey`)
2. Removing any regular key
3. Removing any signer lists

Once blackholed, no transactions can ever be submitted from that account. The XRP in the reserve is permanently inaccessible.

## Account Root JSON Example

### Standard Account

```json
{
  "Account": "r9cZA1mLK5R5Am25ArfXFmqgN1sV5f3gQR",
  "Balance": "10000000000",
  "Flags": 0,
  "LedgerEntryType": "AccountRoot",
  "OwnerCount": 3,
  "PreviousTxnID": "E8F0E8F0E8F0E8F0E8F0E8F0E8F0E8F0E8F0E8F0E8F0E8F0E8F0E8F0E8F0",
  "PreviousTxnLgrSeq": 12345,
  "Sequence": 15,
  "index": "5C5F5C5F5C5F5C5F5F5C5F5F5C5F5F5C5F5F5C5F5C5F5C5F5C5F5C5F5C5F"
}
```

### Token Issuer Account

```json
{
  "Account": "rKiCet8SfE9T3zF3i1gXzT6YLuYQnXqXr",
  "Balance": "50000000000",
  "Flags": 8388608,
  "LedgerEntryType": "AccountRoot",
  "OwnerCount": 15,
  "PreviousTxnID": "A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6",
  "PreviousTxnLgrSeq": 54321,
  "RegularKey": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
  "Sequence": 42,
  "Domain": "6578616D706C652E636F6D",
  "TickSize": 5,
  "TransferRate": 1005000000,
  "index": "ABCDEFABCDEFABCDEFABCDEFABCDEFABCDEFABCDEFABCDEFABCDEFABCDEF"
}
```

### AccountInfo Response

```json
{
  "result": {
    "account_data": {
      "Account": "r9cZA1mLK5R5Am25ArfXFmqgN1sV5f3gQR",
      "Balance": "10000000000",
      "Flags": 0,
      "LedgerEntryType": "AccountRoot",
      "OwnerCount": 0,
      "PreviousTxnID": "0000000000000000000000000000000000000000000000000000000000000000",
      "PreviousTxnLgrSeq": 0,
      "Sequence": 1,
      "index": "ABABABABABABABABABABABABABABABABABABABABABABABABABABABABABABABAB"
    },
    "ledger_current_index": 12345678,
    "queue_data": {
      "txn_count": 0
    },
    "validated": true
  },
  "status": "success",
  "type": "response"
}
```

## Data Types

| Type | Description | Size |
|---|---|---|
| UInt8 | Unsigned 8-bit integer | 1 byte |
| UInt16 | Unsigned 16-bit integer | 2 bytes |
| UInt32 | Unsigned 32-bit integer | 4 bytes |
| UInt64 | Unsigned 64-bit integer (serialized as 8 bytes) | 8 bytes |
| STAmount | XRP or issued currency amount (variable) | Variable |
| AccountID | 160-bit account address | 20 bytes |
| Hash128 | 128-bit hash | 16 bytes |
| Hash160 | 160-bit hash | 20 bytes |
| Hash256 | 256-bit hash | 32 bytes |
| Blob | Arbitrary binary data | Variable |
| Vector256 | Array of 256-bit hashes | Variable |
| PathSet | Set of payment paths | Variable |
