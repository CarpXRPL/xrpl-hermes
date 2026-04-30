# XRPL Escrow

## Overview

The XRPL escrow mechanism (enabled via the `Escrow` amendment) allows accounts to lock XRP and release it to a specified destination after a certain time or when a cryptographic condition is met. This is comparable to hash timelock contracts (HTLCs) in other blockchain systems, but integrated directly into the XRP Ledger protocol.

## Use Cases

- **Scheduled payments**: Lock XRP now, release on a future date
- **Atomic swaps**: Exchange XRP for tokens on another chain using crypto-conditions
- **Payment channels**: Create channel-like structures between parties
- **Conditional grants**: Release funds only when a secret is revealed
- **Time-locked inheritance**: Funds become available to heirs after a deadline

## EscrowCreate Transaction

Locks XRP into an escrow. The sender's XRP balance decreases by the amount, and the escrow holds it until released.

### Fields

| Field | Required | JSON Type | Description |
|---|---|---|---|
| `Destination` | ✅ | String | Recipient address when escrow finishes |
| `Amount` | ✅ | String | Amount of XRP to lock (in drops) |
| `FinishAfter` | ❌ | UInt32 | Earliest ledger timestamp (seconds since 1/1/2000) when escrow can finish |
| `CancelAfter` | ❌ | UInt32 | Latest ledger timestamp when escrow expires |
| `Condition` | ❄ | String | Hex-encoded crypto-condition for release |
| `DestinationTag` | ❌ | UInt32 | Tag for the destination (exchange use) |

### Example: Time-Release Escrow

```json
{
  "TransactionType": "EscrowCreate",
  "Account": "rSenderAddress",
  "Destination": "rReceiverAddress",
  "Amount": "100000000",  // 100 XRP
  "FinishAfter": 791635710,  // Ripple timestamp (seconds since 2000-01-01)
  "CancelAfter": 791722110,
  "Fee": "10",
  "Sequence": 25
}
```

### Example: Condition-Based Escrow (HTLC)

```json
{
  "TransactionType": "EscrowCreate",
  "Account": "rSenderAddress",
  "Destination": "rReceiverAddress",
  "Amount": "100000000",
  "FinishAfter": 791635710,
  "Condition": "A0258020E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855810100",
  "CancelAfter": 791722110,
  "Fee": "10",
  "Sequence": 25
}
```

### Python Example

```python
from xrpl.transaction import submit_and_wait
from xrpl.models.transactions import EscrowCreate
from xrpl.utils import xrp_to_drops

escrow = EscrowCreate(
    account="rSenderAddress",
    destination="rReceiverAddress",
    amount=xrp_to_drops(100),
    finish_after=791635710,
    cancel_after=791722110,
    condition="A0258020E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855810100",
)
response = submit_and_wait(escrow, client, wallet)
```

## EscrowFinish Transaction

Releases XRP from an escrow to the destination. Can only be executed after `FinishAfter` time has passed and before `CancelAfter`.

### Fields

| Field | Required | JSON Type | Description |
|---|---|---|---|
| `Owner` | ✅ | String | The account that created the escrow |
| `OfferSequence` | ✅ | UInt32 | Sequence number of the EscrowCreate transaction |
| `Condition` | ❌ | String | The condition (must match the one set in EscrowCreate) |
| `Fulfillment` | ❌ | String | The fulfillment that satisfies the condition |

### Example: Finish Without Condition

```json
{
  "TransactionType": "EscrowFinish",
  "Account": "rReceiverAddress",  // Anyone can submit this
  "Owner": "rSenderAddress",
  "OfferSequence": 25,
  "Fee": "10"
}
```

### Example: Finish With Condition (Reveal Secret)

```json
{
  "TransactionType": "EscrowFinish",
  "Account": "rReceiverAddress",
  "Owner": "rSenderAddress",
  "OfferSequence": 25,
  "Condition": "A0258020E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855810100",
  "Fulfillment": "A0228020E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B80",
  "Fee": "10"
}
```

