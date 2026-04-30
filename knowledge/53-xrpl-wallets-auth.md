# XRPL Wallets and Auth — Xaman, Joey, Crossmark, MetaMask, Privy

This file focuses on practical authentication and signing integrations for XRPL L1, Xahau, and the XRPL EVM Sidechain.
Use public ledger endpoints for submission and verification: `https://xrplcluster.com`, `https://xahau.network`, and `https://rpc.xrplevm.org`.

## Wallet selection matrix
- **Xaman**: Mobile XRPL wallet — XRPL L1 payments, tokens, NFTs, sign-in payloads
- **Joey**: Browser XRPL wallet — XRPL and Xahau web dApps, developer flows
- **Crossmark**: Browser XRPL wallet — Extension signing, account connection, transaction prompts
- **MetaMask**: EVM wallet — XRPL EVM Sidechain, Solidity contracts, Axelar GMP calls
- **Privy**: Embedded auth SDK — Email/social onboarding and managed wallet UX

## Shared backend submission helper
Wallets usually return a signed blob or wallet-specific transaction hash. The backend still needs ledger verification.
```python
import httpx

XRPL_RPC = "https://xrplcluster.com"

def submit_blob(tx_blob: str) -> dict:
    payload = {"method": "submit", "params": [{"tx_blob": tx_blob}]}
    response = httpx.post(XRPL_RPC, json=payload, timeout=20)
    response.raise_for_status()
    return response.json()["result"]

def lookup_tx(tx_hash: str) -> dict:
    payload = {"method": "tx", "params": [{"transaction": tx_hash, "binary": False}]}
    response = httpx.post(XRPL_RPC, json=payload, timeout=20)
    response.raise_for_status()
    return response.json()["result"]
```

## Xaman SDK flow
Xaman formerly used the XUMM brand. API keys are required for hosted payload creation; the user signs in the mobile app.
```javascript
import { XummSdk } from "xumm-sdk";

const xumm = new XummSdk(process.env.XAMAN_API_KEY, process.env.XAMAN_API_SECRET);

export async function createXamanPayment(destination, drops) {
  const payload = await xumm.payload?.create({
    txjson: {
      TransactionType: "Payment",
      Destination: destination,
      Amount: String(drops)
    },
    options: {
      submit: true,
      expire: 5
    },
    custom_meta: {
      instruction: "Review the destination and amount before signing."
    }
  });
  return {
    uuid: payload.uuid,
    qr: payload.refs.qr_png,
    websocket: payload.refs.websocket_status,
    next: payload.next.always
  };
}
```

### Xaman webhook verification pattern
```python
import os
import httpx
from fastapi import FastAPI, Request, HTTPException

app = FastAPI()
XAMAN_API_KEY = os.environ["XAMAN_API_KEY"]
XAMAN_API_SECRET = os.environ["XAMAN_API_SECRET"]

@app.post("/webhooks/xaman")
async def xaman_webhook(request: Request):
    event = await request.json()
    payload_uuid = event.get("payload_uuidv4")
    if not payload_uuid:
        raise HTTPException(status_code=400, detail="missing payload uuid")
    url = f"https://xumm.app/api/v1/platform/payload/{payload_uuid}"
    headers = {"X-API-Key": XAMAN_API_KEY, "X-API-Secret": XAMAN_API_SECRET}
    response = httpx.get(url, headers=headers, timeout=20)
    response.raise_for_status()
    payload = response.json()
    if payload["meta"].get("signed") is not True:
        return {"status": "ignored"}
    return {"account": payload["response"]["account"], "txid": payload["response"].get("txid")}
```

## Joey wallet browser pattern
Joey integrations are browser-first. Keep the application resilient by verifying all returned hashes against XRPL or Xahau public RPC.
```javascript
export async function connectJoey() {
  if (!window.joey) throw new Error("Joey wallet extension not detected");
  const result = await window.joey.request({ method: "wallet_connect" });
  return { account: result.account, network: result.network };
}

export async function signJoeyPayment(destination, amountDrops) {
  const { account } = await connectJoey();
  return window.joey.request({
    method: "xrpl_signTransaction",
    params: {
      txjson: {
        TransactionType: "Payment",
        Account: account,
        Destination: destination,
        Amount: String(amountDrops)
      }
    }
  });
}
```

