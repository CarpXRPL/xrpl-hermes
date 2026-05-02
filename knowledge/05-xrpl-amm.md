# XRPL Automated Market Maker (AMM)

## Overview

The Automated Market Maker (AMM) on the XRP Ledger was introduced by the **XLS-30** amendment, which was enabled on mainnet in March 2024. AMMs provide decentralized liquidity pools that allow users to trade between two assets (XRP and a token, or two tokens) using a constant product formula, similar to Uniswap V2 on Ethereum, but integrated directly into the XRP Ledger protocol.

## AMM Architecture

An AMM pool is a specialized ledger entry that holds two assets and a pool of LP (Liquidity Provider) tokens. The pool has its own XRPL account (`amm_account`), which owns the assets.

### Key Components

- **Pool Assets**: Two assets held in reserve (XRP/token or token/token)
- **LP Tokens**: Represent ownership shares in the pool
- **Trading Fee**: Applied to every swap, paid to LP token holders
- **Auction Slot**: Accounts can bid for reduced fee rates

## AMMCreate Transaction

Creates a new AMM pool. The transaction simultaneously deposits both assets and issues LP tokens to the creator.

### Fields

| Field | Required | JSON Type | Description |
|---|---|---|---|
| `Amount` | ✅ | String or Object | First asset (XRP or token) |
| `Amount2` | ✅ | String or Object | Second asset (must be different from first) |
| `TradingFee` | ✅ | UInt32 | Fee in units of 1/100,000. Range: **0–1000** (0 = 0%, 1000 = 1%). E.g. 500 = 0.5% |

### Example: Create XRP/USD AMM

```json
{
  "TransactionType": "AMMCreate",
  "Account": "r9cZA1mLK5R5Am25ArfXFmqgN1sV5f3gQR",
  "Amount": "10000000000",  // 10,000 XRP
  "Amount2": {
    "currency": "USD",
    "issuer": "rIssuerAddress",
    "value": "5000"
  },
  "TradingFee": 500,  // 0.5% fee
  "Fee": "10",
  "Sequence": 30
}
```

The initial LP tokens are minted based on the geometric mean of the two deposits:
```
LP Tokens = sqrt(amount1 * amount2) ... simplified
```

### Python Example

```python
from xrpl.transaction import submit_and_wait
from xrpl.models.transactions import AMMCreate
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.utils import xrp_to_drops

amm_create = AMMCreate(
    account="r9cZA1mLK5R5Am25ArfXFmqgN1sV5f3gQR",
    amount=xrp_to_drops(10000),
    amount2=IssuedCurrencyAmount(
        currency="USD",
        issuer="rIssuerAddress",
        value="5000",
    ),
    trading_fee=500,  # 0.5%
)
response = submit_and_wait(amm_create, client, wallet)
```

## AMMDeposit Transaction

Deposits assets into an existing AMM pool and receives LP tokens (or can deposit single-sided).

### Fields

| Field | Required | JSON Type | Description |
|---|---|---|---|
| `Amount` | ❌ | String or Object | First asset to deposit |
| `Amount2` | ❌ | String or Object | Second asset to deposit |
| `Amount` variants | ❌ | - | See below |
| `EPrice` | �8 | String or Object | Effective price for single-asset deposit |

### Deposit Modes

#### Two-Asset Deposit (Equal Value)

Deposit both assets in proportion to the pool's current ratio:

```json
{
  "TransactionType": "AMMDeposit",
  "Account": "rUserAddress",
  "Amount": "1000000000",  // 1,000 XRP
  "Amount2": {
    "currency": "USD",
    "issuer": "rIssuerAddress",
    "value": "500"
  },
  "Flags": 0
}
```

#### Single-Asset Deposit

Deposit only one asset. The AMM automatically swaps some of it to maintain the pool balance:

```json
{
  "TransactionType": "AMMDeposit",
  "Account": "rUserAddress",
  "Amount": "500000000",  // 500 XRP (single-sided)
  "Flags": 1048576  // tfSingleAsset
}
```

This uses the `tfSingleAsset` flag (0x00100000 = 1048576).

### LP Tokens

The LP token is an issued currency with a special hex currency code derived from the pool's assets. The format is:

```
LP Token Currency = "03" + first_38_hex_chars_of_SHA512Half(canonical_pool_asset_pair)
```

The canonical form sorts the two assets deterministically (XRP sorts before tokens; tokens sort by currency+issuer). The resulting 20-byte currency code begins with `0x03`. The LP token's issuer is the AMM account itself (not a user account).