## EscrowCancel Transaction

Cancels an expired escrow and returns the XRP to the sender.

```json
{
  "TransactionType": "EscrowCancel",
  "Account": "rAnyAddress",  // Anyone can cancel an expired escrow
  "Owner": "rSenderAddress",
  "OfferSequence": 25,
  "Fee": "10"
}
```

## Crypto-Conditions

Crypto-conditions are the cryptographic building blocks that enable conditional escrows. They implement the IETF draft standard.

### Condition Types

| Type | Prefix | Description |
|---|---|---|
| **PREIMAGE-SHA-256** | 0x00 | Reveal a preimage (secret) that hashes to a given value |
| **PREFIX-SHA-256** | 0x0F | Hash of a prefix + message |
| **THRESHOLD-SHA-256** | 0x01 | M-of-N threshold of conditions |
| **RSA-SHA-256** | 0x02 | RSA signature verification |
| **ED25519-SHA-256** | 0x03 | Ed25519 signature verification |

### PREIMAGE-SHA-256 (Most Common)

This is the simplest and most commonly used condition type:

```
Condition = SHA-256(secret)
Fulfillment = secret
```

The receiver must reveal the original secret (preimage) to claim the escrow.

### Generating Conditions

Using the `crypto-conditions` library:

**Node.js:**
```javascript
const cc = require('five-bells-condition');

// Generate a PREIMAGE-SHA-256 condition
const condition = new cc.PreimageSha256();
const secret = Buffer.from('my_secret_value', 'utf8');
condition.setPreimage(secret);

const conditionUri = condition.getConditionUri();  // Condition to put on ledger
const fulfillment = condition.serializeFulfillment();  // Fulfillment to submit
```

**Python:**
```python
from crypto_conditions import PreimageSha256

condition = PreimageSha256()
condition.set_preimage(b'my_secret_value')

condition_uri = condition.get_condition_uri()
fulfillment = condition.serialize_fulfillment()
```

### Anatomy of a Condition

A condition in URI format:
```
cc:0:3:3GXfY7pnMqjVmWenY5ZJjQ:26
```

Broken down:
- `cc:` — Crypto-condition prefix
- `0:` — Version
- `3:` — Feature bits (indicates PREIMAGE-SHA-256)
- `3GXfY7pnMqjVmWenY5ZJjQ:` — Base64-encoded fingerprint
- `26` — Max fulfillment length

On the ledger, conditions are stored in binary format (hex-encoded):
```
A0258020E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855810100
```

This is the ASN.1 DER encoding of the condition.

## Escrow Lifecycle

### Time-Based Escrow

1. **Sender** creates escrow with `FinishAfter` timestamp
2. Escrow enters the ledger as a `SuspendedPayment` entry
3. At `FinishAfter`, any account can call `EscrowFinish`
4. XRP is transferred to `Destination`
5. If `CancelAfter` passes before finishing, any account can `EscrowCancel`
6. XRP returns to sender

### Condition-Based Escrow (HTLC)

1. **Sender** creates escrow with `Condition` and `FinishAfter`
2. **Receiver** monitors for the escrow
3. **Receiver** reveals the fulfillment (secret) in `EscrowFinish`
4. Protocol verifies the fulfillment satisfies the condition
5. XRP is transferred to `Destination`
6. If time runs out, sender cancels and reclaims XRP

## Atomic Swaps with Escrow

Escrows enable cross-ledger atomic swaps. Here's how a XRP ↔ BTC swap works:

1. **Alice** (has XRP, wants BTC) creates escrow with condition C1
2. **Bob** (has BTC, wants XRP) sees the escrow conditions
3. **Bob** creates an escrow/HTLC on Bitcoin with condition C1 (same condition hash)
4. **Alice** reveals the secret on Bitcoin to claim BTC
5. The secret revealed on Bitcoin is now public
6. **Bob** (or anyone) can use the same secret to fulfill the XRP escrow

