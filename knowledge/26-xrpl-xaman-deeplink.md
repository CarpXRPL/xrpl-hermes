# XRPL Xaman Deep-Link & Signing

## Overview

Xaman (formerly XUMM) is the leading XRPL mobile wallet. It provides a signing infrastructure via its API: apps submit "payloads" (transaction templates), users scan QR codes, sign in Xaman, and the signed result is returned to the app. Supports push notifications, WebSocket callbacks, and deep links.

---

## 1. Xaman API Overview

```
App Backend
    │
    ├─► POST /payload          (create signing request)
    │       │
    │       └─► Returns: payload_uuid, qr_png, deep_link, ws_url
    │
    ├─► QR code shown to user
    │
    │       User scans with Xaman → reviews → signs
    │
    ├─► WebSocket /payload/{uuid}/subscribe (real-time updates)
    │
    └─► GET /payload/{uuid}    (check signed result)
```

Base URL: `https://xumm.app/api/v1/platform`
SDK: `xumm-sdk` (Node.js) or `xumm-py` (Python)

---

## 2. Xaman SDK Setup

### Node.js

```bash
npm install xumm-sdk
```

```javascript
const { Xumm } = require('xumm-sdk');

const xumm = new Xumm('YOUR_API_KEY', 'YOUR_API_SECRET');
```

### Python

```bash
pip install xumm-sdk
```

```python
from xumm import XummSdk

sdk = XummSdk(api_key="YOUR_API_KEY", api_secret="YOUR_API_SECRET")
```

Get API keys from: `https://apps.xumm.dev`

---

## 3. Creating a Payload (Signing Request)

### Python

```python
from xumm import XummSdk
from xumm.model.payload import XummPostPayloadBodyJson

sdk = XummSdk(api_key="...", api_secret="...")

# Payment request
payload = await sdk.payload.create(
    XummPostPayloadBodyJson(
        txjson={
            "TransactionType": "Payment",
            "Destination": "rRECIPIENT...",
            "Amount": "1000000",  # 1 XRP
            "DestinationTag": 1234
        },
        options={
            "expire": 15,               # minutes until expired
            "submit": True,             # auto-submit after signing
            "return_url": {
                "app": "yourapp://signed/{id}",
                "web": "https://yourapp.com/signed?id={id}"
            },
            "push_token": "USER_PUSH_TOKEN"  # optional
        },
        custom_meta={
            "identifier": "order_123",
            "instruction": "Pay for Order #123",
            "blob": {"order_id": 123, "items": ["item1"]}
        }
    )
)

print(f"UUID: {payload.uuid}")
print(f"QR PNG: {payload.refs.qr_png}")
print(f"QR matrix: {payload.refs.qr_matrix}")
print(f"Deep link: {payload.next.always}")
print(f"WebSocket: {payload.refs.websocket_status}")
```

### JavaScript

```javascript
const payload = await xumm.payload.create({
  txjson: {
    TransactionType: 'Payment',
    Destination: 'rRECIPIENT...',
    Amount: '1000000',
    DestinationTag: 1234
  },
  options: {
    expire: 15,
    submit: true,
    return_url: {
      web: `https://yourapp.com/callback?id={id}`
    }
  },
  custom_meta: {
    instruction: 'Pay for your order'
  }
});

console.log('QR URL:', payload.refs.qr_png);
console.log('Deep link:', payload.next.always);
```

---

## 4. Payload Response Structure

```json
{
  "uuid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "next": {
    "always": "https://xumm.app/sign/uuid",
    "no_push_msg_received": "https://xumm.app/sign/uuid/qr"
  },
  "refs": {
    "qr_png": "https://xumm.app/sign/uuid_q.png",
    "qr_matrix": "https://xumm.app/sign/uuid_q.json",
    "qr_uri_quality_opts": ["m", "q", "h"],
    "websocket_status": "wss://xumm.app/sign/uuid"
  },
  "pushed": true
}
```

---

## 5. Deep Link Formats

```
# Universal deep link (works on all platforms)
https://xumm.app/sign/{payload_uuid}

# iOS deep link
xumm://xumm.app/sign/{payload_uuid}

# Android intent
intent://xumm.app/sign/{payload_uuid}#Intent;package=com.xrpllabs.xumm;scheme=https;end
```

### QR Code Generation (Frontend)

```javascript
import QRCode from 'qrcode';

async function generateQR(deepLink) {
  const canvas = document.getElementById('qr-canvas');
  await QRCode.toCanvas(canvas, deepLink, {
    width: 300,
    margin: 2,
    color: {
      dark: '#000000',
      light: '#ffffff'
    }
  });
}

// Use the Xaman-provided QR image directly
function showQR(payload) {
  const img = document.getElementById('qr-image');
  img.src = payload.refs.qr_png;
  img.alt = 'Scan with Xaman';
}
```

---

## 6. WebSocket: Real-Time Status Updates

```javascript
async function waitForSignature(payload) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(payload.refs.websocket_status);
    
    ws.onmessage = async (event) => {
      const msg = JSON.parse(event.data);
      console.log('Xaman event:', msg);
      
      if (msg.signed === true) {
        ws.close();
        const result = await xumm.payload.get(payload.uuid);
        resolve(result);
      }
      
      if (msg.signed === false || msg.expired) {
        ws.close();
        reject(new Error(msg.expired ? 'Payload expired' : 'User rejected'));
      }
      
      // msg.opened: user opened the request
      // msg.resolved: resolved without signing
    };
    
    ws.onerror = reject;
    
    // Timeout
    setTimeout(() => {
      ws.close();
      reject(new Error('Signing timeout'));
    }, 15 * 60 * 1000);  // 15 minutes
  });
}
```

### Python WebSocket

```python
import asyncio
import websockets
import json
from xumm import XummSdk