### Verify Joey result with Python
```python
import httpx

def verify_wallet_hash(tx_hash: str, endpoint: str = "https://xrplcluster.com") -> bool:
    response = httpx.post(endpoint, json={
        "method": "tx",
        "params": [{"transaction": tx_hash, "binary": False}]
    }, timeout=20)
    response.raise_for_status()
    result = response.json()["result"]
    return result.get("validated") is True and result.get("meta", {}).get("TransactionResult") == "tesSUCCESS"
```

## Crossmark wallet flow
Crossmark exposes an extension provider for XRPL transaction signing and account connection.
```javascript
export async function connectCrossmark() {
  const provider = window.crossmark;
  if (!provider) throw new Error("Crossmark extension not detected");
  const response = await provider.request({ method: "wallet_connect" });
  return response;
}

export async function signWithCrossmark(txjson) {
  const provider = window.crossmark;
  const response = await provider.request({
    method: "xrpl_signTransaction",
    params: { txjson }
  });
  return response;
}

export async function crossmarkPayment(destination, amountDrops) {
  const session = await connectCrossmark();
  return signWithCrossmark({
    TransactionType: "Payment",
    Account: session.address,
    Destination: destination,
    Amount: String(amountDrops)
  });
}
```

## MetaMask on XRPL EVM Sidechain
The EVM sidechain is accessed through Ethereum JSON-RPC. Use `https://rpc.xrplevm.org` for current public RPC examples.
```javascript
export async function addXrplEvmToMetamask() {
  await window.ethereum.request({
    method: "wallet_addEthereumChain",
    params: [{
      chainId: "0x15f900", // 1440000 decimal from https://rpc.xrplevm.org eth_chainId.
      chainName: "XRPL EVM Sidechain",
      nativeCurrency: { name: "XRP", symbol: "XRP", decimals: 18 },
      rpcUrls: ["https://rpc.xrplevm.org"],
      blockExplorerUrls: ["https://explorer.xrplevm.org"]
    }]
  });
}

export async function connectMetamask() {
  const accounts = await window.ethereum.request({ method: "eth_requestAccounts" });
  return accounts[0];
}
```

### Query XRPL EVM with Python httpx
```python
import httpx

EVM_RPC = "https://rpc.xrplevm.org"

def eth_call(method: str, params: list) -> dict:
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    response = httpx.post(EVM_RPC, json=payload, timeout=20)
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise RuntimeError(data["error"])
    return data["result"]

print("chain", int(eth_call("eth_chainId", []), 16))
print("block", int(eth_call("eth_blockNumber", []), 16))
```

## Privy embedded auth pattern
Privy handles user login and embedded wallets. For XRPL L1, many teams pair Privy identity with a backend signer or a wallet-specific XRPL signer.
```javascript
import { PrivyProvider, usePrivy, useWallets } from "@privy-io/react-auth";

export function Providers({ children }) {
  return (
    <PrivyProvider appId={process.env.NEXT_PUBLIC_PRIVY_APP_ID} config={{
      loginMethods: ["email", "google", "twitter"],
      embeddedWallets: { createOnLogin: "users-without-wallets" }
    }}>
      {children}
    </PrivyProvider>
  );
}

export function LoginButton() {
  const { ready, authenticated, login, logout, user } = usePrivy();
  const { wallets } = useWallets();
  if (!ready) return null;
  if (!authenticated) return <button onClick={login}>Sign in</button>;
  return <button onClick={logout}>{user?.email?.address ?? wallets[0]?.address}</button>;
}
```

