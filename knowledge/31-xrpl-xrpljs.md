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

---

## 16. Xahau Hooks with xrpl.js

Xahau is a sidechain of the XRPL with native smart-contract support via **Hooks**. Hooks are small WASM modules attached to an account that execute on inbound/outbound transactions. xrpl.js can build, install, and read hooks against `wss://xahau.network`.

### 16.1 Installing a Hook (`SetHook` transaction)

```javascript
const xrpl = require('xrpl');

// Connect to Xahau (NOT XRPL mainnet)
const client = new xrpl.Client('wss://xahau.network');
await client.connect();

const wallet = xrpl.Wallet.fromSeed('sn...');

// CreateCode is the WASM bytecode (hex-encoded)
const wasmHex = '0061736D01000000...'.toUpperCase();

const setHookTx = {
  TransactionType: 'SetHook',
  Account: wallet.address,
  Hooks: [{
    Hook: {
      CreateCode: wasmHex,
      HookOn: 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFBFFFFE',
      // HookOn bitmap: which transaction types trigger the hook.
      // Each bit (inverted) represents a TT. 0xBFFFFE fires on Payment.
      HookNamespace: 'A'.repeat(64),  // 32-byte hex namespace
      HookApiVersion: 0,
      Flags: 1,                        // hsfOverride — replace existing hook at this slot
      HookParameters: [{
        HookParameter: {
          HookParameterName: xrpl.convertStringToHex('THRESHOLD'),
          HookParameterValue: '00000000000F4240'  // 1,000,000 drops
        }
      }],
      HookGrants: []                   // optional: grant other hooks state access
    }
  }]
};

const prepared = await client.autofill(setHookTx);
const { tx_blob, hash } = wallet.sign(prepared);
const result = await client.submitAndWait(tx_blob);

console.log('SetHook result:', result.result.meta.TransactionResult);
console.log('Hash:', hash);

await client.disconnect();
```

**Key fields:**
- `CreateCode` — WASM bytecode (compiled from C with hookapi.h, or AssemblyScript). Omit or set `''` to delete a hook slot.
- `HookOn` — 256-bit bitmap, **inverted**: bit set = does NOT fire. Default `'F'.repeat(64)` fires on nothing.
- `HookNamespace` — 32-byte hex string isolating this hook's state from others on the same account.
- `HookApiVersion` — currently `0`.
- `HookParameters` — runtime config readable from inside the hook via `hook_param`.

### 16.2 Querying Installed Hooks (`account_objects`)

```javascript
// List all hooks on an account
const resp = await client.request({
  command: 'account_objects',
  account: 'rN7n...',
  type: 'hook',
  ledger_index: 'validated'
});

for (const hookObj of resp.result.account_objects) {
  console.log('Hook count:', hookObj.Hooks.length);
  for (const h of hookObj.Hooks) {
    const hk = h.Hook;
    console.log('  Namespace:', hk.HookNamespace);
    console.log('  HookHash:', hk.HookHash);  // sha256 of CreateCode
    console.log('  HookOn:', hk.HookOn);
    console.log('  Params:', hk.HookParameters);
  }
}

// Fetch the underlying HookDefinition (shared CreateCode)
const def = await client.request({
  command: 'ledger_entry',
  hook_definition: 'ABCDEF...HookHash',
  ledger_index: 'validated'
});
console.log('CreateCode size:', def.result.node.CreateCode.length / 2, 'bytes');
console.log('Fee:', def.result.node.Fee);  // execution fee in drops
```

### 16.3 Reading & Writing Hook State

Hook state is a per-namespace key-value store. **Writes happen inside the hook** (via `state_set`); JS reads it from outside.

```javascript
// Read a single state entry
const stateResp = await client.request({
  command: 'ledger_entry',
  hook_state: {
    account: 'rN7n...',                          // hook owner
    key: '0'.repeat(56) + '4F574E4552',           // 32-byte hex key, e.g. "OWNER" right-padded
    namespace_id: 'A'.repeat(64)
  },
  ledger_index: 'validated'
});

console.log('State value:', stateResp.result.node.HookStateData);
// Hex — decode based on what the hook stored

// List all state entries in a namespace
async function getHookState(account, namespace) {
  const all = [];
  let marker;
  do {
    const r = await client.request({
      command: 'account_objects',
      account,
      type: 'hook_state',
      limit: 400,
      ...(marker && { marker })
    });
    for (const obj of r.result.account_objects) {
      if (obj.HookStateData && obj.Namespace === namespace) {
        all.push({ key: obj.HookStateKey, value: obj.HookStateData });
      }
    }
    marker = r.result.marker;
  } while (marker);
  return all;
}

const entries = await getHookState('rN7n...', 'A'.repeat(64));
entries.forEach(e => {
  const keyStr = xrpl.convertHexToString(e.key.replace(/00+$/, ''));
  console.log(`${keyStr} = ${e.value}`);
});
```

