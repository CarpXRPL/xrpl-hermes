# XRPL Payment Channels

## Overview

Payment channels enable fast, low-cost off-chain micropayments between two parties. The payer creates a channel, funds it with XRP, then sends signed claims off-chain. The recipient can redeem claims on-ledger at any time up to channel expiry. Ideal for streaming payments, metered APIs, gaming, and IoT.

---

## Lifecycle

```
Payer                         Recipient
  |                               |
  |-- PaymentChannelCreate -----> |  (on-ledger: channel created)
  |                               |
  |-- Claim (off-chain, signed) ->|  (repeated many times)
  |-- Claim (off-chain, signed) ->|
  |-- Claim (off-chain, signed) ->|
  |                               |
  |                    |-- PaymentChannelClaim (redeem best claim)
  |                               |
  |-- PaymentChannelFund -------> |  (optional: add more XRP)
  |                               |
  |-- PaymentChannelClose ------> |  (request close / expire)
  |                               |
  |           [channel expires]   |
  |                               |
  |  Unclaimed XRP returned to payer
```

---

## 1. PaymentChannelCreate

```json
{
  "TransactionType": "PaymentChannelCreate",
  "Account": "rPAYER...",
  "Destination": "rRECIPIENT...",
  "Amount": "1000000",
  "SettleDelay": 86400,
  "PublicKey": "ED...payer_public_key_hex...",
  "CancelAfter": 1893456000,
  "DestinationTag": 1234,
  "Fee": "12",
  "Sequence": 42
}
```

| Field | Description |
|-------|-------------|
| `Amount` | XRP (in drops) to fund the channel |
| `SettleDelay` | Seconds after close request before channel can be closed |
| `PublicKey` | Payer's public key (hex) used to verify claims |
| `CancelAfter` | Optional hard expiry (Ripple Epoch seconds) |
| `DestinationTag` | Optional tag for recipient routing |

**Ripple Epoch**: Unix time minus 946684800 (Jan 1 2000 00:00:00 UTC).

```python
import time
ripple_epoch = int(time.time()) - 946684800
cancel_after = ripple_epoch + (30 * 24 * 3600)  # 30 days from now
```

---

## 2. Reading Channel State

After creation, find the channel object:

```python
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountChannels

client = JsonRpcClient("https://xrplcluster.com")

resp = client.request(AccountChannels(
    account="rPAYER...",
    destination_account="rRECIPIENT..."
))

channel = resp.result["channels"][0]
channel_id = channel["channel_id"]
print(f"Channel ID: {channel_id}")
print(f"Amount: {channel['amount']} drops")
print(f"Balance: {channel['balance']} drops")
print(f"Settle Delay: {channel['settle_delay']}s")
```

Response fields:
- `channel_id`: 64-char hex, used in claims and transactions
- `amount`: total XRP funded
- `balance`: XRP already claimed by recipient
- `expiration`: set once close is requested

---

## 3. Creating and Signing Claims (Off-Chain)

Claims are signed messages authorizing a cumulative payment. Each new claim should be for the total cumulative amount (not incremental).

### Python (xrpl-py)

```python
import xrpl
from xrpl.core.keypairs import sign
from xrpl.core.binarycodec import encode_for_signing_claim

# channel_id: 64-char hex string
# amount: cumulative drops authorized
def create_claim(channel_id: str, amount: int, private_key: str) -> str:
    claim_bytes = encode_for_signing_claim({
        "channel": channel_id,
        "amount": str(amount)
    })
    signature = sign(claim_bytes, private_key)
    return signature

# Example — load private key from environment variable, never hardcode
import os
channel_id = "A5A9F7C0..."  # from channel lookup
private_key = os.environ["PAYER_PRIVATE_KEY"]  # set in env: export PAYER_PRIVATE_KEY=ED...

sig_1000 = create_claim(channel_id, 1000, private_key)
sig_5000 = create_claim(channel_id, 5000, private_key)
sig_9999 = create_claim(channel_id, 9999, private_key)
```

### JavaScript (xrpl.js)

```javascript
const xrpl = require('xrpl');

function createClaim(channelId, amountDrops, wallet) {
  const message = xrpl.hashPaymentChannel(
    wallet.address,
    destination,
    amountDrops,
    channelId
  );
  return wallet.sign(message);
}
```

### Verifying a Claim

Before redeeming, the recipient should verify:

```python
from xrpl.core.keypairs import is_valid_message
from xrpl.core.binarycodec import encode_for_signing_claim

def verify_claim(channel_id: str, amount: int, signature: str, public_key: str) -> bool:
    claim_bytes = encode_for_signing_claim({
        "channel": channel_id,
        "amount": str(amount)
    })
    return is_valid_message(claim_bytes, bytes.fromhex(signature), public_key)
```

---

## 4. PaymentChannelClaim (Redeem)