async def wait_for_signature(sdk: XummSdk, payload_uuid: str):
    ws_url = f"wss://xumm.app/sign/{payload_uuid}"
    
    async with websockets.connect(ws_url) as ws:
        async for message in ws:
            data = json.loads(message)
            print(f"Xaman event: {data}")
            
            if data.get("signed") is True:
                result = await sdk.payload.get(payload_uuid)
                return result
            
            if data.get("signed") is False or data.get("expired"):
                raise Exception("Signing rejected or expired")
```

---

## 7. Push Notifications

```python
# Get user's push token via OAuth/OTT flow
async def get_push_token(sdk: XummSdk) -> str:
    ott = await sdk.storage.get("user_push_token")
    if ott:
        return ott
    
    # Create OTT (one-time-token) for user auth
    ott_response = await sdk.storage.set("auth", {"requested": True})
    # Present OTT QR to user...
    # After user scans, get their push token
    return None

# Include push_token in payload options
payload = await sdk.payload.create({
    "txjson": {...},
    "options": {
        "push_token": user_push_token  # sends push notification
    }
})
```

---

## 8. Checking Payload Result

```python
async def get_signing_result(sdk: XummSdk, payload_uuid: str) -> dict:
    result = await sdk.payload.get(payload_uuid)
    
    response = result.response
    meta = result.meta
    
    if not meta.signed:
        return {"signed": False, "reason": "User did not sign"}
    
    return {
        "signed": True,
        "tx_hash": response.txid,
        "account": response.account,
        "dispatched_result": response.dispatched_result,
        "multisign_account": response.multisign_account
    }
```

Result structure:
```json
{
  "meta": {
    "uuid": "...",
    "submit": true,
    "signed": true,
    "resolved": true,
    "expired": false
  },
  "application": {
    "name": "YourApp",
    "uuidv4": "..."
  },
  "response": {
    "hex": "1200002200...",
    "txid": "TXHASH...",
    "resolved_at": "2024-01-01T00:00:00Z",
    "dispatched_to": "wss://xrplcluster.com",
    "dispatched_result": "tesSUCCESS",
    "account": "rUSER_ADDRESS..."
  }
}
```

---

## 9. React Integration

```jsx
import { useState, useEffect } from 'react';

function XamanSignButton({ transaction, onSigned, onRejected }) {
  const [payload, setPayload] = useState(null);
  const [status, setStatus] = useState('idle');

  const initiateSign = async () => {
    setStatus('creating');
    const resp = await fetch('/api/xaman/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ transaction })
    });
    const data = await resp.json();
    setPayload(data);
    setStatus('waiting');
    
    // Poll for result
    const ws = new WebSocket(data.refs.websocket_status);
    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.signed === true) {
        setStatus('signed');
        onSigned(msg);
      } else if (msg.signed === false) {
        setStatus('rejected');
        onRejected();
      }
    };
  };

  return (
    <div>
      {status === 'idle' && (
        <button onClick={initiateSign}>Sign with Xaman</button>
      )}
      {status === 'waiting' && payload && (
        <div>
          <img src={payload.refs.qr_png} alt="Scan with Xaman" width={200} />
          <p>Or open: <a href={payload.next.always}>Xaman App</a></p>
        </div>
      )}
      {status === 'signed' && <p>✅ Signed successfully!</p>}
      {status === 'rejected' && <p>❌ Signing rejected</p>}
    </div>
  );
}
```

---

## 10. XRPL Signing Flow (App-to-Ledger)

```
User clicks "Buy" in webapp
    │
    ▼
Backend creates Xaman payload (POST /payload)
    │
    ▼
Frontend shows QR code / deep link
    │
    ▼
User scans with Xaman mobile app
    │
    ▼
Xaman shows transaction details for review
    │
    ▼
User approves → Xaman signs with their private key
    │
    ▼
Xaman submits signed tx to XRPL (if submit=true)
    │
    ▼
WebSocket callback to backend with tx hash
    │
    ▼
Backend verifies tx on XRPL ledger
    │
    ▼
Backend fulfills order / grants access
```

---

## 11. Xaman Subscription Types (txjson)

```javascript
// TrustSet (token opt-in)
{
  TransactionType: 'TrustSet',
  LimitAmount: {
    currency: 'SOLO',
    issuer: 'rHZwvHEs56GCmHupwjA4RY7oPA3EoAJWuN',
    value: '1000000'
  }
}

// NFT offer acceptance
{
  TransactionType: 'NFTokenAcceptOffer',
  NFTokenSellOffer: 'OFFER_ID...'
}

// Generic sign (blob, not transaction)
{
  txblob: "1200002200..."  // pre-built and signed blob to show
}
```
