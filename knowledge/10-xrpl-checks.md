# XRPL Checks

## Overview

Checks on the XRP Ledger are deferred payment instruments. A sender creates a check that authorizes a specific receiver to claim a specific amount of XRP or tokens. The receiver can then cash the check at any time before it expires. This is similar to a paper check in traditional finance — the check writer authorizes the payment, and the recipient deposits it when they choose.

## Use Cases

- **Authorized payments**: Pre-authorize a payment without executing it immediately
- **Deferred settlement**: Create a check now, cash it later when conditions are met
- **Payment guarantees**: Provide proof of authorization without transferring funds
- **Escrow alternative**: Simpler than escrow for non-time-sensitive cases
- **Expense approvals**: Approve a payment that gets cashed at a specific time

## CheckCreate Transaction

Creates a new check that the destination can cash later.

### Fields

| Field | Required | JSON Type | Description |
|---|---|---|---|
| `Destination` | ✅ | String | Who can cash the check |
| `SendMax` | ✅ | String or Object | Maximum amount the check sender authorizes (XRP or token) |
| `Expiration` | ❌ | UInt32 | Ledger sequence when the check expires |
| `DestinationTag` | ❌ | UInt32 | Tag for the destination (exchange use) |
| `InvoiceID` | ❌ | Hash256 | Optional identifier for the check |

### Example: Create XRP Check

```json
{
  "TransactionType": "CheckCreate",
  "Account": "rSenderAddress",
  "Destination": "rReceiverAddress",
  "SendMax": "10000000",  // 10 XRP
  "Expiration": 791635710,
  "Fee": "10",
  "Sequence": 20
}
```

### Example: Create Token Check

```json
{
  "TransactionType": "CheckCreate",
  "Account": "rSenderAddress",
  "Destination": "rReceiverAddress",
  "SendMax": {
    "currency": "USD",
    "issuer": "rIssuerAddress",
    "value": "1000"
  },
  "Expiration": 791635710,
  "Fee": "10",
  "Sequence": 20
}
```

### Python Example

```python
from xrpl.transaction import submit_and_wait
from xrpl.models.transactions import CheckCreate
from xrpl.utils import xrp_to_drops
from xrpl.models.amounts import IssuedCurrencyAmount

# XRP check
check = CheckCreate(
    account="rSenderAddress",
    destination="rReceiverAddress",
    send_max=xrp_to_drops(10),
    expiration=791635710,
)
response = submit_and_wait(check, client, wallet)
```

## CheckCash Transaction

The destination cashes the check to receive the funds.

### Fields

| Field | Required | JSON Type | Description |
|---|---|---|---|
| `CheckID` | ✅ | String | The ID of the check to cash |
| `Amount` | ❌ | String or Object | Exact amount to cash (for fixed-amount checks) |
| `DeliverMin` | ❌ | String or Object | Minimum amount to accept (for variable-amount checks) |

You must specify either `Amount` (exact) or `DeliverMin` (minimum) depending on the check type.

### Example: Cash Full Amount

```json
{
  "TransactionType": "CheckCash",
  "Account": "rReceiverAddress",
  "CheckID": "49647F0D748DC3FE26BDACBC57F251AADEFFF391403EC9BF87C97F67E9977FB0",
  "Amount": "10000000",  // Cash exactly 10 XRP
  "Fee": "10",
  "Sequence": 30
}
```

### Example: Cash with Minimum (Token Check)

```json
{
  "TransactionType": "CheckCash",
  "Account": "rReceiverAddress",
  "CheckID": "49647F0D748DC3FE26BDACBC57F251AADEFFF391403EC9BF87C97F67E9977FB0",
  "DeliverMin": {
    "currency": "USD",
    "issuer": "rIssuerAddress",
    "value": "500"
  },
  "Fee": "10",
  "Sequence": 30
}
```

### Important Rules

- Only the `Destination` specified in the `CheckCreate` can cash the check
- The check must not have expired
- The sender must have sufficient balance (XRP or token trust line) when cashing
- For token checks, the destination must have a trust line to the issuer

## CheckCancel Transaction

Cancels a check before it's cashed. Either the sender or the destination can cancel it.

```json
{
  "TransactionType": "CheckCancel",
  "Account": "rSenderAddress",
  "CheckID": "49647F0D748DC3FE26BDACBC57F251AADEFFF391403EC9BF87C97F67E9977FB0",
  "Fee": "10"
}
```

## Check Lifecycle