Recipient submits the best claim to the ledger:

```json
{
  "TransactionType": "PaymentChannelClaim",
  "Account": "rRECIPIENT...",
  "Channel": "A5A9F7C0...",
  "Balance": "9999",
  "Amount": "9999",
  "Signature": "3045...",
  "PublicKey": "ED...payer_public_key_hex...",
  "Fee": "12",
  "Sequence": 10
}
```

| Field | Description |
|-------|-------------|
| `Channel` | Channel ID from PaymentChannelCreate |
| `Balance` | Cumulative drops to redeem (channel `balance` after this tx) |
| `Amount` | Same as Balance for full redemption |
| `Signature` | Payer's claim signature |
| `PublicKey` | Payer's public key |

Flags:
- `tfRenew` (0x00010000): Renew expiration if channel has one set
- `tfClose` (0x00020000): Request channel close after claim

---

## 5. PaymentChannelFund (Add Funds)

```json
{
  "TransactionType": "PaymentChannelFund",
  "Account": "rPAYER...",
  "Channel": "A5A9F7C0...",
  "Amount": "500000",
  "Expiration": 1893456000,
  "Fee": "12",
  "Sequence": 43
}
```

- Only the channel creator can fund
- Extends or sets the expiration
- Recipient can still claim previously signed claims

---

## 6. Closing a Channel

### Payer initiates close:

```json
{
  "TransactionType": "PaymentChannelClaim",
  "Account": "rPAYER...",
  "Channel": "A5A9F7C0...",
  "Flags": 131072,
  "Fee": "12",
  "Sequence": 44
}
```

- `Flags: 131072` = `tfClose` (0x00020000)
- Channel won't close immediately; `SettleDelay` must pass
- Recipient can still claim during settle delay

### Recipient claims and closes simultaneously:

```json
{
  "TransactionType": "PaymentChannelClaim",
  "Account": "rRECIPIENT...",
  "Channel": "A5A9F7C0...",
  "Balance": "9999",
  "Amount": "9999",
  "Signature": "3045...",
  "PublicKey": "ED...",
  "Flags": 131072,
  "Fee": "12",
  "Sequence": 11
}
```

---

## 7. Channel Expiry Rules

```
expiration = max(close_request_time + SettleDelay, CancelAfter)
```

- Once expired, anyone can submit PaymentChannelClaim with `tfClose` to close it
- Unclaimed XRP returns to payer automatically
- CancelAfter is absolute; SettleDelay is relative to close request

---

## 8. Streaming Payments Pattern

High-frequency off-chain payment stream:

```python
import asyncio
from dataclasses import dataclass

@dataclass
class StreamState:
    channel_id: str
    public_key: str
    private_key: str
    cumulative_drops: int = 0
    best_claim_sig: str = ""
    unit_price_drops: int = 10  # per API call / per second

async def send_payment_unit(state: StreamState):
    state.cumulative_drops += state.unit_price_drops
    sig = create_claim(state.channel_id, state.cumulative_drops, state.private_key)
    state.best_claim_sig = sig
    return {
        "channel_id": state.channel_id,
        "amount": state.cumulative_drops,
        "signature": sig,
        "public_key": state.public_key
    }

async def streaming_api_client(state: StreamState, num_requests: int):
    for i in range(num_requests):
        claim = await send_payment_unit(state)
        # Send claim over HTTP/WebSocket to service provider
        # Provider verifies claim before serving response
        await make_api_request(claim)
        await asyncio.sleep(0.1)

    # At end, provider redeems final claim on-ledger
    print(f"Total paid: {state.cumulative_drops} drops")
```

---

## 9. PaymentChannel Object on Ledger

```json
{
  "LedgerEntryType": "PayChannel",
  "Account": "rPAYER...",
  "Destination": "rRECIPIENT...",
  "Amount": "1000000",
  "Balance": "9999",
  "PublicKey": "ED...",
  "SettleDelay": 86400,
  "CancelAfter": 1893456000,
  "Expiration": 1780000000,
  "DestinationTag": 1234,
  "index": "A5A9F7C0..."
}
```

---

## 10. Use Cases

| Use Case | SettleDelay | Notes |
|----------|-------------|-------|
| Streaming video | 60–300s | Per-second micropayments |
| Metered API access | 3600s | Per-request claims |
| Gaming (in-game transactions) | 86400s | Long session |
| IoT device billing | 86400s | Low-value, high-frequency |
| B2B invoice streaming | 604800s | Weekly settlement |

---

## 11. Security Considerations

- Always use cumulative amounts in claims (recipient keeps best claim)
- Payer should track cumulative amounts off-chain
- Recipient should verify signature before serving
- Set `CancelAfter` to prevent indefinitely locked funds
- Monitor channel balance vs amount funded
- Use `SettleDelay` long enough for recipient to claim before payer closes
