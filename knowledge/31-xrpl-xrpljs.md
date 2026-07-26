# xrpl.js Library Reference

## Overview

`xrpl.js` is an official JavaScript/TypeScript SDK for the XRP Ledger. It supports Node.js/browser clients and WebSocket workflows; exact transaction-model and runtime coverage depends on the installed release and must be checked against current SDK documentation.

```bash
npm install xrpl
```

---

## 1. Core Imports

```javascript
const xrpl = require('xrpl');
// or ES modules:
import { Client, Wallet, xrpToDrops, dropsToXrp } from 'xrpl';

// Key imports:
const {
  // Client
  Client,
  
  // Wallet
  Wallet,
  
  // Utils
  xrpToDrops,
  dropsToXrp,
  convertStringToHex,
  convertHexToString,
  
  // Transaction builders (as plain objects)
  // xrpl.js uses plain JS objects for transactions
  
  // Request models
  // also plain objects with 'command' field
  
  // Helpers
  multisign,
  encode,
  decode,
  encodeForSigning,
  
  // Constants
  ECDSA,
} = require('xrpl');
```

---

## 2. Client Initialization

```javascript
// Basic WebSocket client
const client = new xrpl.Client('wss://xrplcluster.com');
await client.connect();

// With options
const client = new xrpl.Client('wss://xrplcluster.com', {
  timeout: 20000,           // request timeout ms
  connectionTimeout: 5000,  // connection timeout ms
  maxFeeXRP: '2',           // max fee for autofill (XRP)
});

// Don't forget to disconnect
await client.disconnect();

// Pattern: use with try/finally
const client = new xrpl.Client('wss://xrplcluster.com');
try {
  await client.connect();
  // ... do work
} finally {
  await client.disconnect();
}
```

### HTTP Client (for read-only, no WebSocket)

```javascript
// xrpl.js uses WebSocket internally even for HTTP URLs
const client = new xrpl.Client('https://xrplcluster.com');
```

---

## 3. Wallet

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## 4. Account Info & Lines

```javascript
// Account info
const resp = await client.request({
  command: 'account_info',
  account: 'rN7n...',
  ledger_index: 'validated'
});
const acct = resp.result.account_data;
console.log(`Balance: ${xrpl.dropsToXrp(acct.Balance)} XRP`);
console.log(`Sequence: ${acct.Sequence}`);

// Account trust lines (with pagination)
async function getAllTrustLines(address) {
  const lines = [];
  let marker;
  
  do {
    const resp = await client.request({
      command: 'account_lines',
      account: address,
      limit: 400,
      ...(marker && { marker })
    });
    
    lines.push(...resp.result.lines);
    marker = resp.result.marker;
  } while (marker);
  
  return lines;
}

// Account NFTs
const nftResp = await client.request({
  command: 'account_nfts',
  account: 'rN7n...',
  limit: 400
});
console.log(nftResp.result.account_nfts);
```

---

## 5. Sending XRP

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## 6. Token Payment

```javascript
const tx = {
  TransactionType: 'Payment',
  Account: wallet.address,
  Destination: 'rDEST...',
  Amount: {
    currency: 'USD',
    issuer: 'rISSUER...',
    value: '50'
  }
};
```

---

## 7. TrustSet

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## 8. OfferCreate (DEX)

```javascript
// Buy 1000 SOLO for 10 XRP
const tx = {
  TransactionType: 'OfferCreate',
  Account: wallet.address,
  TakerPays: {
    currency: 'SOLO',
    issuer: 'rHZwvHEs...',
    value: '1000'
  },
  TakerGets: xrpl.xrpToDrops('10'),
  Flags: 0
};
```

---

## 9. NFTokenMint

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## 10. WebSocket Subscriptions

```javascript
// Subscribe to account transactions
const client = new xrpl.Client('wss://xrplcluster.com');
await client.connect();

// Subscribe
await client.request({
  command: 'subscribe',
  accounts: ['rWATCH...', 'rTREASURY...']
});

// Listen
client.on('transaction', (tx) => {
  console.log('New tx:', tx.transaction.TransactionType);
  console.log('Hash:', tx.transaction.hash);
  
  if (tx.meta.TransactionResult === 'tesSUCCESS') {
    const delivered = tx.meta.delivered_amount;
    console.log('Delivered:', delivered);
  }
});

// Subscribe to ledger stream
await client.request({
  command: 'subscribe',
  streams: ['ledger']
});

client.on('ledgerClosed', (ledger) => {
  console.log(`Ledger ${ledger.ledger_index} closed`);
});

// Unsubscribe
await client.request({
  command: 'unsubscribe',
  accounts: ['rWATCH...']
});
```