```
                    ┌─────────────┐
                    │  Created    │  (CheckCreate)
                    └──────┬──────┘
                           │
                           ├─────────────────┐
                           │                 │
                    ┌──────▼──────┐  ┌───────▼──────┐
                    │   Cashed    │  │   Expired    │
                    │ (CheckCash) │  │ (time passes) │
                    └──────┬──────┘  └───────┬──────┘
                           │                 │
                           │         ┌───────▼──────┐
                           │         │   Cancelled  │
                           │         │(CheckCancel) │
                           │         └──────┬───────┘
                           │                │
                           └────────────────┘
                      Check removed from ledger
```

### States

1. **Created**: Check is in the ledger as a `Check` object. Reserve locked.
2. **Cashed**: Check has been cashed. Funds transferred. Check removed.
3. **Cancelled**: Check creator or destination cancelled it. Check removed.
4. **Expired**: Check's expiration time passed. Can be cancelled by anyone.

## Check ID

Each check gets a unique ID derived from:
```
CheckID = SHA-512Half(
    CheckCreate sender address +
    CheckCreate sequence number
)
```

You can find the CheckID by looking up the check object on the ledger using `account_objects`.

## Finding Checks

### account_objects with Check Type

```json
{
  "method": "account_objects",
  "params": [{
    "account": "rSenderAddress",
    "type": "check"
  }]
}
```

### Response

```json
{
  "result": {
    "account": "rSenderAddress",
    "account_objects": [
      {
        "LedgerEntryType": "Check",
        "Account": "rSenderAddress",
        "Destination": "rReceiverAddress",
        "SendMax": "10000000",
        "Expiration": 791635710,
        "DestinationNode": "0",
        "SourceNode": "0",
        "PreviousTxnID": "ABCD...",
        "PreviousTxnLgrSeq": 12345,
        "index": "49647F0D748DC3FE26BDACBC57F251AADEFFF391403EC9BF87C97F67E9977FB0"
      }
    ],
    "validated": true
  }
}
```

## Reserve and Checks

Each check the sender creates consumes 1 owner reserve unit (0.2 XRP). The destination does NOT pay a reserve for checks made out to them.

**Optimization:** Cancel expired or unwanted checks promptly to free up reserve.

For an account with 10 checks: 10 XRP (base) + 20 XRP (10 × 2) = 30 XRP locked.

## Checks vs Other Payment Methods

| Feature | Check | Direct Payment | Escrow | Payment Channel |
|---|---|---|---|---|
| Sender control | Full (can cancel) | None after send | Timed release | Incremental |
| Receiver action | Must cash | Receives immediately | Must finish | Must claim |
| Expiration | Optional | No | Yes | Yes |
| Partial payment | Must be exact | Yes | No | Yes |
| Use case | Deferred pay | Immediate | Conditional | Streaming |

## Practical Scenarios

### Scenario 1: Subscription Payment

Alice wants to authorize recurring payments to Bob, but doesn't want to give Bob her keys:
1. She creates a check for 100 USD each month
2. Bob cashes it when payment is due
3. If Alice needs to stop, she cancels the check before Bob cashes it

### Scenario 2: Payment Proof

Alice needs to prove she can pay Bob before a contract is signed:
1. Alice creates a check for 10,000 XRP to Bob
2. Bob can verify the check exists on the ledger
3. Both parties sign the contract
4. Bob cashes the check

### Scenario 3: Delayed Settlement

Alice owes Bob money but wants to delay the actual transfer:
1. Alice creates a check with a future expiration
2. Bob holds the check (doesn't cash immediately)
3. Bob cashes it when he needs the funds

## Replacing Checks with Payment Channels

For recurring payments, payment channels are often better than checks:

| Aspect | Check | Payment Channel |
|---|---|---|
| Setup | One CheckCreate per payment | One channel, many claims |
| Reserve | 2 XRP per check (one-time) | ~2 XRP per channel (ongoing) |
| Cost | One transaction per payment | One claim (off-chain) per payment |
| Streaming | No | Yes |
| Trust | Requires trust to cancel | Trustless incremental claims |

For streaming or high-frequency payments, prefer payment channels. For occasional deferred payments, checks work well.

## Security Considerations

1. **Sender balance**: Check sender must have sufficient funds AT THE TIME OF CASHING, not at creation
2. **Expiration always**: Always set an expiration to prevent indefinite liability
3. **Cancel promptly**: If you no longer want a check to be cashed, cancel it immediately
4. **Check IDs**: Store or compute Check IDs for efficient lookup
5. **Token checks**: Ensure destination has the appropriate trust line before creating
