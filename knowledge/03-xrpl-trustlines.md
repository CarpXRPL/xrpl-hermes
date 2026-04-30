# XRPL Trust Lines

## Overview

A trust line (also called a "RippleState" in the ledger) represents the relationship between two accounts for a specific issued currency. Trust lines are the foundation of the XRPL's token system — every issued currency position is recorded as a balance on a trust line between two parties.

## What Is a Trust Line?

On the XRP Ledger, tokens called "issued currencies" are not native to the ledger like XRP. Instead, they exist as balances on **trust lines** — bilateral relationships between two accounts denominated in a specific currency.

When you hold USD issued by Gateway A, what actually exists on the ledger is a trust line between you and Gateway A with a positive balance on your side and a negative balance on Gateway A's side.

## TrustSet Transaction

Creating or modifying a trust line requires a `TrustSet` transaction.

### Fields

| Field | Required | JSON Type | Description |
|---|---|---|---|
| `LimitAmount` | ✅ | Object | The trust line parameters |
| `QualityIn` | ❌ | UInt32 | Value representing the quality of incoming balances (fee discount/v2) |
| `QualityOut` | ❌ | UInt32 | Value representing the quality of outgoing balances |

### LimitAmount Object

```json
{
  "currency": "USD",
  "issuer": "rIssuerAddress",
  "value": "1000000000"
}
```

- `currency`: 3-letter ISO code or 40-hex-character hex code
- `issuer`: The XRPL address of the counterparty (the token issuer)
- `value`: Maximum amount you are willing to trust them for (decimal string)

### Example: Create a Trust Line

```json
{
  "TransactionType": "TrustSet",
  "Account": "rUserAddress",
  "LimitAmount": {
    "currency": "USD",
    "issuer": "rGatewayAddress",
    "value": "10000"
  },
  "Fee": "10",
  "Sequence": 10,
  "Flags": 0
}
```

This creates a trust line between `rUserAddress` and `rGatewayAddress` for USD, with a limit of 10,000 USD. The user can now receive up to 10,000 USD from the gateway.

### Python Example

```python
from xrpl.transaction import submit_and_wait
from xrpl.models.transactions import TrustSet
from xrpl.models.amounts import IssuedCurrencyAmount

trustset = TrustSet(
    account="r9cZA1mLK5R5Am25ArfXFmqgN1sV5f3gQR",
    limit_amount=IssuedCurrencyAmount(
        currency="USD",
        issuer="rKiCet8SfE9T3zF3i1gXzT6YLuYQnXqXr",
        value="1000000",
    ),
)
response = submit_and_wait(trustset, client, wallet)
```

### JavaScript Example

```javascript
const { TrustSet } = require('xrpl');

const trustset = {
  TransactionType: 'TrustSet',
  Account: 'r9cZA1mLK5R5Am25ArfXFmqgN1sV5f3gQR',
  LimitAmount: {
    currency: 'USD',
    issuer: 'rKiCet8SfE9T3zF3i1gXzT6YLuYQnXqXr',
    value: '1000000',
  },
};
const response = await client.submitAndWait(trustset, { wallet });
```

## Trust Line Balance Tracking

A trust line balance is always a **signed** value — it can be positive or negative depending on perspective.

### Balance Examples

| Account A | Account B | A's Balance | B's Balance |
|---|---|---|---|
| rUser | rGateway | 500 USD (holds) | -500 USD (owes) |
| rGateway | rUser | -500 USD (owes) | 500 USD (holds) |
| rAlice | rBob | 100 EUR | -100 EUR |

The balance is from the perspective of the account that has the lower address (lexicographically). So when you look up trust lines, you'll see the balance field which might be negative or positive.

### Getting Trust Lines via RPC

```json
{
  "method": "account_lines",
  "params": [{
    "account": "r9cZA1mLK5R5Am25ArfXFmqgN1sV5f3gQR"
  }]
}
```

Response:

```json
{
  "result": {
    "account": "r9cZA1mLK5R5Am25ArfXFmqgN1sV5f3gQR",
    "lines": [
      {
        "account": "rKiCet8SfE9T3zF3i1gXzT6YLuYQnXqXr",
        "balance": "500",
        "currency": "USD",
        "limit": "1000000",
        "limit_peer": "0",
        "no_ripple": false,
        "no_ripple_peer": false,
        "quality_in": 0,
        "quality_out": 0
      }
    ]
  },
  "status": "success"
}
```