---

## 11. Account Tracking Pattern

```javascript
class XRPLAccountTracker {
  constructor(addresses) {
    this.addresses = addresses;
    this.client = new xrpl.Client('wss://xrplcluster.com');
    this.handlers = [];
  }

  onTransaction(handler) {
    this.handlers.push(handler);
    return this;
  }

  async start() {
    await this.client.connect();
    
    await this.client.request({
      command: 'subscribe',
      accounts: this.addresses
    });
    
    this.client.on('transaction', (event) => {
      if (event.meta.TransactionResult !== 'tesSUCCESS') return;
      this.handlers.forEach(h => h(event));
    });

    this.client.on('disconnected', async () => {
      console.log('Disconnected, reconnecting...');
      await new Promise(r => setTimeout(r, 3000));
      await this.start();
    });
  }

  async stop() {
    await this.client.disconnect();
  }
}

// Usage
const tracker = new XRPLAccountTracker(['rHOT_WALLET...', 'rTREASURY...'])
  .onTransaction((event) => {
    const tx = event.transaction;
    const delivered = event.meta.delivered_amount;
    console.log(`${tx.TransactionType}: ${JSON.stringify(delivered)}`);
  });

await tracker.start();
```

---

## 12. Transaction Submission with Retry

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## 13. Browser vs Node.js

```javascript
// Browser (via CDN)
// <script src="https://unpkg.com/xrpl/build/xrpl-latest-min.js"></script>
// Global: window.xrpl

// Browser ES module
import * as xrpl from 'https://unpkg.com/xrpl@latest/build/xrpl-latest.js';

// Node.js CommonJS
const xrpl = require('xrpl');

// Node.js ESM
import * as xrpl from 'xrpl';
```

Browser-specific considerations:
- Use `wss://` not `ws://` (mixed content)
- No secret storage in browser — use wallet extensions
- Client reconnect on WebSocket close is essential

---

## 14. Multi-Client Failover

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## 15. TypeScript Types

```typescript
import {
  Client,
  Wallet,
  Payment,
  TrustSet,
  OfferCreate,
  NFTokenMint,
  AMMDeposit,
  AccountInfoRequest,
  AccountInfoResponse,
  LedgerEntryRequest,
  SubmittableTransaction,
  TransactionMetadata,
  CreatedNode,
  ModifiedNode,
  Amount,
  IssuedCurrencyAmount,
} from 'xrpl';

// Type guard for issued currency
function isIssuedCurrency(amount: Amount): amount is IssuedCurrencyAmount {
  return typeof amount === 'object' && 'currency' in amount;
}

// Typed transaction result
interface SubmitResult {
  result: {
    meta: TransactionMetadata;
    hash: string;
    ledger_index: number;
    validated: boolean;
  };
}
```

---

## 16. Xahau and JavaScript — Compatibility Boundary

Xahau is not an XRPL Mainnet endpoint. It uses Xahau network IDs (`21337` Mainnet, `21338` Testnet), Xahau-specific transaction definitions, and amendment state that can differ between its networks.

Do **not** assume a generic `xrpl.js` installation can serialize Xahau-only types such as `SetHook`, `Invoke`, `Remit`, or URIToken transactions. Use a current Xahau-maintained JavaScript client/codec and pin its version. Validate the exact unsigned transaction against the target network's current `server_definitions.json` and `simulate` before signing.

XRPL-Hermes does not ship a JavaScript Xahau runtime or a `SetHook` builder. Its certified Xahau support is intentionally narrower:

```bash
python3 scripts/xrpl_tools.py hooks-bitmask Payment Invoke
python3 scripts/xrpl_tools.py hooks-info rACCOUNT testnet
```

Never adapt an XRPL example by only changing the endpoint or `TransactionType`. Never pass a seed to a node, script example, or agent.

### Reading Xahau data from JavaScript

For production code:

1. use a current Xahau-aware library;
2. connect to the explicit target endpoint;
3. call `server_info` and require the expected `network_id`;
4. request validated ledger state;
5. treat top-level/result RPC errors as failures;
6. preserve ledger index/hash and endpoint provenance.

Installed Hooks are represented by Hook ledger objects, not fields embedded in `account_info`. The released Python CLI already applies this error/provenance discipline.

### Writing Xahau transactions

A safe JavaScript workflow is architectural, not copy-paste transaction JSON:

1. prepare with a pinned Xahau-aware model/codec;
2. include the correct `NetworkID`;
3. decode and review all Xahau-specific fields;
4. compare serialization against current target-network definitions;
5. call `simulate` where supported;
6. hand the unsigned payload to a user-controlled compatible wallet;
7. verify validated transaction and resulting ledger state.

No key handling or broadcast path is provided by XRPL-Hermes.

## 17. Xahau-Specific Protocol Notes

- Hooks are native Xahau account logic installed with `SetHook`; they are not XRPL Mainnet Hooks.
- `HookOn` is a 256-bit active-low mask except active-high `SetHook` bit 22.
- Hook chains are positional and contain up to 10 slots.
- URIToken transaction types are Xahau-specific and not interchangeable with XRPL NFTs.
- `Invoke` and `Remit` are Xahau protocol transaction types, not generic xrpl.js patterns.
- Amendment support differs by network. At the 2026-07-25 review, Testnet enabled HookOnV2/NamedHooks while Mainnet disabled/vetoed them.
- Historic Xahau burn-to-mint distribution must not be described as a current general bridge API.

Use `references/xahau-hooks.md` and `knowledge/51-xrpl-xahau-hooks.md` for the pinned protocol facts and current capability boundary.

---

## 18. xrpl.js Beta / Advanced Features

### 18.1 MPT (Multi-Purpose Tokens)

MPTs are a newer token primitive: fungible, fixed-supply or capped, without a trustline. xrpl.js v4+ exposes the transactions; some helper utilities are still being polished.

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


### 18.2 AMM Methods (XRPL only — not Xahau)

```javascript
// Create an AMM pool: 1000 XRP <-> 5000 USD
const ammCreateTx = {
  TransactionType: 'AMMCreate',
  Account: wallet.address,
  Amount: xrpl.xrpToDrops('1000'),
  Amount2: {
    currency: 'USD',
    issuer: 'rISSUER...',
    value: '5000'
  },
  TradingFee: 500   // 0.5% in units of 1/100,000
};

// Deposit liquidity (single-asset)
const ammDepositTx = {
  TransactionType: 'AMMDeposit',
  Account: wallet.address,
  Asset: { currency: 'XRP' },
  Asset2: { currency: 'USD', issuer: 'rISSUER...' },
  Amount: xrpl.xrpToDrops('100'),
  Flags: 0x00080000   // tfSingleAsset
};

// Withdraw by LP token amount
const ammWithdrawTx = {
  TransactionType: 'AMMWithdraw',
  Account: wallet.address,
  Asset: { currency: 'XRP' },
  Asset2: { currency: 'USD', issuer: 'rISSUER...' },
  LPTokenIn: {
    currency: '03'.padEnd(40, '0'),   // 20-byte LP currency code
    issuer: 'rAMM_ACCOUNT...',
    value: '50'
  },
  Flags: 0x00010000   // tfLPToken
};

// Query AMM state
const ammInfo = await client.request({
  command: 'amm_info',
  asset: { currency: 'XRP' },
  asset2: { currency: 'USD', issuer: 'rISSUER...' },
  ledger_index: 'validated'
});
console.log('Pool XRP:', ammInfo.result.amm.amount);
console.log('Pool USD:', ammInfo.result.amm.amount2);
console.log('LP supply:', ammInfo.result.amm.lp_token);
console.log('Trading fee:', ammInfo.result.amm.trading_fee);
```

### 18.3 DID Operations

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


**Note:** these features require their respective amendments to be enabled on the network. Check `feature` RPC or `server_info.amendment_blocked`.

---

## Related Files

- `knowledge/30-xrpl-xrplpy.md` — Python equivalent
- `knowledge/41-xrpl-bots-patterns.md` — bot patterns in JavaScript