To **write** state from JS, you submit a transaction that triggers the hook; the hook itself calls `state_set`. There is no direct "write hook state" RPC.

### 16.4 Decoding HookEmittedTxns and Hook Execution Results

```javascript
// After submitting a tx that triggered a hook, inspect emitted txns
const result = await client.submitAndWait(tx_blob);
const meta = result.result.meta;

// HookExecutions array — one entry per hook that ran
if (meta.HookExecutions) {
  for (const he of meta.HookExecutions) {
    const ex = he.HookExecution;
    console.log('Hook account:', ex.HookAccount);
    console.log('Return code:', ex.HookReturnCode);  // 0 = ROLLBACK, >0 = ACCEPT
    console.log('Return string:', xrpl.convertHexToString(ex.HookReturnString || ''));
    console.log('Instructions:', ex.HookInstructionCount);
    console.log('Emitted count:', ex.HookEmitCount);
  }
}

// Emitted transactions appear as their own validated txns with EmitDetails set
```

---

## 17. Xahau-Specific Patterns

### 17.1 Connecting to Xahau

```javascript
// Mainnet
const xahau = new xrpl.Client('wss://xahau.network');

// Testnet
const xahauTest = new xrpl.Client('wss://xahau-test.net');

await xahau.connect();

// Verify you're on Xahau, not XRPL
const serverInfo = await xahau.request({ command: 'server_info' });
console.log('Network ID:', serverInfo.result.info.network_id);
// Xahau mainnet network_id = 21337
// Xahau testnet network_id = 21338
```

**Critical:** Xahau transactions require a `NetworkID` field for any network with `network_id >= 1024`. xrpl.js v4+ autofills this if the client is connected to that network — but verify.

```javascript
const tx = {
  TransactionType: 'Payment',
  Account: wallet.address,
  Destination: 'rDEST...',
  Amount: '1000000',
  NetworkID: 21337   // explicit, in case autofill misses it
};
```

### 17.2 XAH as Native Gas Token

Xahau's native asset is **XAH**, not XRP. The drops/decimal conversion is identical (1 XAH = 1,000,000 drops), but xrpl.js's helper is named `xrpToDrops` for legacy reasons — it works fine for XAH since the math is the same.

```javascript
// Convert XAH amounts using the same helpers
const oneXah = xrpl.xrpToDrops('1');  // '1000000'
const balance = await xahau.getXrpBalance(wallet.address);
console.log(`${balance} XAH`);   // returns XAH on Xahau, XRP on XRPL

// Fee on Xahau is dynamic and depends on installed hooks.
// autofill() queries the right base fee + hook fee automatically.
const prepared = await xahau.autofill(tx);
console.log('Computed Fee (drops of XAH):', prepared.Fee);
```

### 17.3 Differences from XRPL Mainnet

| Concept | XRPL | Xahau |
|---|---|---|
| Native asset | XRP | XAH |
| Reserves | base 1 XRP, owner 0.2 XRP | typically lower; check `server_state` |
| Hooks | not supported | native (`SetHook` tx) |
| Network ID | not required | required (21337 mainnet) |
| URITokens | NFTokenMint/Burn | URITokenMint/Burn (different tx types) |
| AMM | yes | not currently supported |
| Genesis amendments | full XRPL set | Xahau-specific, includes Hooks, Import, URIToken |

```javascript
// URIToken (Xahau equivalent of NFToken)
const uriMintTx = {
  TransactionType: 'URITokenMint',
  Account: wallet.address,
  URI: xrpl.convertStringToHex('ipfs://QmXXX...'),
  Digest: 'ABCD'.repeat(16),    // optional 32-byte sha512half of content
  Flags: 1                       // tfBurnable
};

// Import — bridge XRP from XRPL into Xahau as XAH
// Requires a sync tx from XRPL mainnet (the "blob") plus this Import tx
const importTx = {
  TransactionType: 'Import',
  Account: wallet.address,
  Blob: '...long hex from XRPL Burn2Mint tx...'
};
```

