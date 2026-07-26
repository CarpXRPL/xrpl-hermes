# XRPL Joey Wallet

## Overview

This legacy article describes an unverified browser-wallet interface. Joey's current distribution, API, network support, and security posture were not certified during the v1.9.0 review. Do not treat the examples as an official SDK contract; verify every capability against a current first-party Joey source before use.

---

## 1. Key Features

| Feature | Description |
|---------|-------------|
| Browser-based | Chrome extension, no mobile required |
| Xahau/Hooks | Unsupported/unverified in XRPL-Hermes |
| Trust line manager | View, create, and remove trust lines |
| Multi-account | Manage multiple wallets in one interface |
| Quick auth | One-click sign for dApp interactions |
| Dev tools | Raw TX builder, ledger explorer |
| No seed phrase leak | Keys stay in browser secure storage |

---

## 2. Installation

```
Chrome Web Store: "Joey - XRPL Wallet"
Or: https://chrome.google.com/webstore/search/joey+xrpl
```

Manual install (dev mode):
1. Clone repository: `https://github.com/WietseWind/joey`
2. `npm install && npm run build`
3. Chrome: Extensions → Load unpacked → select `build/` folder

---

## 3. Connecting to Joey from a Web App

Joey injects a provider into the browser window:

```javascript
// Check if Joey is installed
const isJoeyAvailable = () => {
  return typeof window.xrpl !== 'undefined' && window.xrpl.joey;
};

// Connect / request account
async function connectJoey() {
  if (!isJoeyAvailable()) {
    throw new Error('Joey wallet not installed');
  }
  
  const response = await window.xrpl.joey.request({
    method: 'requestAccount'
  });
  
  return response.address;  // rUSER...
}

// Get current account
async function getAccount() {
  const response = await window.xrpl.joey.request({
    method: 'getAccount'
  });
  return response;
}
```

---

## 4. Signing Transactions with Joey

```javascript
// Sign a payment
async function signPayment(destination, amountDrops) {
  const tx = {
    TransactionType: 'Payment',
    Destination: destination,
    Amount: String(amountDrops)
  };
  
  const result = await window.xrpl.joey.signTransaction(tx);
  
  if (result.signed) {
    console.log('TX hash:', result.txid);
    console.log('Signed blob:', result.tx_blob);
  } else {
    console.log('User rejected');
  }
  
  return result;
}

// Sign and submit
async function signAndSubmit(tx) {
  const result = await window.xrpl.joey.signAndSubmit(tx);
  return result;
}
```

---

## 5. Trust Line Management

Joey provides a UI for trust lines, but you can also drive it programmatically:

```javascript
// Request user to set a trust line
async function requestTrustLine(currency, issuer, limit = '1000000') {
  const tx = {
    TransactionType: 'TrustSet',
    LimitAmount: {
      currency: currency,
      issuer: issuer,
      value: limit
    }
  };
  
  return window.xrpl.joey.signAndSubmit(tx);
}

// Check if trust line exists (read-only, via XRPL node)
async function checkTrustLine(account, currency, issuer) {
  const xrpl = require('xrpl');
  const client = new xrpl.Client('wss://xrplcluster.com');
  await client.connect();
  
  const resp = await client.request({
    command: 'account_lines',
    account: account,
    peer: issuer
  });
  
  const line = resp.result.lines.find(
    l => l.currency === currency && l.account === issuer
  );
  
  await client.disconnect();
  return line || null;
}
```

---

## 6. Xahau Compatibility Boundary

Do not assume the Joey wallet API supports Xahau, Xahau network switching, `SetHook`, or `Invoke`. The former examples were removed because their wallet methods, network selector, HookOn encoding, and signing behavior were not verified against a current official Joey source.

For a Xahau flow:

1. use `references/xahau-hooks.md` for protocol facts;
2. use a currently documented Xahau-compatible wallet;
3. prepare and simulate the unsigned transaction with a current Xahau-aware serializer;
4. show the exact decoded network ID, chain slot, flags, mask, namespace, parameters, grants, and code/hash to the user;
5. let the user approve and sign in the wallet;
6. verify validated post-state with `hooks-info rACCOUNT testnet`.

