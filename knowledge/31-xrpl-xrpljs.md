# xrpl.js Library Reference

## Overview

`xrpl.js` is the official JavaScript/TypeScript SDK for the XRP Ledger. Supports Node.js and browsers, WebSocket subscriptions, async/await patterns, and all transaction types.

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

```javascript
// Generate new wallet
const wallet = xrpl.Wallet.generate();
console.log(wallet.seed);         // sn...
console.log(wallet.address);      // rN7n...
console.log(wallet.publicKey);    // ED...
console.log(wallet.privateKey);   // ED...

// From seed
const wallet = xrpl.Wallet.fromSeed('sn...');

// From mnemonic
const wallet = xrpl.Wallet.fromMnemonic(
  'word1 word2 ... word12',
  { derivationPath: "m/44'/144'/0'/0/0" }
);

// From entropy
const wallet = xrpl.Wallet.fromEntropy(Buffer.from('32bytes...', 'hex'));

// Get balance
const balance = await client.getXrpBalance(wallet.address);
console.log(`${balance} XRP`);
```

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

```javascript
const client = new xrpl.Client('wss://xrplcluster.com');
await client.connect();

const wallet = xrpl.Wallet.fromSeed('sn...');

const tx = {
  TransactionType: 'Payment',
  Account: wallet.address,
  Destination: 'rDEST...',
  Amount: xrpl.xrpToDrops('10'),   // '10000000'
  DestinationTag: 1234,
  Memos: [{
    Memo: {
      MemoData: xrpl.convertStringToHex('Hello XRPL'),
      MemoType: xrpl.convertStringToHex('text/plain')
    }
  }]
};

// Autofill fills Sequence, Fee, LastLedgerSequence
const prepared = await client.autofill(tx);
const { tx_blob, hash } = wallet.sign(prepared);
const result = await client.submitAndWait(tx_blob);

console.log(result.result.meta.TransactionResult);  // tesSUCCESS
console.log(`Hash: ${hash}`);

await client.disconnect();
```

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

```javascript
const tx = {
  TransactionType: 'TrustSet',
  Account: wallet.address,
  LimitAmount: {
    currency: 'SOLO',
    issuer: 'rHZwvHEs56GCmHupwjA4RY7oPA3EoAJWuN',
    value: '1000000'
  }
};

const prepared = await client.autofill(tx);
const { tx_blob } = wallet.sign(prepared);
await client.submitAndWait(tx_blob);
```

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

```javascript
const tx = {
  TransactionType: 'NFTokenMint',
  Account: wallet.address,
  NFTokenTaxon: 0,
  Flags: 0x0000000B,     // Burnable | OnlyXRP | Transferable
  TransferFee: 5000,     // 5%
  URI: xrpl.convertStringToHex('ipfs://QmXXX...')
};

const prepared = await client.autofill(tx);
const { tx_blob } = wallet.sign(prepared);
const result = await client.submitAndWait(tx_blob);

// Extract NFT ID
const nftPage = result.result.meta.AffectedNodes.find(
  n => (n.ModifiedNode || n.CreatedNode)?.LedgerEntryType === 'NFTokenPage'
);
const tokens = (nftPage?.ModifiedNode?.FinalFields || nftPage?.CreatedNode?.NewFields)?.NFTokens;
const nftId = tokens?.[tokens.length - 1]?.NFToken?.NFTokenID;
console.log('NFT ID:', nftId);
```

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

```javascript
async function submitWithRetry(client, wallet, tx, maxRetries = 3) {
  const prepared = await client.autofill(tx);
  const { tx_blob, hash } = wallet.sign(prepared);
  
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const result = await client.submitAndWait(tx_blob, {
        failHard: false,
        wallet
      });
      
      const txResult = result.result.meta.TransactionResult;
      if (txResult === 'tesSUCCESS') {
        return { success: true, hash, result };
      }
      
      // tec codes: fee charged, tx failed — don't retry
      if (txResult.startsWith('tec')) {
        return { success: false, hash, result, code: txResult };
      }
      
      // ter codes: retry
      if (txResult.startsWith('ter')) {
        await new Promise(r => setTimeout(r, 2000 * (attempt + 1)));
        continue;
      }
      
      return { success: false, hash, result, code: txResult };
    } catch (e) {
      if (attempt === maxRetries - 1) throw e;
      await new Promise(r => setTimeout(r, 2000 * (attempt + 1)));
    }
  }
}
```

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

```javascript
const NODES = [
  'wss://xrplcluster.com',
  'wss://xrpl.ws',
  'wss://s1.ripple.com'
];

class FailoverXRPLClient {
  constructor(nodes = NODES) {
    this.nodes = nodes;
    this.idx = 0;
    this.client = null;
  }

  async connect() {
    for (let i = 0; i < this.nodes.length; i++) {
      const url = this.nodes[(this.idx + i) % this.nodes.length];
      try {
        const c = new xrpl.Client(url, { connectionTimeout: 5000 });
        await c.connect();
        this.client = c;
        this.idx = (this.idx + i) % this.nodes.length;
        return;
      } catch (e) {
        console.warn(`Failed ${url}: ${e.message}`);
      }
    }
    throw new Error('All XRPL nodes failed');
  }

  async request(params) {
    if (!this.client?.isConnected()) {
      await this.connect();
    }
    try {
      return await this.client.request(params);
    } catch (e) {
      this.idx++;
      await this.connect();
      return this.client.request(params);
    }
  }

  async autofill(tx) {
    if (!this.client?.isConnected()) await this.connect();
    return this.client.autofill(tx);
  }

  async submitAndWait(txBlob) {
    if (!this.client?.isConnected()) await this.connect();
    return this.client.submitAndWait(txBlob);
  }
}
```

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