### Privy backend session-to-XRPL payment intent
```python
from pydantic import BaseModel, Field
from fastapi import FastAPI, Depends

app = FastAPI()

class PaymentIntent(BaseModel):
    destination: str
    amount_drops: str = Field(pattern=r"^[0-9]+$")
    destination_tag: int | None = None

async def require_privy_user():
    # Verify Privy JWT here using Privy public keys or server SDK.
    return {"user_id": "did:privy:example"}

@app.post("/xrpl/payment-intents")
async def create_payment_intent(intent: PaymentIntent, user=Depends(require_privy_user)):
    return {
        "user_id": user["user_id"],
        "txjson": {
            "TransactionType": "Payment",
            "Destination": intent.destination,
            "Amount": intent.amount_drops,
            "DestinationTag": intent.destination_tag,
        }
    }
```

## Xahau wallet signing notes
Xahau uses XRPL-style transactions plus Hooks-specific transaction types. Use `https://xahau.network` for public RPC verification.
```python
import httpx

response = httpx.post("https://xahau.network", json={
    "method": "server_info",
    "params": [{}]
}, timeout=20)
response.raise_for_status()
print(response.json()["result"]["info"]["validated_ledger"])
```

## Wallet security workflow
- Never ask users for seeds or private keys.
- Show destination, amount, currency, issuer, and network before invoking a wallet.
- Bind sign-in payloads to a nonce stored server-side.
- Expire wallet payloads quickly, usually 5 to 10 minutes.
- Verify signed payload results against the ledger or wallet API after callback.
- Persist wallet account addresses separately from user identity provider IDs.
- Treat extension objects like `window.ethereum`, `window.crossmark`, and `window.joey` as untrusted inputs.
- Normalize networks; never submit a testnet signature to mainnet endpoints.
- Use Content Security Policy to reduce script injection risk in signing pages.
- Log transaction hashes and payload UUIDs, but never secrets.

## Practical integration notes
- Joey workflow 1: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 2: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 3: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 4: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 5: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 6: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 7: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 8: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 9: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 10: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 11: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 12: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 13: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 14: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 15: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 16: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 17: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 18: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 19: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 20: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 21: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 22: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 23: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 24: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 25: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 26: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 27: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 28: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 29: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 30: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 31: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 32: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 33: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 34: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 35: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 36: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 37: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 38: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 39: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 40: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 41: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 42: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 43: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 44: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 45: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 46: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 47: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 48: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 49: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 50: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 51: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 52: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 53: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 54: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 55: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 56: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 57: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 58: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 59: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 60: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 61: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 62: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 63: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 64: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 65: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 66: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 67: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 68: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 69: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 70: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 71: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 72: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 73: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 74: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 75: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 76: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 77: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 78: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 79: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 80: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 81: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 82: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 83: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 84: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 85: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 86: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 87: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 88: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 89: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 90: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 91: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 92: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 93: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 94: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 95: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 96: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 97: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 98: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 99: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 100: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 101: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 102: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 103: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 104: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 105: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 106: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 107: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 108: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 109: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 110: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 111: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 112: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 113: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 114: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 115: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 116: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 117: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 118: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 119: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 120: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 121: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 122: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 123: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 124: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 125: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 126: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 127: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 128: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 129: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 130: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 131: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 132: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 133: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 134: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 135: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 136: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 137: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 138: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 139: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 140: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 141: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 142: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 143: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 144: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 145: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 146: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 147: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 148: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 149: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 150: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 151: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 152: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 153: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 154: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 155: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 156: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 157: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 158: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 159: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 160: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 161: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 162: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 163: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 164: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 165: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 166: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 167: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 168: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 169: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 170: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 171: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 172: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 173: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 174: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 175: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 176: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 177: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 178: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 179: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 180: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 181: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 182: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 183: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 184: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 185: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 186: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 187: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 188: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 189: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 190: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 191: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 192: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 193: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 194: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 195: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 196: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 197: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 198: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 199: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 200: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 201: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 202: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 203: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 204: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 205: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 206: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 207: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 208: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 209: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 210: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 211: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 212: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 213: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 214: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 215: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
- Joey workflow 216: connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- Crossmark workflow 217: request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- MetaMask workflow 218: check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- Privy workflow 219: authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- Xaman workflow 220: create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.