XRPL-Hermes does not provide a Joey-to-Xahau signing adapter.

---

## 7. Hooks Interaction via Joey

**Status: unsupported/unverified.** Do not generate Joey `SetHook` or `Invoke` calls from this knowledge file. Consult current official Joey documentation and independently certify that capability before adding an integration.

---

## 8. React Hook for Joey

```jsx
import { useState, useEffect, createContext, useContext } from 'react';

const JoeyContext = createContext(null);

export function JoeyProvider({ children }) {
  const [address, setAddress] = useState(null);
  const [connected, setConnected] = useState(false);
  const [network, setNetwork] = useState('mainnet');

  useEffect(() => {
    // Auto-detect connection
    if (window.xrpl?.joey) {
      window.xrpl.joey.on('accountChanged', (acc) => {
        setAddress(acc.address);
      });
      window.xrpl.joey.on('networkChanged', (net) => {
        setNetwork(net.name);
      });
      window.xrpl.joey.on('disconnected', () => {
        setConnected(false);
        setAddress(null);
      });
    }
  }, []);

  const connect = async () => {
    if (!window.xrpl?.joey) {
      window.open('https://chrome.google.com/webstore/search/joey+xrpl', '_blank');
      return;
    }
    const resp = await window.xrpl.joey.request({ method: 'requestAccount' });
    setAddress(resp.address);
    setConnected(true);
  };

  const sign = async (tx) => {
    return window.xrpl.joey.signAndSubmit(tx);
  };

  return (
    <JoeyContext.Provider value={{ address, connected, network, connect, sign }}>
      {children}
    </JoeyContext.Provider>
  );
}

export const useJoey = () => useContext(JoeyContext);

// Usage in component:
function PayButton() {
  const { address, connected, connect, sign } = useJoey();
  
  const handlePay = async () => {
    const result = await sign({
      TransactionType: 'Payment',
      Destination: 'rRECIPIENT...',
      Amount: '1000000'
    });
    console.log(result);
  };
  
  return (
    <button onClick={connected ? handlePay : connect}>
      {connected ? `Pay (${address.slice(0, 8)}...)` : 'Connect Joey'}
    </button>
  );
}
```

---

## 9. Developer Use Cases

### Quick Local Testing

```javascript
// Joey can import a devnet/testnet account for instant testing
// No mainnet funds needed

// In Joey settings: switch to Testnet
// Fund via faucet: https://xrpl.org/xrp-testnet-faucet.html
```

### Raw Transaction Builder

Joey includes a raw TX editor for testing transaction formats before production. Navigate to: Settings → Developer Tools → Raw TX Builder.

### Multi-Account Management

```javascript
// List accounts
const accounts = await window.xrpl.joey.request({
  method: 'getAccounts'
});

// Switch active account
await window.xrpl.joey.request({
  method: 'setActiveAccount',
  address: 'rOTHER...'
});
```

---

## 10. Comparison with Other XRPL Wallets

| Feature | Joey | Xaman | Bifrost | Crossmark |
|---------|------|-------|---------|-----------|
| Browser extension | ✅ | ❌ | ✅ | ✅ |
| Mobile app | ❌ | ✅ | ✅ | ❌ |
| Hooks/Xahau | Unverified | Unverified | Unverified | Unverified |
| Push notifications | ❌ | ✅ | ❌ | ❌ |
| Dev tools | ✅ | ❌ | Partial | ✅ |
| Multi-account | ✅ | ✅ | ✅ | ✅ |
| Hardware wallet | ❌ | ✅ | ❌ | ❌ |

---

## 11. Security Notes

- Joey keys never leave the browser extension's isolated storage
- No seed phrase transmitted over network
- Sign requests are shown with full transaction details
- Users can review and reject before signing
- For production dApps: combine Joey (dev) with Xaman (end user)

---

## Related Files

- `knowledge/26-xrpl-xaman-deeplink.md` — Xaman for end users
- `knowledge/28-xrpl-privy-auth.md` — Privy for embedded auth
- `knowledge/53-xrpl-wallets-auth.md` — wallet auth patterns
