# XRPL MPTokens (XLS-70)

## Overview

**MPTokens** (Multi-Purpose Tokens) are a new token standard on the XRP Ledger introduced by the **XLS-70** draft specification. Unlike issued currencies on trust lines, MPTokens operate through a single-issuer issuance model with native support for features like transfer fees, locking, freezing, and authorized minting — all without requiring bilateral trust lines.

## Amendment Status

**IMPORTANT: The XLS-70 amendment for MPTokens is NOT YET ACTIVE on XRPL mainnet as of early 2026.** It has been specified and may be in testing on testnet/devnet. Check the current XRPL amendment status at [https://xrpl.org/amendments.html](https://xrpl.org/amendments.html) for the latest.

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

## MPTokenIssuanceSet Transaction

Creates or modifies an MPTokenIssuance.

```json
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rIssuerAddress",
  "MPTokenIssuanceID": "0000000000000000000000000000000000000000000000000000000000000001",
  "Flags": 3,  // mfMPTLocking (1) + mfMPTFreezing (2)
  "TransferFee": 50  // 0.5%
}
```

### Creating a New Issuance

```json
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rIssuerAddress",
  "AssetScale": 6,
  "MaximumAmount": "1000000000000000",
  "Flags": 1,
  "TransferFee": 100  // 1%
}
```

This creates a new MPTokenIssuance with:
- 6 decimal places
- 1 billion max supply (1,000,000,000,000,000 / 10^6)
- Locking support enabled
- 1% transfer fee

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

To create new tokens (increase supply):
1. Issuer calls `MPTokenIssuanceSet` with increased supply parameters
2. Or uses a specific mint transaction (depending on final spec)

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

As XLS-70 is still in draft/specification phase:

1. **Follow development**: Watch the XRPL spec repo for updates
2. **Testnet testing**: When available, experiment on testnet
3. **Library support**: Check `xrpl.js`, `xrpl-py` for MPToken support
4. **Implementation**: Be ready to implement when the amendment activates

## Resources

- [XLS-70 Specification](https://github.com/XRPLF/XRPL-Standards/discussions/70)
- [xrpl.org MPToken Docs](https://xrpl.org/docs/concepts/tokens/mptokens)
- XRPL Dev Blog for amendment status updates
