# XRPL Decentralized Exchange (DEX)

## Overview

The XRP Ledger has a built-in decentralized exchange (DEX) that operates as an order book-based trading system. It allows any account to create buy and sell offers for any pair of currencies (XRP/token or token/token) without a central intermediary. The DEX is part of the core protocol, not a smart contract.

## OfferCreate Transaction

The `OfferCreate` transaction places an order on the DEX. It can either execute immediately against existing offers (taking) or become a standing order on the order book (making).

### Fields

| Field | Required | JSON Type | Description |
|---|---|---|---|
| `TakerGets` | ✅ | String or Object | What the taker gets (the offer creator sells this) |
| `TakerPays` | ✅ | String or Object | What the taker pays (the offer creator wants this) |
| `Expiration` | ❌ | UInt32 | Ledger sequence when the offer expires |
| `OfferSequence` | ❌ | UInt32 | Sequence of a previous offer to cancel and replace |

### Example: Sell 100 XRP for USD

```json
{
  "TransactionType": "OfferCreate",
  "Account": "r9cZA1mLK5R5Am25ArfXFmqgN1sV5f3gQR",
  "TakerGets": "100000000",  // 100 XRP
  "TakerPays": {
    "currency": "USD",
    "issuer": "rIssuerAddress",
    "value": "50"
  },
  "Fee": "10",
  "Sequence": 20,
  "Flags": 0
}
```

This means: "I want to sell 100 XRP and receive at least 50 USD. I'm offering at a rate of 0.50 USD per XRP."

### Example: Buy 100 XRP for USD

```json
{
  "TransactionType": "OfferCreate",
  "Account": "rBuyerAddress",
  "TakerGets": {
    "currency": "USD",
    "issuer": "rIssuerAddress",
    "value": "100"
  },
  "TakerPays": "100000000",  // 100 XRP
  "Fee": "10",
  "Sequence": 15,
  "Flags": 0
}
```

This means: "I'll pay up to 100 USD to receive 100 XRP. My offer rate is 1.00 USD per XRP."

### Python Example

```python
from xrpl.transaction import submit_and_wait
from xrpl.models.transactions import OfferCreate
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.utils import xrp_to_drops

# Sell 100 XRP for USD
offer = OfferCreate(
    account="r9cZA1mLK5R5Am25ArfXFmqgN1sV5f3gQR",
    taker_gets=xrp_to_drops(100),
    taker_pays=IssuedCurrencyAmount(
        currency="USD",
        issuer="rIssuerAddress",
        value="50",
    ),
)
response = submit_and_wait(offer, client, wallet)
```

## Offer Matching Algorithm

The XRPL uses a **continuous limit order book** with the following matching rules:

### Quality Calculation

```
Quality = TakerPays / TakerGets
```

For an offer selling XRP for USD:
- TakerGets = 100 XRP (what the offer creator gives)
- TakerPays = 50 USD (what the offer creator receives)
- Quality = 50 / 100 = 0.5 (USD per XRP)

### Matching Priority

1. **Best quality first**: Offers with the best (lowest) quality are matched first
2. **Time priority**: Among offers with the same quality, older offers take priority
3. **Partial fills**: An offer can be partially filled, leaving a remainder on the books

### Full Consumption Example

```
Order Book: Offers to sell XRP for USD
- Offer A: Sell 100 XRP @ 0.50 USD/XRP (oldest)
- Offer B: Sell 100 XRP @ 0.50 USD/XRP
- Offer C: Sell 100 XRP @ 0.55 USD/XRP

New Buy Order: Buy 250 XRP @ 0.55 USD/XRP

Execution:
- Takes 100 XRP from Offer A (pays 50 USD)
- Takes 100 XRP from Offer B (pays 50 USD)
- Takes 50 XRP from Offer C (pays 27.5 USD)
Total: 250 XRP for 127.5 USD
```

### Partial Fill

If a new offer partially matches existing offers, the remainder becomes a new offer on the books.

```
Order Book: Offers to buy XRP for USD
- Offer A: Buy 100 XRP @ 0.50 USD/XRP

New Sell Order: Sell 150 XRP @ 0.50 USD/XRP

Execution:
- Takes 100 XRP from Offer A (receives 50 USD)
- 50 XRP remains as a new sell offer @ 0.50 USD/XRP
```

## Auto-Bridging

The XRPL automatically finds paths through XRP when there's no direct order book for a currency pair.

### How Auto-Bridging Works

If there's no EUR:JPY order book, but there are EUR:XRP and XRP:JPY books, the DEX automatically finds the best route:

```
Sell EUR → Buy XRP (via EUR:XRP offers)
Sell XRP → Buy JPY (via XRP:JPY offers)
Result: EUR → JPY through XRP
```

This liquidity aggregation is automatic — the trader doesn't need to do anything special.

## Offer Lifecycle

### States

1. **Created**: Offer is placed on the order book. Reserve (2 XRP) locked.
2. **Partially Filled**: Some of the offer has been consumed, remainder stays on books.
3. **Fully Filled**: All of the offer has been consumed. Offer removed from books.
4. **Cancelled**: Offer creator cancels it before it's filled.
5. **Expired**: Reached the `Expiration` ledger sequence without being filled.
6. **Consumed by Cross-Currency Payment**: Used as a hop in a payment path.

### Offer Create → Funded Check

Before executing an OfferCreate, the protocol checks if the account has sufficient funds:
- For XRP sales: Balance must cover what's being offered
- For token sales: Trust line balance must cover what's being offered

If insufficient, the offer is consumed as much as possible without becoming unfunded.

## OfferCancel Transaction

