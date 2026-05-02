# XRPL Payments

## Overview

The `Payment` transaction type is the most fundamental operation on the XRP Ledger. It sends XRP or issued tokens from one account to another. The XRPL payment engine is sophisticated — it supports direct sends, pathfinding through multiple currencies, partial payments, and cross-currency conversions via the DEX.

## Payment Transaction Fields

### Common Fields (all transactions share these)

All transactions share standard fields. See the Transaction Format document for details.

### Payment-Specific Fields

| Field | Required | JSON Type | Description |
|---|---|---|---|
| `Amount` | ✅ | String or Object | Amount to deliver (XRP as string of drops, token as currency object) |
| `Destination` | ✅ | String | Address of the receiver |
| `DestinationTag` | ❌ | UInt32 | 32-bit tag for exchanges (acts as memo/destination identifier) |
| `InvoiceID` | ❌ | Hash256 | 256-bit hash for identifying a specific payment |
| `Paths` | ❌ | Array | Paths for cross-currency or rippled payments |
| `SendMax` | ❌ | String or Object | Maximum amount to send (required for partial/cross-currency payments) |
| `DeliverMin` | ❌ | String or Object | Minimum amount to deliver in the destination currency |
| `SourceTag` | ❌ | UInt32 | Tag identifying the payment source |

## Amount Formats

### XRP Amount

XRP amounts are specified as strings representing drops:

```json
{
  "Amount": "1000000"  // 1 XRP
}
```

1 XRP = 1,000,000 drops. The string format avoids JavaScript floating-point precision issues.

### Token (Issued Currency) Amount

Token amounts use an object with three fields:

```json
{
  "Amount": {
    "currency": "USD",
    "issuer": "r9cZA1mLK5R5Am25ArfXFmqgN1sV5f3gQR",
    "value": "100.50"
  }
}
```

- `currency`: 3-character ISO code or 40-hex-character hex code for non-standard currencies
- `issuer`: The XRPL address of the token issuer
- `value`: Decimal string representing the amount

For 40-hex currencies (like tokens with names > 3 characters), the currency code looks like:

```
"currency": "0158415500000000C1F76FF6ECB6BACF00000000"
```

## Direct XRP Payment

The simplest payment: sending XRP directly between two accounts.

### Example: Send 10 XRP

```json
{
  "TransactionType": "Payment",
  "Account": "r9cZA1mLK5R5Am25ArfXFmqgN1sV5f3gQR",
  "Destination": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
  "Amount": "10000000",
  "Fee": "10",
  "Sequence": 15,
  "Flags": 0
}
```

### Python Example

```python
from xrpl.transaction import submit_and_wait
from xrpl.models.transactions import Payment
from xrpl.utils import xrp_to_drops

payment = Payment(
    account="r9cZA1mLK5R5Am25ArfXFmqgN1sV5f3gQR",
    destination="rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
    amount=xrp_to_drops(10),
)
response = submit_and_wait(payment, client, wallet)
```

### JavaScript Example

```javascript
const { Payment } = require('xrpl');

const payment = {
  TransactionType: 'Payment',
  Account: 'r9cZA1mLK5R5Am25ArfXFmqgN1sV5f3gQR',
  Destination: 'rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh',
  Amount: xrpl.xrpToDrops(10),
};
const response = await client.submitAndWait(payment, { wallet });
```

## Direct Token Payment

Sending issued tokens (e.g., USD issued by Gateway) directly to an account that has a trust line for that token.

### Example: Send 50 USD

```json
{
  "TransactionType": "Payment",
  "Account": "r9cZA1mLK5R5Am25ArfXFmqgN1sV5f3gQR",
  "Destination": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
  "Amount": {
    "currency": "USD",
    "issuer": "rKiCet8SfE9T3zF3i1gXzT6YLuYQnXqXr",
    "value": "50"
  },
  "Fee": "10",
  "Sequence": 16
}
```

**Important:** For direct token payments, the `issuer` in the `Amount` field is the token issuer — but the actual tokens being sent come from the sender's trust line with that issuer. The `Destination` must have a trust line to the same issuer.

## Rippling Through Trust Lines

The XRPL can route payments through connected trust lines. For example, if A→B has a trust line for USD and B→C has a trust line for USD, a payment from A to C of USD automatically uses B as an intermediary.

```json
{
  "TransactionType": "Payment",
  "Account": "rA",
  "Destination": "rC",
  "Amount": {
    "currency": "USD",
    "issuer": "rIssuer",
    "value": "100"
  },
  "Paths": [
    [
      {
        "account": "rB",
        "type": 1,
        "type_hex": "0000000000000001"
      }
    ]
  ]
}
```

The intermediary (rB in this case) must have `lsfDefaultRipple` enabled or have `lsfNoRipple` disabled on the relevant trust lines for rippling to work.

## Partial Payments

A partial payment sends as much as possible up to a limit, delivering less than the full amount. This is used for returned payments or "refunds." The sender specifies `SendMax` (what they're willing to spend) and `DeliverMin` (the minimum they'll accept delivering).

### Flag: tfPartialPayment (0x00020000)

```json
{
  "TransactionType": "Payment",
  "Account": "r9cZA1mLK5R5Am25ArfXFmqgN1sV5f3gQR",
  "Destination": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
  "Amount": "1000000",
  "DeliverMin": "500000",
  "SendMax": "2000000",
  "Flags": 131072  // tfPartialPayment
}
```

**Security Warning:** Always check `delivered_amount` in the transaction metadata, not the `Amount` field from the request. A partial payment can appear to deliver more than it actually does if you only check the request fields. This is the basis of the infamous "payshaas" attack.