> **lsfAMM flag**: The AMM account has the `lsfAMM` flag set (0x02000000) in its AccountRoot, marking it as a protocol-controlled AMM account. It cannot send transactions and is not owned by any user.

## AMMWithdraw Transaction

Withdraws assets from an AMM pool, burning LP tokens.

### Fields

| Field | Required | JSON Type | Description |
|---|---|---|---|
| `Amount` | ❌ | String or Object | First asset to withdraw |
| `Amount2` | ❌ | String or Object | Second asset to withdraw |
| `EPrice` | ❌ | String or Object | Effective price for single-asset withdrawal |
| `LPTokenIn` | ❌ | IssuedCurrencyAmount | LP tokens to burn |

### Withdrawal Modes

#### Two-Asset Withdrawal (Equal Proportion)

```json
{
  "TransactionType": "AMMWithdraw",
  "Account": "rUserAddress",
  "Amount": "500000000",  // 500 XRP
  "Amount2": {
    "currency": "USD",
    "issuer": "rIssuerAddress",
    "value": "250"
  },
  "LPTokenIn": {
    "currency": "03...",
    "issuer": "rPoolAccount",
    "value": "1000"
  }
}
```

#### Single-Asset Withdrawal

```json
{
  "TransactionType": "AMMWithdraw",
  "Account": "rUserAddress",
  "Amount": "500000000",
  "Flags": 1048576  // tfSingleAsset
}
```

#### LP Token-Only Withdrawal (All Assets)

```json
{
  "TransactionType": "AMMWithdraw",
  "Account": "rUserAddress",
  "LPTokenIn": {
    "currency": "03...",
    "issuer": "rPoolAccount",
    "value": "1000"
  },
  "Flags": 2097152  // tfLPToken
}
```

## AMMBid Transaction

Bids on an auction slot to get reduced trading fees for a period of time.

```json
{
  "TransactionType": "AMMBid",
  "Account": "rUserAddress",
  "AuthSlot": {
    "account": "rUserAddress",
    "auth_slot_count": 0
  },
  "Amount": "10000000"  // 10 XRP bid
}
```

The highest bidder gets the auction slot, which reduces their trading fees for a certain timeframe.

## AMMVote Transaction

Vote on the trading fee of an AMM pool. LP holders can vote to increase or decrease the fee.

```json
{
  "TransactionType": "AMMVote",
  "Account": "rUserAddress",
  "TradingFee": 300,  // Vote for 0.3%
  "LPTokenIn": {
    "currency": "03...",
    "issuer": "rPoolAccount",
    "value": "1000"
  }
}
```

## amm_info RPC

Query AMM pool information:

```json
{
  "method": "amm_info",
  "params": [{
    "asset": {
      "currency": "XRP"
    },
    "asset2": {
      "currency": "USD",
      "issuer": "rIssuerAddress"
    }
  }]
}
```

### Response Example

```json
{
  "result": {
    "amm": {
      "account": "rp9vL6p5F5Q6R5F5Q6R5F5Q6R5F5Q6R5F5Q6R5F5",
      "amount": "50000000000",
      "amount2": {
        "currency": "USD",
        "issuer": "rIssuerAddress",
        "value": "25000"
      },
      "lp_token": {
        "currency": "0359ED4C8A5E5B5F5A5B5C5D5E5F5A5B5C5D5E5F5A5B5C5D5E5F5A5B5C5D5E",
        "issuer": "rp9vL6p5F5Q6R5F5Q6R5F5Q6R5F5Q6R5F5Q6R5F5",
        "value": "35355.33906"
      },
      "trading_fee": 500,
      "vote_slots": [
        {
          "account": "rUser1",
          "trading_fee": 500,
          "vote_weight": 2500
        }
      ],
      "auction_slot": null
    },
    "validated": true
  }
}
```

## Constant Product Formula

The AMM uses the constant product formula:

```
x * y = k
```

Where:
- `x` = reserve amount of asset 1
- `y` = reserve amount of asset 2
- `k` = constant product

When a trade swaps `Δx` of asset 1 for `Δy` of asset 2:

```
(x + Δx) * (y - Δy) = k
Δy = y - (k / (x + Δx))
```

With the trading fee applied:
- Fee portion of input = `Δx * fee_rate`
- Actual amount entering pool = `Δx * (1 - fee_rate)`
- `k` increases by the fee amount (paid to LP holders)

## LP Token Mechanics