Remove an offer from the order book.

```json
{
  "TransactionType": "OfferCancel",
  "Account": "r9cZA1mLK5R5Am25ArfXFmqgN1sV5f3gQR",
  "OfferSequence": 20,
  "Fee": "10",
  "Sequence": 25
}
```

`OfferSequence` identifies which offer to cancel (it's the sequence number of the original `OfferCreate` transaction).

## Offer Flags

| Flag | Hex | Decimal | Description |
|---|---|---|---|
| `tfPassive` | 0x00010000 | 65536 | Offer can only be filled by existing offers; it cannot consume offers at own expense |
| `tfImmediateOrCancel` | 0x00020000 | 131072 | Execute immediately against matching offers; any unfilled portion is cancelled |
| `tfFillOrKill` | 0x00040000 | 262144 | Execute only if the entire amount can be filled; otherwise cancel entirely |
| `tfSell` | 0x00080000 | 524288 | Treat the offer as a sell (important for offers that trade identical currencies) |

### tfPassive

A passive offer waits for others to trade against it. It will never "eat" an offer at its own price level:

```json
{
  "TransactionType": "OfferCreate",
  "Account": "r9cZA1mLK5R5Am25ArfXFmqgN1sV5f3gQR",
  "TakerGets": "100000000",
  "TakerPays": {
    "currency": "USD",
    "issuer": "rIssuerAddress",
    "value": "50"
  },
  "Flags": 65536  // tfPassive
}
```

### tfImmediateOrCancel (IOC)

Fill what you can immediately, cancel the rest:

```json
{
  "TransactionType": "OfferCreate",
  "Account": "r9cZA1mLK5R5Am25ArfXFmqgN1sV5f3gQR",
  "TakerGets": "100000000",
  "TakerPays": {
    "currency": "USD",
    "issuer": "rIssuerAddress",
    "value": "50"
  },
  "Flags": 131072  // tfImmediateOrCancel
}
```

### tfFillOrKill (FOK)

Fill entirely or don't fill at all:

```json
{
  "TransactionType": "OfferCreate",
  "Account": "r9cZA1mLK5R5Am25ArfXFmqgN1sV5f3gQR",
  "TakerGets": "100000000",
  "TakerPays": {
    "currency": "USD",
    "issuer": "rIssuerAddress",
    "value": "50"
  },
  "Flags": 262144  // tfFillOrKill
}
```

### tfSell

Normally the XRPL treats offers as either buy or sell based on which direction gives better quality. `tfSell` forces the offer to be treated as a sell, which matters for exact-currency offers:

```json
{
  "TransactionType": "OfferCreate",
  "Account": "rUserAddress",
  "TakerGets": "100000000",
  "TakerPays": "100000000",
  "Flags": 524288  // tfSell — explicitly mark as sell
}
```

## Cross-Currency Payments Using DEX

The DEX is automatically used by the payment engine for cross-currency payments. When a payment specifies different currencies for send and receive, the engine finds paths through the DEX.

### How It Works

1. User submits a payment with `SendMax` and `Amount` in different currencies
2. Engine calls pathfinding to find routes
3. Routes may go through offers on the DEX
4. Offers consumed are atomic with the payment

### Direct vs Pathfinding

For simple XRP ↔ token swaps, the DEX is used directly:

```json
{
  "TransactionType": "Payment",
  "Account": "rUser",
  "Destination": "rReceiver",
  "Amount": {
    "currency": "USD",
    "issuer": "rIssuer",
    "value": "10"
  },
  "SendMax": "20000000",
  "Paths": "auto"
}
```

The engine will use the USD:XRP order book to convert XRP to USD, then deliver USD to the receiver.

## Querying Order Books

### book_offers RPC

Get offers on a specific order book:

```json
{
  "method": "book_offers",
  "params": [{
    "taker_gets": {
      "currency": "XRP"
    },
    "taker_pays": {
      "currency": "USD",
      "issuer": "rIssuerAddress"
    },
    "limit": 10
  }]
}
```

This returns offers to **sell XRP for USD**.

### Reverse Direction

```json
{
  "method": "book_offers",
  "params": [{
    "taker_gets": {
      "currency": "USD",
      "issuer": "rIssuerAddress"
    },
    "taker_pays": {
      "currency": "XRP"
    },
    "limit": 10
  }]
}
```

This returns offers to **buy XRP with USD** (i.e., sell USD for XRP).

## Reserve and Offers

Each offer on the DEX consumes 0.2 XRP of the account's owner reserve. An account with 5 active offers has:
- 1 XRP base reserve
- 1 XRP (5 × 0.2) for offers
- Total: 20 XRP locked

**Tip:** Cancel unfilled or unwanted offers to free up reserve. Use `account_objects` RPC to find all owned objects:

```json
{
  "method": "account_objects",
  "params": [{
    "account": "r9cZA1mLK5R5Am25ArfXFmqgN1sV5f3gQR",
    "type": "offer"
  }]
}
```

## Offer Replacement

To replace an existing offer, use `OfferSequence` to specify the offer to replace:

```json
{
  "TransactionType": "OfferCreate",
  "Account": "r9cZA1mLK5R5Am25ArfXFmqgN1sV5f3gQR",
  "TakerGets": "100000000",
  "TakerPays": {
    "currency": "USD",
    "issuer": "rIssuerAddress",
    "value": "55"
  },
  "OfferSequence": 20,  // Cancel old offer (created at Sequence 20)
  "Fee": "10",
  "Sequence": 21
}
```

This atomically cancels the old offer (at sequence 20) and creates a new one in a single transaction.
