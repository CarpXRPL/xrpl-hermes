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
- **Joey**: Connect in browser, request XRPL signing, and confirm the returned hash with `tx` on `https://xrplcluster.com`.
- **Crossmark**: Request account access only when needed, pass minimal `txjson`, and let the extension autofill account context when supported.
- **MetaMask**: Check `eth_chainId` on `https://rpc.xrplevm.org` and reject contract calls on the wrong sidechain network.
- **Privy**: Authenticate user identity first, then attach XRPL payment intent records to the Privy user id for auditability.
- **Xaman**: Create a payload on the server, show QR/deep link, then verify `payload_uuidv4` before crediting user state.

---

## Related Files

- `knowledge/26-xrpl-xaman-deeplink.md` — Xaman deep-links
- `knowledge/27-xrpl-joey-wallet.md` — Joey wallet
- `knowledge/28-xrpl-privy-auth.md` — Privy embedded auth
