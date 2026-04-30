# XRP Ledger L1 — Complete Reference

## Overview
The XRP Ledger (XRPL) is a decentralized, public blockchain built for payments. Uses a unique consensus protocol (not Proof of Work / not Proof of Stake). Confirms transactions in 3-5 seconds, handles 1,500+ TPS, costs fractions of a cent per tx.

**Key facts:**
- Native token: XRP (100 billion minted at genesis, no inflation)
- Validators: ~150+ UNL (Unique Node List)
- Consensus: XRPL Consensus Protocol (Byzantine fault tolerant, ~80% threshold)
- Ledger close time: 3-5 seconds
- Finality: Once included in a validated ledger, permanent
- Account reserve: 1 XRP base + 0.2 XRP per owned object (verify live with server_info)

## Accounts
- Format: base58, starts with `r` (e.g., `rD9yBuvcn8cCJf9up4JNZZkn5Zhcb1Zuog`)
- Key pair: secp256k1 or ed25519
- Created by sending minimum reserve (1 XRP) from an existing account
- Cannot be deleted (funds sent to genesis blackhole)
- Each account has a sequence number (increments with each tx)

### Account Flags
```json
{
  "lsfDefaultRipple": 0x00800000,  // Required for token issuers
  "lsfDepositAuth": 0x01000000,    // Only preauthorized can send
  "lsfDisableMasterKey": 0x00100000, // Master key disabled
  "lsfDisallowXRP": 0x00080000,    // Account disallows XRP
  "lsfGlobalFreeze": 0x00400000,   // All tokens frozen
  "lsfNoFreeze": 0x00200000,       // Cannot freeze tokens (permanent)
  "lsfRequireAuth": 0x00040000,    // Requires auth for trust lines
  "lsfRequireDestTag": 0x00020000  // Requires destination tag on payments
}
```

### Account Root Fields (on-ledger)
- `Balance`: XRP balance in drops (1 XRP = 1,000,000 drops)
- `Flags`: Bitmask of account flags
- `OwnerCount`: Number of objects owned (affects reserve)
- `Sequence`: Next transaction sequence number
- `Domain`: Hex-encoded domain (verified by DSN check)
- `EmailHash`: MD5 hash of email (legacy)
- `MessageKey`: Ed25519 or secp256k1 public key for encryption
- `RegularKey`: Regular key pair address (can sign but not change account)
- `TicketCount`: Number of tickets available
- `TickSize`: Number of significant digits in offers (5-15)
- `TransferRate`: Transfer fee charged by issuers (1.0 = no fee, 1.005 = 0.5%)

## Transaction Types

### Payment
```json
{
  "TransactionType": "Payment",
  "Account": "rSender",
  "Destination": "rReceiver",
  "Amount": "1000000",  // drops, or token format
  "DestinationTag": 12345,  // optional memo
  "InvoiceID": "...",  // optional
  "Paths": [],  // optional — auto-pathfinding
  "SendMax": "1000000",  // for partial payments
  "DeliverMin": "990000"  // for partial payments
}
```

### TrustSet
Create or modify a trust line to hold tokens:
```json
{
  "TransactionType": "TrustSet",
  "Account": "rTrustingAccount",
  "LimitAmount": {
    "currency": "USD",
    "issuer": "rIssuer",
    "value": "1000000"
  },
  "QualityIn": 0,  // optional exchange rate for inbound
  "QualityOut": 0  // optional exchange rate for outbound
}
```

### OfferCreate (DEX Order)
```json
{
  "TransactionType": "OfferCreate",
  "Account": "rTrader",
  "TakerGets": "1000000",  // paying XRP
  "TakerPays": {
    "currency": "USD",
    "issuer": "rIssuer",
    "value": "100"
  },
  "Expiration": 1234567890,  // optional expiry
  "OfferSequence": 0  // replace existing offer
}
```

### SignerListSet (Multi-signing)
Configure multi-signing with up to 32 signers:
```json
{
  "TransactionType": "SignerListSet",
  "Account": "rAccount",
  "SignerQuorum": 3,
  "SignerEntries": [
    {"SignerEntry": {"Account": "rSigner1", "SignerWeight": 1}},
    {"SignerEntry": {"Account": "rSigner2", "SignerWeight": 1}},
    {"SignerEntry": {"Account": "rSigner3", "SignerWeight": 1}},
    {"SignerEntry": {"Account": "rSigner4", "SignerWeight": 1}},
    {"SignerEntry": {"Account": "rSigner5", "SignerWeight": 1}}
  ]
}
```

### SetAccountRoot
```json
{
  "TransactionType": "SetAccountRoot",
  "Account": "rIssuer",
  "Domain": "6578616D706C652E636F6D",  // hex of "example.com"
  "EmailHash": "...",
  "MessageKey": "...",
  "SetFlag": 0x00800000,  // lsfDefaultRipple — required for issuers
  "ClearFlag": 0,  // clear a flag
  "TickSize": 5
}
```

## Token Operations