This guarantees atomicity: either both swaps happen or neither does.

## Practical Example: Full HTLC Flow

### Step 1: Generate Condition

```javascript
const cc = require('five-bells-condition');
const crypto = require('crypto');

// Generate random 256-bit secret
const secret = crypto.randomBytes(32);

// Create condition
const cond = new cc.PreimageSha256();
cond.setPreimage(secret);

const conditionHex = cond.getConditionBinary().toString('hex').toUpperCase();
const fulfillmentHex = cond.serializeFulfillment().toString('hex').toUpperCase();

console.log('Secret:', secret.toString('hex'));
console.log('Condition:', conditionHex);
console.log('Fulfillment:', fulfillmentHex);
```

### Step 2: Create Escrow (Sender)

```json
{
  "TransactionType": "EscrowCreate",
  "Account": "rAlice",
  "Destination": "rBob",
  "Amount": "100000000",
  "FinishAfter": 791635710,
  "CancelAfter": 791722110,
  "Condition": "A0258020...",
  "Sequence": 30
}
```

### Step 3: Claim Escrow (Receiver)

```json
{
  "TransactionType": "EscrowFinish",
  "Account": "rBob",
  "Owner": "rAlice",
  "OfferSequence": 30,
  "Condition": "A0258020...",
  "Fulfillment": "A0228020..."
}
```

## Timestamp Format

XRPL uses **Ripple Epoch Time** (seconds since January 1, 2000, 00:00:00 UTC).

### Conversion

**Unix to Ripple:**
```
RippleTime = UnixTime - 946684800
```

**Ripple to Unix:**
```
UnixTime = RippleTime + 946684800
```

### JavaScript Conversion

```javascript
function unixToRipple(unixTimestamp) {
  return unixTimestamp - 946684800;
}

function rippleToUnix(rippleTimestamp) {
  return rippleTimestamp + 946684800;
}
```

## Reserve and Escrows

Each escrow created consumes 1 owner reserve unit (0.2 XRP). So:
- 5 escrows = 5 × 0.2 = 1 XRP locked as owner reserve
- Plus 1 XRP base reserve
- Total: 0.2 XRP locked

When an escrow finishes or is cancelled, the reserve is released back to the owner.

## Querying Escrows

### account_objects with Escrow Type

```json
{
  "method": "account_objects",
  "params": [{
    "account": "rSenderAddress",
    "type": "escrow"
  }]
}
```

### Response Example

```json
{
  "result": {
    "account": "rSenderAddress",
    "account_objects": [
      {
        "Amount": "100000000",
        "CancelAfter": 791722110,
        "Condition": "A0258020...",
        "Destination": "rReceiverAddress",
        "FinishAfter": 791635710,
        "LedgerEntryType": "Escrow",
        "Owner": "rSenderAddress",
        "PreviousTxnID": "ABCD...",
        "PreviousTxnLgrSeq": 12345,
        "index": "ABCDEF..."
      }
    ],
    "validated": true
  }
}
```

## Security Considerations

1. **Condition security**: Use a sufficiently random secret (at least 32 bytes of cryptographic randomness)
2. **Fulfillment expiration**: Always set both `FinishAfter` and `CancelAfter` to avoid funds being stuck
3. **Condition reuse**: Never reuse the same secret across different escrows
4. **Front-running**: Anyone can submit `EscrowFinish` once eligible — the receiver doesn't have to be the one to claim
5. **Cancel windows**: If `CancelAfter` passes, escrow can be cancelled even if the condition is satisfied

## Integration with Payment Channels

Escrows and payment channels serve different but complementary roles:

| Feature | Escrow | Payment Channel |
|---|---|---|
| Recipient | Specified at creation | Any valid claim |
| Claim process | On-chain EscrowFinish | Off-chain claim verification |
| Partial claims | No (all-or-nothing) | Yes (incremental claims) |
| Conditions | Crypto-conditions | Public key signature |
| Use case | Atomic swaps, one-time releases | Streaming, recurring payments |
