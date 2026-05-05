# XRPL MPTokens (XLS-33)

## Overview

**MPTokens** (Multi-Purpose Tokens) are a new token standard on the XRP Ledger introduced by the **XLS-33** specification. Unlike issued currencies on trust lines, MPTokens operate through a single-issuer issuance model with native support for features like transfer fees, locking, freezing, and authorized minting — all without requiring bilateral trust lines.

## Amendment Status

**IMPORTANT: The MPTokensV1 amendment is enabled on XRPL mainnet.** Check the current XRPL amendment status at [https://xrpl.org/amendments.html](https://xrpl.org/amendments.html) for the latest.

## MPTokens vs Trust Lines

| Feature | Trust Lines | MPTokens |
|---|---|---|
| Relationship | Bilateral (both parties agree) | Unilateral (issuer controls) |
| Reserve cost | 0.2 XRP per trust line per account | Single MPTokenIssuance entry |
| Transfer fees | Via TransferRate (global) | Per-issuance (can vary per issuance) |
| Freezing | Per trust line or global | Per-holder or global |
| Locking | Not available natively | Built-in locking mechanism |
| Authorized minting | Via RequireAuth + TrustSet | Built-in authorization |
| Scalability | Good for few trust lines | Better for mass distribution |

## MPTokenIssuance

An `MPTokenIssuance` is the ledger entry that defines a specific token. It's similar to an ERC-20 contract on Ethereum.

### Fields

| Field | Type | Description |
|---|---|---|
| `MPTokenIssuanceID` | Hash256 | Unique identifier for the issuance |
| `Issuer` | AccountID | The account that created the issuance |
| `AssetScale` | UInt8 | Number of decimal places (similar to token decimals) |
| `MaximumAmount` | UInt64 | Maximum total supply that can ever exist |
| `OutstandingAmount` | UInt64 | Current circulating supply |
| `Flags` | UInt32 | Issuance-level flags |
| `TransferFee` | UInt16 | Fee on transfers (in basis points, 1/100 of 1%) |
| `Metadata` | Blob | Optional metadata (hex-encoded) |

### MPTokenIssuanceID

The ID is derived from:
```
MPTokenIssuanceID = SHA-512Half(Issuer's AccountID + Issuer's Sequence Number)
```

### MPTokenIssuance Flags

| Flag | Hex | Decimal | Description |
|---|---|---|---|
| `mfMPTLocking` | 0x0001 | 1 | Issuance supports locking individual holder balances |
| `mfMPTFreezing` | 0x0002 | 2 | Issuance supports freezing individual holders |
| `mfMPTCanLock` | 0x0004 | 4 | Holders can lock their own tokens |
| `mfMPTAuthorizedMint` | 0x0008 | 8 | Only authorized accounts can mint new tokens |

## MPTokenIssuanceCreate Transaction

Creates a new MPTokenIssuance. This is a one-time setup transaction — you cannot modify fields like `AssetScale` or `MaximumAmount` after creation.

```json
{
  "TransactionType": "MPTokenIssuanceCreate",
  "Account": "rIssuerAddress",
  "AssetScale": 6,
  "MaximumAmount": "1000000000000000",
  "Flags": 1,
  "TransferFee": 100
}
```

This creates a new MPTokenIssuance with:
- 6 decimal places
- 1 billion max supply (1,000,000,000,000,000 / 10^6)
- Locking support enabled
- 1% transfer fee

## MPTokenIssuanceSet Transaction

Modifies an **existing** MPTokenIssuance (e.g., freeze a holder, lock a balance). Cannot change `AssetScale`, `MaximumAmount`, or `TransferFee` after creation.

```json
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rIssuerAddress",
  "MPTokenIssuanceID": "0000000000000000000000000000000000000000000000000000000000000001",
  "Flags": 2
}
```

## MPTokenAuthorize Transaction

Authorizes a holder to receive or hold MPTokens. Required when the issuance has authorized minting enabled.

```json
{
  "TransactionType": "MPTokenAuthorize",
  "Account": "rUserAddress",
  "MPTokenIssuanceID": "0000000000000000000000000000000000000000000000000000000000000001"
}
```

## MPTokenIssuanceDestroy Transaction

Destroys an MPTokenIssuance. Only the issuer can do this, and only if the outstanding amount is zero.

```json
{
  "TransactionType": "MPTokenIssuanceDestroy",
  "Account": "rIssuerAddress",
  "MPTokenIssuanceID": "0000000000000000000000000000000000000000000000000000000000000001"
}
```

## MPToken Fields

Individual holders have `MPToken` objects in their ledger entries representing their balance of a specific issuance.

### MPToken Fields

| Field | Type | Description |
|---|---|---|
| `MPTokenIssuanceID` | Hash256 | Which issuance this belongs to |
| `Holder` | AccountID | The holder's address |
| `Balance` | UInt64 | Current balance (in raw units, scaled by AssetScale) |
| `Flags` | UInt32 | Holder-level flags |
| `LockedAmount` | UInt64 | Amount that is locked (cannot be transferred) |

### MPToken Holder Flags

| Flag | Hex | Decimal | Description |
|---|---|---|---|
| `mfMPTLocked` | 0x0001 | 1 | This holder's tokens are locked |
| `mfMPTFrozen` | 0x0002 | 2 | This holder's tokens are frozen |

## Key Differences from Trust Lines

### Single Issuer Model

MPTokens have a single designated issuer. There is no "both sides" concept like trust lines. The issuer defines the token and all holders interact with that single issuance.

### No Reserve Per Holder

With trust lines, each holder pays 0.2 XRP reserve per trust line. With MPTokens, only the issuer pays reserve for the MPTokenIssuance object. Holders pay a smaller reserve for their MPToken balance object.

### Transfer Fees

Transfer fees are per-issuance and collected automatically on all secondary transfers:
- The fee is deducted from the transferred amount
- Accumulated fees go to the issuer
- Fee is specified in basis points (1 basis point = 0.01%)

### Locking

MPTokens support locking mechanisms:
- **Issuer lock**: Issuer can lock a holder's balance (if `mfMPTLocking` is enabled)
- **Self-lock**: Holder can lock their own balance (if `mfMPTCanLock` is enabled)
- Locked tokens cannot be transferred

### Freezing

Similar to freezing on trust lines:
- **Issuer freeze**: Issuer can freeze a holder (if `mfMPTFreezing` is enabled)
- Frozen tokens cannot be transferred or used in any way

## Working with MPTokens

### Minting Tokens

To create new tokens (increase supply), use a `Payment` transaction from the issuer's account to a holder with the MPToken amount. The supply is controlled by the `MaximumAmount` set at issuance time.

### Transferring Tokens

Transfers use a specialized transaction or can be done via the standard `Payment` transaction with the MPToken as the amount format.

### Querying MPToken Balances

```json
{
  "method": "account_lines",
  "params": [{
    "account": "rUserAddress"
  }]
}
```

Or a dedicated MPToken query endpoint (depending on implementation).

## Use Cases

### 1. Stablecoins

MPTokens are well-suited for stablecoin issuance:
- Single issuer control
- Built-in freeze for regulatory compliance
- Locking for reserve attestation
- Transfer fees for operational costs

### 2. Loyalty Points

- Issuer-controlled supply
- Locking prevents early redemption
- Authorized minting for partner programs
- Transfer fees for program economics

### 3. Tokenized Securities

- Regulatory compliance via freezing
- Authorized holders only
- Locking for settlement periods
- Single-issuer model matches security structure

### 4. Corporate Tokens

- Employee token grants with vesting (locking)
- Transfer restrictions
- Centralized management

## Migration from Trust Lines

For projects currently using trust lines and considering MPTokens:

1. **New tokens**: Issue new tokens as MPTokens
2. **Existing tokens**: May need a bridge or migration plan
3. **Hybrid approach**: Run both trust line and MPToken versions during transition
4. **User communication**: Explain the benefits and any required actions

## Development Status

As the MPTokensV1 amendment is enabled on mainnet:

1. **Follow development**: Watch the XRPL spec repo for updates
2. **Testnet testing**: When available, experiment on testnet
3. **Library support**: Check `xrpl.js`, `xrpl-py` for MPToken support
4. **Implementation**: Use amendment checks for networks where MPTokensV1 may not be enabled

## Issuance Code

The Hermes CLI can build unsigned MPToken transactions for review, signing, or handoff to a wallet service.

Create an issuance:

```bash
python3 -m scripts.xrpl_tools build-mpt-issuance-create \
  --from rIssuerAddress \
  --asset-scale 6 \
  --maximum-amount 1000000000000000 \
  --transfer-fee 100
```

Representative output:

```json
{
  "TransactionType": "MPTokenIssuanceCreate",
  "Account": "rIssuerAddress",
  "AssetScale": 6,
  "MaximumAmount": "1000000000000000",
  "TransferFee": 100
}
```

Create an issuance with holder authorization required:

```bash
python3 -m scripts.xrpl_tools build-mpt-issuance-create \
  --from rIssuerAddress \
  --asset-scale 2 \
  --maximum-amount 100000000 \
  --flags 8
```

Python builder example:

```python
from xrpl.models.transactions import MPTokenIssuanceCreate

tx = MPTokenIssuanceCreate(
    account="rIssuerAddress",
    asset_scale=6,
    maximum_amount="1000000000000000",
    transfer_fee=100,
)

print(tx.to_xrpl())
```

Metadata can be attached as a hex blob. Keep the JSON small and host full metadata off-ledger when possible:

```python
import json

metadata = {
    "name": "Example Points",
    "ticker": "POINT",
    "uri": "https://example.com/mpt/points.json",
}

metadata_hex = json.dumps(metadata, separators=(",", ":")).encode().hex().upper()
```

```json
{
  "TransactionType": "MPTokenIssuanceCreate",
  "Account": "rIssuerAddress",
  "AssetScale": 0,
  "MaximumAmount": "1000000000",
  "Metadata": "7B226E616D65223A224578616D706C6520506F696E7473227D"
}
```

## Holder-Side Example

When authorization is required, the holder creates or updates their MPToken object with `MPTokenAuthorize`.

```bash
python3 -m scripts.xrpl_tools build-mpt-authorize \
  --from rHolderAddress \
  --mpt-issuance-id 0000000000000000000000000000000000000000000000000000000000000001
```

Representative holder authorization transaction:

```json
{
  "TransactionType": "MPTokenAuthorize",
  "Account": "rHolderAddress",
  "MPTokenIssuanceID": "0000000000000000000000000000000000000000000000000000000000000001"
}
```

Issuer-side authorization of a holder:

```bash
python3 -m scripts.xrpl_tools build-mpt-authorize \
  --from rIssuerAddress \
  --mpt-issuance-id 0000000000000000000000000000000000000000000000000000000000000001 \
  --holder rHolderAddress
```

Representative issuer authorization transaction:

```json
{
  "TransactionType": "MPTokenAuthorize",
  "Account": "rIssuerAddress",
  "MPTokenIssuanceID": "0000000000000000000000000000000000000000000000000000000000000001",
  "Holder": "rHolderAddress"
}
```

After authorization, distribution normally happens through a payment from the issuer to the holder:

```json
{
  "TransactionType": "Payment",
  "Account": "rIssuerAddress",
  "Destination": "rHolderAddress",
  "Amount": {
    "mpt_issuance_id": "0000000000000000000000000000000000000000000000000000000000000001",
    "value": "25000000"
  }
}
```

Holder self-custody flow:

1. Holder funds an XRPL account with enough XRP for reserve.
2. Holder authorizes the issuance if the token requires authorization.
3. Issuer sends the MPToken payment.
4. Holder verifies the MPToken object exists in account objects.
5. Holder monitors freezes, locks, and balances before secondary transfers.

## Balance Query

Use `account_objects` to inspect MPToken entries owned by an account:

```json
{
  "method": "account_objects",
  "params": [{
    "account": "rHolderAddress",
    "ledger_index": "validated",
    "type": "mptoken"
  }]
}
```

Example response shape:

```json
{
  "account_objects": [{
    "LedgerEntryType": "MPToken",
    "MPTokenIssuanceID": "0000000000000000000000000000000000000000000000000000000000000001",
    "Balance": "25000000",
    "Flags": 0
  }],
  "ledger_index": 12345678,
  "validated": true
}
```

Python balance helper:

```python
from decimal import Decimal
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountObjects

client = JsonRpcClient("https://xrplcluster.com")

def mpt_balance(account: str, issuance_id: str, asset_scale: int) -> Decimal:
    resp = client.request(AccountObjects(
        account=account,
        ledger_index="validated",
        type="mptoken",
    ))
    for obj in resp.result.get("account_objects", []):
        if obj.get("MPTokenIssuanceID") == issuance_id:
            raw = Decimal(obj.get("Balance", "0"))
            return raw / (Decimal(10) ** asset_scale)
    return Decimal("0")
```

CLI-style query using the generic account objects command:

```bash
python3 -m scripts.xrpl_tools account-objects rHolderAddress mptoken
```

Display helper:

```python
def format_mpt_amount(raw_value: str, asset_scale: int, symbol: str) -> str:
    value = Decimal(raw_value) / (Decimal(10) ** asset_scale)
    return f"{value:f} {symbol}"
```

## Operational Patterns

Issuers should record the issuance transaction hash and derive the `MPTokenIssuanceID` from validated ledger data, not from an unvalidated local sequence estimate.

Recommended issuance records:

| Field | Source |
|---|---|
| `issuer` | Issuer account |
| `issuance_id` | Validated `MPTokenIssuanceID` |
| `asset_scale` | Issuance create transaction |
| `maximum_amount` | Issuance create transaction |
| `transfer_fee` | Issuance create transaction |
| `metadata_uri` | Decoded metadata or project database |
| `create_hash` | Validated transaction hash |

For services, separate responsibilities:

- Builder service creates unsigned JSON.
- Wallet or signing service handles signatures.
- Submission service tracks validation.
- Indexer service records balances and holder flags.
- API service serves normalized token data to applications.

Validation checklist:

- Confirm `MPTokensV1` is enabled on the target network.
- Confirm issuer reserve can cover the issuance object.
- Confirm `MaximumAmount` uses raw units, not display units.
- Confirm `AssetScale` matches UI display expectations.
- Confirm `TransferFee` is within protocol limits.
- Confirm metadata is hex-encoded and not oversized.
- Confirm authorization behavior before public launch.
- Confirm the destroy path requires zero outstanding supply.

## Common Errors

| Symptom | Likely Cause | Fix |
|---|---|---|
| Holder cannot receive tokens | Authorization missing | Submit `MPTokenAuthorize` |
| Display amount is too large | Raw units shown directly | Divide by `10 ** AssetScale` |
| Issuance cannot be destroyed | Outstanding supply remains | Burn or return all tokens first |
| Transfers fail after issuance | Freeze or lock flag active | Inspect holder MPToken flags |
| Supply math is confusing | Mixed raw and display units | Store raw values and format at edges |

Use immutable issuance settings carefully. If decimals, max supply, or fee are wrong, the practical fix is usually a new issuance plus migration tooling.

## Resources

- [XLS-33 Specification (originally XLS-70)](https://github.com/XRPLF/XRPL-Standards/discussions/70)
- [xrpl.org MPToken Docs](https://xrpl.org/docs/concepts/tokens/mptokens)
- XRPL Dev Blog for amendment status updates

---

## Related Files

- `knowledge/21-xrpl-token-model.md` — MPT vs trust line trade-offs
- `knowledge/22-xrpl-token-issuance.md` — issuance flow patterns
- `knowledge/36-xrpl-xls-standards.md` — XLS-33 spec
- `knowledge/37-xrpl-amendments.md` — MPT amendment status

## End-to-End MPT Issuance Example

Issuer creates an MPT issuance, holder authorizes it, then the client queries holder balances through account objects.

```bash
ISSUER=r9cZA1mLK5R5Am25ArfXFmqgNwjZgnfk59
HOLDER=rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe
python3 -m scripts.xrpl_tools build-mpt-issuance-create --from $ISSUER --maximum-amount 1000000 --transfer-fee 250
python3 -m scripts.xrpl_tools build-mpt-authorize --from $HOLDER --mpt-issuance-id MPT_ISSUANCE_ID
python3 -m scripts.xrpl_tools account_objects $HOLDER mptoken
```

## Holder-Side Authorization Example

```python
from scripts.tools.mpts import tool_build_mpt_authorize
tool_build_mpt_authorize(frm='rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe', mpt_issuance_id='000001...')
```

Holder authorization should be presented as a signer-ready transaction. The holder signs from their own wallet.

## Client-Side MPT Balance Query

```python
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountObjects

client = JsonRpcClient('https://s.altnet.rippletest.net:51234')
resp = client.request(AccountObjects(account='rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe', type='mptoken', ledger_index='validated'))
for obj in resp.result.get('account_objects', []):
    print(obj)
```

### MPT Implementation Note 1

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 2

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 3

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 4

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 5

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 6

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 7

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 8

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 9

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 10

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 11

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 12

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 13

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 14

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 15

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 16

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 17

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 18

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 19

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 20

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 21

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 22

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 23

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 24

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 25

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 26

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 27

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 28

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 29

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 30

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 31

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 32

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 33

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 34

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 35

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 36

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 37

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 38

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 39

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 40

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.

### MPT Implementation Note 41

- Keep issuer, holder, issuance ID, and authorization status in separate database columns.
- Query `account_objects type=mptoken` after signing to confirm the holder-side ledger object exists.
- Treat amendment availability and testnet behavior as network-specific until mainnet support is confirmed.