### Issuing Tokens
1. Set DefaultRipple flag on issuer account (lsfDefaultRipple)
2. Set TransferRate (optional, default 1.0 = no fee)
3. Set Domain (for verification)
4. Optional: Set RequireAuth flag + authorize trust lines manually

### AMM (Automated Market Maker)
XLS-30 amendment. Create AMM pools between any two assets on XRPL.

**AMMCreate:**
```json
{
  "TransactionType": "AMMCreate",
  "Account": "rProvider",
  "Amount": "1000000",  // XRP amount
  "Amount2": {
    "currency": "TOKEN",
    "issuer": "rIssuer",
    "value": "100"
  },
  "TradingFee": 600  // 600 = 0.6% fee (1/100,000 units)
}
```

**AMMDeposit / AMMWithdraw:**
Liquidity provision. LP tokens track proportional ownership.

**AMMBid:**
Bid on the auction slot for reduced trading fees.

**AMM pool structure:**
- `amm_account`: Special account holding the pool assets
- `lp_token_currency`: LP token identifier (unique per pool)
- `trading_fee`: Fee in 1/100,000 units
- Composition: two assets (XRP + token or token + token)

### NFTs (XLS-20)
**NFTokenMint:**
```json
{
  "TransactionType": "NFTokenMint",
  "Account": "rIssuer",
  "NFTokenTaxon": 0,
  "Issuer": "rIssuer",  // if different from Account
  "TransferFee": 5000,  // royalty in 1/1000 (5%)
  "Flags": 8,  // 1=burnable, 2=onlyXRP, 4=trustlines, 8=transferable
  "URI": "ipfs://..."  // metadata URI (max 256 bytes)
}
```

**NFTokenCreateOffer:** Create buy/sell offer.
**NFTokenAcceptOffer:** Accept existing offer.
**NFTokenBurn:** Burn an owned NFT.

### Clawback (XLS-39)
Allows token issuers to claw back tokens from holders. Requires:
- Issuer account sets `lsfAllowTrustLineClawback` flag (permanent, cannot be unset)
- Only works on trust lines created AFTER the amendment
- Clawback runs within 86400 ledgers (~48h) of the trust line being created

```json
{
  "TransactionType": "Clawback",
  "Account": "rIssuer",
  "Amount": {
    "currency": "TOKEN",
    "issuer": "rIssuer",
    "value": "1000"
  }
}
```

### MPTokens (XLS-70)
Multi-Purpose Tokens — next-gen token standard replacing IOUs:
- Single issuer, single currency
- Configurable: transfer fees, locking, freezing, authorization
- More efficient than trust lines
- Still in amendment process (not yet active on mainnet)

## DEX (Decentralized Exchange)

### Orderbook
- Uses OfferCreate to place orders
- Auto-matched by the consensus engine
- Offers executed in order of quality (price)
- Offers of equal quality sorted by time
- Partial fills supported, unfilled portion remains active

### Auto-Bridging
XRPL automatically routes through XRP as a bridge currency. If you offer TOKEN1/XRP and someone wants TOKEN2/XRP, the system can auto-bridge TOKEN1→XRP→TOKEN2.

### Pathfinding
Multi-hop payments through multiple issuers and currencies. Server computes `paths` parameter. Use with `SendMax` and `DeliverMin` for partial payments.

## Consensus

### Validators
- Run rippled with `[validator_token]`
- Published on UNL (Unique Node List)
- ~150 validators as of 2025
- Anyone can run a validator (but only UNL validators affect consensus)

### Amendment Process
1. Proposed by validator
2. 80% support for 2 weeks → enabled
3. If support drops below 80% → fails
4. Key amendments:
   - XLS-20 (NFTs) — enabled
   - XLS-30 (AMM) — enabled  
   - XLS-39 (Clawback) — enabled
   - XLS-70 (MPTs) — in progress
   - XLS-??? (Hooks on mainnet) — proposed

## Public API Endpoints

| Endpoint | URL | Use |
|----------|-----|-----|
| xrplcluster | `wss://xrplcluster.com` | Best public WS + JSON-RPC |
| Ripple 1 | `wss://s1.ripple.com` / `https://s1.ripple.com:51234` | Ripple's own |
| Ripple 2 | `wss://s2.ripple.com` / `https://s2.ripple.com:51234` | Ripple backup |
| xrpl.ws | `wss://xrpl.ws` | Public cluster |
| xrpl.to API | `https://api.xrpl.to/v1` | RESTful XRPL data |

## Data APIs

| Service | Base URL | Provides |
|---------|----------|----------|
| XRPSCAN | `https://api.xrpscan.com/api/v1` | Account, token, NFT, transaction data. Token search by name |
| xrpl.to | `https://api.xrpl.to/v1` | Token prices, AMM pools (60+ pool discovery), token detail enrichment, market data |
| Bithomp | `https://bithomp.com/api/v2` | AMM search, explorer, token metadata (requires API key) |
| XRPLMeta | `https://s1.xrplmeta.org` | Token names, website/social links, metadata |
| OnTheDEX | `https://api.onthedex.live` | DEX rates and pricing |