LP tokens represent ownership of the pool. The token's currency code is a hex string beginning with `03` followed by 38 hex characters (SHA-512Half of the pool assets).

### LP Token Value

The value of LP tokens changes based on:
1. **Trading fees**: Accumulated fees increase the pool's value
2. **Price changes**: Impermanent loss from price divergence
3. **Deposits/Withdrawals**: Other LPs joining or leaving

### LP Token Math

```
Total LP Supply = sqrt(reserve1 * reserve2)
LP Share = User LP Balance / Total LP Supply
User's Share of Pool = LP Share * reserve1, LP Share * reserve2
```

## Impermanent Loss

Impermanent loss occurs when the price ratio of the two assets changes after you deposit. The loss is relative to simply holding the two assets outside the pool.

### Example

1. Deposit: 10,000 XRP + 5,000 USD (ratio 2:1)
2. XRP price doubles: Pool rebalances to maintain constant product
3. Withdraw: Get different amounts than deposited
4. Loss compared to just holding: ~5.7% for 2x price change

### Loss Table

| Price Change | Impermanent Loss |
|---|---|
| 1.25x | 0.6% |
| 1.5x | 2.0% |
| 2x | 5.7% |
| 3x | 13.4% |
| 4x | 20.0% |
| 5x | 25.5% |

## Slippage

Slippage is the difference between the expected price of a trade and the actual executed price. It occurs because large trades move the pool's price ratio.

### Slippage Calculation

For a trade of `Δx` on a pool with reserves `x` and `y`:

```
Expected Rate = y / x
Actual Rate = (y - Δy) / (x + Δx)
Slippage = (Expected Rate - Actual Rate) / Expected Rate
```

Larger trades relative to pool size cause more slippage.

## AMM + DEX Interaction (Arbitrage)

The AMM and the order book DEX coexist on the XRP Ledger. Arbitrageurs can profit from price differences between the two by:

1. **AMM → DEX**: If AMM price > DEX price, buy from DEX, sell to AMM
2. **DEX → AMM**: If DEX price > AMM price, buy from AMM, sell on DEX

This arbitrage activity keeps prices aligned across both venues.

### Cross-Venue Payment

The payment engine can route through both the AMM and the DEX in a single transaction, finding the best available rates across all liquidity sources.

## Practical Considerations

### Creating a Pool

Before creating an AMM pool:
1. Ensure both assets exist (XRP is native, tokens need trust lines)
2. Have enough reserve (AMM creation costs 2-4 XRP reserve for the pool account)
3. Choose a reasonable initial price ratio
4. Set an appropriate trading fee (0.25%-1% is typical)

### Liquidity Provision

- Provide liquidity in proportion to pool ratios for minimal slippage
- Single-asset deposits incur a fee (0.5% by default)
- LP tokens can be traded on the DEX or used elsewhere

### Risks

- **Impermanent loss**: Significant in volatile markets
- **Smart contract risk**: Despite being protocol-level, bugs are possible
- **Low liquidity risk**: Thin pools have high slippage
- **LP token price**: Can trade below NAV in some conditions

## AMM Flags

### Transaction Flags (AMMDeposit / AMMWithdraw)

| Flag | Hex | Decimal | Description |
|---|---|---|---|
| `tfSingleAsset` | 0x00100000 | 1048576 | Single-asset deposit/withdrawal |
| `tfTwoAsset` | 0x00200000 | 2097152 | Two-asset deposit/withdrawal |
| `tfOneAssetLPToken` | 0x00400000 | 4194304 | LP token-only deposit (single asset, receive LP tokens) |
| `tfLPToken` | 0x00800000 | 8388608 | LP token only withdrawal (burn LP tokens, receive both assets) |

### AccountRoot Flags (AMM account state)

| Flag | Hex | Description |
|---|---|---|
| `lsfAMM` | 0x02000000 | Marks this AccountRoot as an AMM account; the account is protocol-controlled |

## AMM on Testnet

AMM is available on testnet. To test:

1. Fund accounts with test XRP (faucet)
2. Create trust lines for test tokens
3. Create AMM pool
4. Test deposits, swaps, and withdrawals
5. Check pool state with `amm_info`

---

## Related Files

- `knowledge/04-xrpl-dex.md` — DEX order book interaction
- `knowledge/30-xrpl-xrplpy.md` — xrpl-py AMM transaction builders
- `knowledge/34-xrpl-amm-bots.md` — AMM rebalancing bots
- `knowledge/36-xrpl-xls-standards.md` — XLS-30 specification context