Fields in the response:
- `account`: The counterparty on the trust line
- `balance`: Current balance (from the requesting account's perspective)
- `currency`: The currency code
- `limit`: The limit set by the requesting account
- `limit_peer`: The limit set by the counterparty
- `no_ripple`: Whether rippling is disabled for this trust line (requesting account)
- `no_ripple_peer`: Whether rippling is disabled (counterparty)
- `quality_in`/`quality_out`: Exchange quality settings

## Trust Line Flags

Trust lines have their own flags stored in both the trust line entry and the account root.

### lsfNoRipple (0x00020000)

Disables rippling through this trust line. When set, the trust line cannot be used as an intermediary for payments between other parties.

- Set on individual trust lines to prevent that specific line from rippling
- When `lsfDefaultRipple` is enabled on the account, new trust lines have rippling enabled by default
- Setting `lsfNoRipple` on a trust line overrides the account-level default

### lsfLowAuth and lsfHighAuth

These flags track authorization status. They come in two variants because each trust line has two sides ("low" and "high" based on which address is lexicographically lower).

### lsfLowFreeze and lsfHighFreeze

Freeze flags on a trust line. When an issuer freezes a trust line, the account on that end cannot transfer the tokens.

### lsfLowDeepFreeze and lsfHighDeepFreeze

Deep freeze is a stronger form of freeze (introduced in XLS-67) that prevents any movement of the frozen asset.

## Rippling

Rippling is the mechanism by which tokens flow through multiple trust lines to enable payments between parties who don't have a direct trust line.

### How Rippling Works

```
Alice (100 USD) → Bob (0 USD) → Charlie (0 USD)
```

If Alice wants to send 50 USD to Charlie:
1. Alice's balance with Bob decreases by 50 USD
2. Bob's balance with Charlie decreases by 50 USD
3. Alice now has 50 USD owed to Bob, Bob now has 50 USD owed to Charlie
4. Effectively, Charlie receives 50 USD

### Requiring DefaultRipple

For an issuer's tokens to be transferred between holders, the issuer **must** have `lsfDefaultRipple` enabled. Without it, trust lines are created with rippling disabled by default, preventing token transferability.

**This is the #1 mistake** new token issuers make — tokens are minted but cannot be transferred because `lsfDefaultRipple` was never set.

### No-Ripple Flags

Accounts can prevent their trust lines from being used as ripple paths:

1. **Account-level**: `lsfDefaultRipple` flag (enables rippling by default on new trust lines)
2. **Trust-line-level**: `lsfNoRipple` flag (disables rippling on a specific trust line)

When an account has NOT set `lsfDefaultRipple`, all its trust lines effectively have `lsfNoRipple` enabled, so tokens don't ripple through that account.

## Auth Trust Lines

When an issuer sets `lsfRequireAuth` on their account, trust lines must be **pre-authorized** before they can hold the issuer's tokens.

### Authorization Flow

1. User creates a trust line to the issuer (with a limit)
2. Issuer sends a `TrustSet` transaction with the same trust line to authorize it
3. The trust line's authorization flag is set
4. User can now receive and hold the issuer's tokens

### Authorization via TrustSet

```json
{
  "TransactionType": "TrustSet",
  "Account": "rIssuerAddress",
  "LimitAmount": {
    "currency": "USD",
    "issuer": "rUserAddress",
    "value": "0"
  },
  "Flags": 65536  // tfSetAuth
}
```

The `tfSetAuth` flag (0x00010000) authorizes a trust line without changing the limit.

## Freezing Trust Lines

Issuers can freeze trust lines to prevent transfers of their tokens:

### lsfGlobalFreeze

Freezes ALL trust lines for the issuer's tokens. No transfers can occur among any holders.

```json
{
  "TransactionType": "AccountSet",
  "Account": "rIssuerAddress",
  "SetFlag": 6  // lsfGlobalFreeze
}
```

### lsfNoFreeze

Permanently gives up the ability to freeze. **IRREVERSIBLE.**

```json
{
  "TransactionType": "AccountSet",
  "Account": "rIssuerAddress",
  "SetFlag": 5  // lsfNoFreeze
}
```

### Individual Trust Line Freeze

Set the freeze flag on a specific trust line (requires `lsfGlobalFreeze` not to be set, and `lsfNoFreeze` not to be set).

```json
{
  "TransactionType": "TrustSet",
  "Account": "rIssuerAddress",
  "LimitAmount": {
    "currency": "USD",
    "issuer": "rFrozenUser",
    "value": "0"
  },
  "Flags": 1048576  // tfSetFreeze
}
```

## Trust Line Graph

The XRPL's trust line network forms a directed graph where:
- Nodes are accounts
- Edges are trust lines with currency, limit, and balance information
- The graph is traversed by the payment engine to find paths

### Graph Properties

- Trust lines are **bilateral**: both parties must agree
- Positive balance on one side = negative balance on the other
- The graph is currency-specific (a trust line for USD is separate from a trust line for EUR)
- Paths can cross through multiple intermediaries

### Account Objects

Each trust line is an account object. The account that creates the trust line incurs the owner reserve cost (0.2 XRP per trust line). However, **both** sides of the trust line may incur the reserve cost depending on who created the trust line entry.

In practice:
- If User A creates a trust line to Issuer B, User A pays the 0.2 XRP reserve
- If Issuer B later modifies it (authorizing), Issuer B also pays a reserve for the modified entry

## Trust Line Lifecycle

1. **Created**: User sends `TrustSet` to create a trust line with a limit. Reserve (0.2 XRP) is locked by the user.
2. **Active**: Tokens flow through the trust line. Balance fluctuates.
3. **Modified**: Either party can modify the trust line (change limit, set flags).
4. **Deleted**: The trust line can be removed when its balance is 0 and any limit is removed (limit set to 0).

### Removing a Trust Line

Send a `TrustSet` with limit value `0`:

```json
{
  "TransactionType": "TrustSet",
  "Account": "rUserAddress",
  "LimitAmount": {
    "currency": "USD",
    "issuer": "rGatewayAddress",
    "value": "0"
  }
}
```

The trust line is removed when:
- Balance is exactly 0
- Limit is 0
- Both sides have no flags set

## Reserve and Trust Lines

Each trust line an account owns consumes 0.2 XRP of owner reserve. For a typical user with 10 trust lines, that's 1 XRP (base) + 2 XRP (10 × 0.2) = 3 XRP locked.

**Optimization:** Only create trust lines for tokens you actually intend to hold or trade. Clean up unused trust lines by setting limit to 0.

## Non-Standard Currencies

Currencies with names longer than 3 characters use a 40-character hex representation:

- "HEX" values: `"0158415500000000C1F76FF6ECB6BACF00000000"`
- The first 8 hex chars contain metadata about the currency code
- The remaining 32 hex chars encode the actual currency name (up to 160 bits)

These are commonly used for:
- XLS-20 NFT LP tokens
- AMM LP tokens
- Custom token names
- Any currency code not in the standard 3-letter ISO set