### Detecting Partial Payments

In transaction metadata:
- If `PartialPayment` flag is set in the metadata, it was a partial payment
- The `delivered_amount` field contains the actual amount delivered

## Cross-Currency Payments

The XRPL can convert currencies through the built-in DEX. A cross-currency payment sends one currency and delivers another.

### Example: Pay 1 XRP, deliver 100 USD

```json
{
  "TransactionType": "Payment",
  "Account": "r9cZA1mLK5R5Am25ArfXFmqgN1sV5f3gQR",
  "Destination": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
  "Amount": {
    "currency": "USD",
    "issuer": "rIssuer",
    "value": "100"
  },
  "SendMax": "2000000",
  "Paths": [
    [
      {
        "currency": "USD",
        "issuer": "rIssuer",
        "type": 48,
        "type_hex": "0000000000000030"
      }
    ]
  ]
}
```

### Auto-Bridging Through XRP

The XRPL's auto-bridging feature finds routes through XRP to connect otherwise illiquid markets. If you want to send EUR and receive JPY and there are EUR/XRP and XRP/JPY order books, the payment engine automatically bridges through XRP.

## Pathfinding

The `Paths` field specifies a set of payment paths. Each path is an array of path steps. Path steps can be:

- **Type 1 (Account step)**: Payment goes through an intermediary account
- **Type 48 (Currency step)**: Payment converts to a different currency at this point
- **Type 49 (Currency+Issuer step)**: Payment converts to a specific issuer's currency

### Ripple Path Find

Use the `ripple_path_find` RPC to discover available paths:

```json
{
  "method": "ripple_path_find",
  "params": [{
    "source_account": "r9cZA1mLK5R5Am25ArfXFmqgN1sV5f3gQR",
    "destination_account": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
    "destination_amount": {
      "currency": "USD",
      "issuer": "rIssuer",
      "value": "100"
    }
  }]
}
```

## Payment Flags

| Flag Name | Hex Value | Decimal | Description |
|---|---|---|---|
| `tfCanCrossCurrency` | 0x00040000 | 262144 | Allow cross-currency payment (implicitly set when needed) |
| `tfLimitQuality` | 0x00010000 | 65536 | Only take offers of equal or better quality |
| `tfNoDirectRipple` | 0x00020000 | 131072 | **DEPRECATED** — was used to force indirect rippling paths; do not use in new transactions |
| `tfPartialPayment` | 0x00020000 | 131072 | Allow the payment to deliver **less than the full `Amount`**; sender spends up to `SendMax`, recipient receives what actually arrives. Check `delivered_amount` in metadata, never `Amount`. |

**Note on flag values:** `tfNoDirectRipple` (deprecated) and `tfPartialPayment` share hex value 0x00020000. Use `tfPartialPayment` only. The semantic meaning is determined by context in modern rippled — `tfNoDirectRipple` is no longer meaningful and should be omitted.

## Memos

Memos attach arbitrary data to a payment (up to ~1KB total):

```json
{
  "TransactionType": "Payment",
  "Account": "r9cZA1mLK5R5Am25ArfXFmqgN1sV5f3gQR",
  "Destination": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
  "Amount": "1000000",
  "Memos": [
    {
      "Memo": {
        "MemoData": "726566756E64207061796D656E74",
        "MemoType": "72726561736F6E",
        "MemoFormat": "746578742F706C61696E"
      }
    }
  ]
}
```

All memo fields are hex-encoded strings (hex-encoded ASCII):
- `MemoData`: The actual payload
- `MemoType`: Describes what the memo contains
- `MemoFormat`: MIME type (optional, defaults to text/plain)

## Multi-Signing Requirements

Payments can be multi-signed if the account has a SignerList and the master key is disabled. See the Multi-Signing document for details on constructing multi-signed payments.

## Delivered Amount in Responses

When a payment is sent, always check metadata for the actual delivered amount:

```json
{
  "meta": {
    "delivered_amount": "1000000"
  }
}
```

For XRP payments, `delivered_amount` is a string of drops. For token payments, it's a currency object.

## Common Scenarios

### 1. Create Account (Fund New Address)

```json
{
  "TransactionType": "Payment",
  "Account": "rExisting",
  "Destination": "rNewAddress",
  "Amount": "20000000"  // 20 XRP
}
```

### 2. Refund with Partial Payment

```json
{
  "TransactionType": "Payment",
  "Account": "rOriginalSender",
  "Destination": "rReturnTo",
  "Amount": "5000000",
  "SendMax": "10000000",
  "DeliverMin": "1000000",
  "Flags": 131072
}
```

### 3. Payment with InvoiceID for Reconciliation

```json
{
  "TransactionType": "Payment",
  "Account": "r9cZA1mLK5R5Am25ArfXFmqgN1sV5f3gQR",
  "Destination": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
  "Amount": "10000000",
  "InvoiceID": "2B3E4F5E6A7B8C9D0E1F2A3B4C5D6E7F8A9B0C1D2E3F4A5B6C7D8E9F0A1B2C"
}
```

---

## Related Files

- `knowledge/01-xrpl-accounts.md` — sender/receiver account fundamentals
- `knowledge/03-xrpl-trustlines.md` — token payments and rippling
- `knowledge/04-xrpl-dex.md` — cross-currency payments via DEX
- `knowledge/19-xrpl-transaction-costs.md` — fee + reserve mechanics
- `knowledge/52-xrpl-l1-reference.md` — Payment field reference