### 17.4 Hook Namespace & Parameter Conventions

```javascript
// Namespace: 32-byte hex, often sha256 of an ASCII tag
const crypto = require('crypto');
const namespace = crypto
  .createHash('sha256')
  .update('my-app:vault-v1')
  .digest('hex')
  .toUpperCase();

// Parameter encoding helpers
function paramName(s) {
  // Param names: max 32 bytes, ASCII hex
  return xrpl.convertStringToHex(s).padEnd(64, '0').slice(0, 64);
}
function paramUint64(n) {
  // 8-byte big-endian uint64 — common for thresholds, timestamps
  return BigInt(n).toString(16).padStart(16, '0').toUpperCase();
}

const params = [
  { HookParameter: {
      HookParameterName: paramName('MIN'),
      HookParameterValue: paramUint64(1_000_000)
  }},
  { HookParameter: {
      HookParameterName: paramName('ADMIN'),
      HookParameterValue: xrpl.decodeAccountID('rADMIN...').toString('hex').toUpperCase()
  }}
];
```

---

## 18. xrpl.js Beta / Advanced Features

### 18.1 MPT (Multi-Purpose Tokens)

MPTs are a newer token primitive: fungible, fixed-supply or capped, without a trustline. xrpl.js v4+ exposes the transactions; some helper utilities are still being polished.

```javascript
// Issue an MPT
const issuanceTx = {
  TransactionType: 'MPTokenIssuanceCreate',
  Account: issuer.address,
  AssetScale: 6,                    // 10^6 sub-units
  TransferFee: 100,                 // 0.1%
  MaximumAmount: '1000000000000',   // 1M whole tokens at scale 6
  Flags:
    0x00000002 |   // tfMPTCanLock
    0x00000020 |   // tfMPTCanTransfer
    0x00000040,    // tfMPTCanEscrow
  MPTokenMetadata: xrpl.convertStringToHex(JSON.stringify({
    name: 'My Token', ticker: 'MYT', icon: 'ipfs://...'
  }))
};

const r1 = await client.submitAndWait(
  (await issuer.sign(await client.autofill(issuanceTx))).tx_blob
);

// Extract the MPTokenIssuanceID
const issuanceId = r1.result.meta.AffectedNodes
  .map(n => n.CreatedNode)
  .find(n => n?.LedgerEntryType === 'MPTokenIssuance')
  ?.LedgerIndex;

// Holder authorizes (opt-in) before receiving
const authTx = {
  TransactionType: 'MPTokenAuthorize',
  Account: holder.address,
  MPTokenIssuanceID: issuanceId
};

// Send MPT
const sendTx = {
  TransactionType: 'Payment',
  Account: issuer.address,
  Destination: holder.address,
  Amount: {
    mpt_issuance_id: issuanceId,
    value: '100'
  }
};
```

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

```javascript
// DIDSet — create or update a DID document on-ledger
const didSetTx = {
  TransactionType: 'DIDSet',
  Account: wallet.address,
  // At least one of URI, Data, DIDDocument must be set
  URI: xrpl.convertStringToHex('https://example.com/did.json'),
  Data: xrpl.convertStringToHex('arbitrary metadata'),
  DIDDocument: xrpl.convertStringToHex(JSON.stringify({
    '@context': 'https://www.w3.org/ns/did/v1',
    id: `did:xrpl:1:${wallet.address}`,
    verificationMethod: [{
      id: `did:xrpl:1:${wallet.address}#keys-1`,
      type: 'Ed25519VerificationKey2020',
      controller: `did:xrpl:1:${wallet.address}`,
      publicKeyMultibase: 'z' + wallet.publicKey
    }]
  }))
};

await client.submitAndWait(
  (await wallet.sign(await client.autofill(didSetTx))).tx_blob
);

// DIDDelete
const didDeleteTx = {
  TransactionType: 'DIDDelete',
  Account: wallet.address
};

// Look up a DID
const didLookup = await client.request({
  command: 'ledger_entry',
  did: wallet.address,
  ledger_index: 'validated'
});
const didDoc = xrpl.convertHexToString(
  didLookup.result.node.DIDDocument || ''
);
console.log('DID Document:', didDoc);
```

**Note:** these features require their respective amendments to be enabled on the network. Check `feature` RPC or `server_info.amendment_blocked`.

---

## Related Files

- `knowledge/30-xrpl-xrplpy.md` — Python equivalent
- `knowledge/41-xrpl-bots-patterns.md` — bot patterns in JavaScript
