# XRPL AMM Bot Patterns

## Overview

AMM (Automated Market Maker) bots on the XRPL interact with liquidity pools created via the AMM amendment. Key strategies include: price monitoring, arbitrage between AMM and DEX order books, liquidity provision, impermanent loss hedging, and AMMBid auction slot management.

---

## 1. AMM Basics

XRPL AMM uses the constant-product formula `x × y = k`, same as Uniswap v2:

```
price = asset2_amount / asset1_amount

After swap:
(asset1 + Δin) × (asset2 - Δout) = k
Δout = asset2 × Δin / (asset1 + Δin)

With trading fee f (e.g., 0.5% = 0.005):
effective_Δin = Δin × (1 - f)
Δout = asset2 × effective_Δin / (asset1 + effective_Δin)
```

---

## 2. AMM Info Query

```python
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AMMInfo

client = JsonRpcClient("https://xrplcluster.com")

# Query by asset pair
resp = client.request(AMMInfo(
    asset={
        "currency": "XRP"
    },
    asset2={
        "currency": "USD",
        "issuer": "rhub8VRN55s94qWKDv6jmDy1pUykJzF3wq"
    }
))

amm = resp.result["amm"]
print(f"AMM account: {amm['account']}")
print(f"XRP amount: {int(amm['amount']) / 1e6:.6f}")
print(f"USD amount: {amm['amount2']['value']}")
print(f"Trading fee: {amm['trading_fee'] / 1000:.3f}%")
print(f"LP token: {amm['lp_token']['currency']} ({amm['lp_token']['issuer']})")

# Compute price
xrp_pool = int(amm['amount']) / 1e6
usd_pool = float(amm['amount2']['value'])
price_per_xrp = usd_pool / xrp_pool
print(f"Price: {price_per_xrp:.4f} USD/XRP")
```

---

## 3. Price Monitoring Bot

```python
import asyncio
import time
from dataclasses import dataclass, field
from collections import deque
from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.models.requests import AMMInfo

@dataclass
class PricePoint:
    timestamp: float
    price: float
    xrp_pool: float
    usd_pool: float
    fee: float

class AMMPriceMonitor:
    def __init__(self, asset2_currency: str, asset2_issuer: str, interval: float = 4.0):
        self.asset2_currency = asset2_currency
        self.asset2_issuer = asset2_issuer
        self.interval = interval
        self.history = deque(maxlen=100)
        self.on_price_change = None
    
    async def fetch_price(self) -> PricePoint:
        async with AsyncJsonRpcClient("https://xrplcluster.com") as client:
            resp = await client.request(AMMInfo(
                asset={"currency": "XRP"},
                asset2={"currency": self.asset2_currency, "issuer": self.asset2_issuer}
            ))
        
        amm = resp.result["amm"]
        xrp = int(amm["amount"]) / 1e6
        token = float(amm["amount2"]["value"])
        fee = amm["trading_fee"] / 100000
        
        return PricePoint(
            timestamp=time.time(),
            price=token / xrp,
            xrp_pool=xrp,
            usd_pool=token,
            fee=fee
        )
    
    async def start(self):
        while True:
            try:
                point = await self.fetch_price()
                
                if self.history:
                    prev = self.history[-1]
                    change_pct = abs(point.price - prev.price) / prev.price * 100
                    if change_pct > 0.1 and self.on_price_change:
                        await self.on_price_change(point, change_pct)
                
                self.history.append(point)
                print(f"Price: {point.price:.6f} USD/XRP | Pool: {point.xrp_pool:.2f} XRP / {point.usd_pool:.2f} USD")
            
            except Exception as e:
                print(f"Monitor error: {e}")
            
            await asyncio.sleep(self.interval)
    
    def vwap(self, n: int = 20) -> float:
        """Volume-weighted average price (simplified)."""
        recent = list(self.history)[-n:]
        if not recent:
            return 0
        return sum(p.price for p in recent) / len(recent)
    
    def spread_from_vwap(self) -> float:
        if not self.history:
            return 0
        current = self.history[-1].price
        vwap = self.vwap()
        return (current - vwap) / vwap * 100

# Usage
monitor = AMMPriceMonitor("USD", "rhub8VRN55s94qWKDv6jmDy1pUykJzF3wq")

async def on_price_change(point, change_pct):
    print(f"⚠️ Price change: {change_pct:.2f}% → {point.price:.6f}")

monitor.on_price_change = on_price_change
asyncio.run(monitor.start())
```

---

## 4. DEX vs AMM Arbitrage

When the AMM price diverges from DEX order book prices, arbitrage restores equilibrium:

```python
from xrpl.models.requests import BookOffers, AMMInfo

async def find_arbitrage_opportunity(
    currency: str,
    issuer: str,
    min_profit_pct: float = 0.3
) -> dict | None:
    
    async with AsyncJsonRpcClient("https://xrplcluster.com") as client:
        # Get AMM price
        amm_resp = await client.request(AMMInfo(
            asset={"currency": "XRP"},
            asset2={"currency": currency, "issuer": issuer}
        ))
        amm = amm_resp.result["amm"]
        amm_xrp = int(amm["amount"]) / 1e6
        amm_token = float(amm["amount2"]["value"])
        amm_price = amm_token / amm_xrp  # token per XRP
        amm_fee = amm["trading_fee"] / 100000
        
        # Get DEX best bid/ask
        # Buy token from DEX (paying XRP)
        dex_buy_resp = await client.request(BookOffers(
            taker_gets={"currency": currency, "issuer": issuer},
            taker_pays={"currency": "XRP"},
            limit=5
        ))
        
        # Sell token to DEX (receiving XRP)
        dex_sell_resp = await client.request(BookOffers(
            taker_gets={"currency": "XRP"},
            taker_pays={"currency": currency, "issuer": issuer},
            limit=5
        ))
        
        dex_offers_buy = dex_buy_resp.result.get("offers", [])
        dex_offers_sell = dex_sell_resp.result.get("offers", [])
        
        if not dex_offers_buy or not dex_offers_sell:
            return None
        
        # Best DEX prices
        best_dex_buy_offer = dex_offers_buy[0]
        best_dex_sell_offer = dex_offers_sell[0]
        
        # Price: token/XRP
        dex_ask = float(best_dex_buy_offer["quality"])   # buying token cheaply
        dex_bid = 1 / float(best_dex_sell_offer["quality"])  # selling token
        
        # Effective AMM price with fees
        amm_effective_buy = amm_price * (1 + amm_fee)   # cost to buy from AMM
        amm_effective_sell = amm_price * (1 - amm_fee)  # receive from AMM
        
        # Arb: buy from DEX, sell to AMM
        if dex_ask < amm_effective_sell:
            profit_pct = (amm_effective_sell - dex_ask) / dex_ask * 100
            if profit_pct >= min_profit_pct:
                return {
                    "direction": "buy_dex_sell_amm",
                    "dex_price": dex_ask,
                    "amm_price": amm_effective_sell,
                    "profit_pct": profit_pct
                }
        
        # Arb: buy from AMM, sell to DEX
        if amm_effective_buy < dex_bid:
            profit_pct = (dex_bid - amm_effective_buy) / amm_effective_buy * 100
            if profit_pct >= min_profit_pct:
                return {
                    "direction": "buy_amm_sell_dex",
                    "amm_price": amm_effective_buy,
                    "dex_price": dex_bid,
                    "profit_pct": profit_pct
                }
    
    return None
```

---

## 5. Liquidity Provision Strategy

```python
from xrpl.models.transactions import AMMDeposit
from xrpl.models.transactions.amm_deposit import AMMDepositFlag

async def add_balanced_liquidity(
    wallet,
    xrp_amount: float,
    currency: str,
    issuer: str,
    client
):
    """Deposit both assets proportionally."""
    
    # Get current pool ratios
    amm_resp = await client.request(AMMInfo(
        asset={"currency": "XRP"},
        asset2={"currency": currency, "issuer": issuer}
    ))
    amm = amm_resp.result["amm"]
    
    xrp_pool = int(amm["amount"])  # drops
    token_pool = float(amm["amount2"]["value"])
    
    # Calculate token amount needed for balanced deposit
    token_ratio = token_pool / (xrp_pool / 1e6)
    token_amount = str(round(xrp_amount * token_ratio, 8))
    
    tx = AMMDeposit(
        account=wallet.address,
        asset={"currency": "XRP"},
        asset2={"currency": currency, "issuer": issuer},
        amount=str(int(xrp_amount * 1e6)),  # drops
        amount2={"currency": currency, "issuer": issuer, "value": token_amount},
        flags=AMMDepositFlag.TF_TWO_ASSET,
        fee="12"
    )
    
    signed = await autofill_and_sign(tx, wallet, client)
    result = await submit_and_wait(signed, client)
    
    return result
```

---

## 6. Impermanent Loss Calculation

```python
import math

def impermanent_loss(price_ratio_change: float) -> float:
    """
    Calculate impermanent loss percentage.
    price_ratio_change = new_price / initial_price
    
    Returns: loss as percentage (negative = loss)
    """
    r = price_ratio_change
    il = 2 * math.sqrt(r) / (1 + r) - 1
    return il * 100

# Examples
print(f"2x price change: {impermanent_loss(2):.2f}%")   # -5.72%
print(f"3x price change: {impermanent_loss(3):.2f}%")   # -13.40%
print(f"5x price change: {impermanent_loss(5):.2f}%")   # -25.46%
print(f"10x price change: {impermanent_loss(10):.2f}%")  # -42.26%

def should_withdraw_liquidity(
    initial_xrp_price: float,
    current_xrp_price: float,
    fees_earned_pct: float,
    il_threshold_pct: float = -5.0
) -> bool:
    """Withdraw if impermanent loss exceeds fee earnings."""
    price_ratio = current_xrp_price / initial_xrp_price
    il = impermanent_loss(price_ratio)
    net_return = il + fees_earned_pct
    return net_return < il_threshold_pct
```

---

## 7. Multi-Pool Analysis

```python
import asyncio
from xrpl.models.requests import LedgerData

async def scan_all_amm_pools() -> list:
    """Get all AMM pools from ledger data."""
    pools = []
    marker = None
    
    async with AsyncJsonRpcClient("https://xrplcluster.com") as client:
        while True:
            params = {
                "ledger_index": "validated",
                "type": "amm",
                "limit": 400
            }
            if marker:
                params["marker"] = marker
            
            resp = await client.request(LedgerData(**params))
            
            for obj in resp.result.get("state", []):
                if obj.get("LedgerEntryType") == "AMM":
                    asset1 = obj.get("Asset", {})
                    asset2 = obj.get("Asset2", {})
                    
                    pools.append({
                        "id": obj.get("index"),
                        "account": obj.get("Account"),
                        "asset1": asset1,
                        "asset2": asset2,
                        "trading_fee": obj.get("TradingFee", 0),
                        "lp_token_balance": obj.get("LPTokenBalance")
                    })
            
            marker = resp.result.get("marker")
            if not marker:
                break
    
    return pools

# Sort by TVL (requires fetching individual AMM info)
async def get_pools_by_tvl(xrp_price_usd: float = 0.5) -> list:
    pools = await scan_all_amm_pools()
    
    async def enrich(pool):
        try:
            async with AsyncJsonRpcClient("https://xrplcluster.com") as client:
                resp = await client.request(AMMInfo(
                    asset=pool["asset1"],
                    asset2=pool["asset2"]
                ))
                amm = resp.result["amm"]
                
                if isinstance(amm.get("amount"), str):
                    xrp_value = int(amm["amount"]) / 1e6 * xrp_price_usd * 2
                    pool["tvl_usd"] = xrp_value
                else:
                    pool["tvl_usd"] = 0
        except:
            pool["tvl_usd"] = 0
        return pool
    
    enriched = await asyncio.gather(*[enrich(p) for p in pools[:50]])
    return sorted(enriched, key=lambda p: p.get("tvl_usd", 0), reverse=True)
```

---

## 8. Trading Fee Optimization

Vote to lower fee if you have LP tokens:

```python
from xrpl.models.transactions import AMMVote

async def vote_for_fee(wallet, currency: str, issuer: str, new_fee: int, client):
    """
    new_fee: fee in 1/100000 units
    500 = 0.5%, 200 = 0.2%, 1000 = 1%
    """
    tx = AMMVote(
        account=wallet.address,
        asset={"currency": "XRP"},
        asset2={"currency": currency, "issuer": issuer},
        trading_fee=new_fee,
        fee="12"
    )
    
    signed = await autofill_and_sign(tx, wallet, client)
    result = await submit_and_wait(signed, client)
    return result

# Fee is weighted average of votes proportional to LP token holdings
# Max: 1000 (1%), Min: 0 (0%)
```

---

## 9. AMMBid Auction Slot

The auction slot gives the holder discounted trading fees for up to 24 hours. The effective fee decays linearly from 0% at slot acquisition back toward the pool's `base_fee` as the slot expires:

```
effective_fee = (1 - slot_ratio) * base_fee

where:
  slot_ratio  = time_elapsed_since_bid / 86400  (0.0 → 1.0 over 24h)
  base_fee    = pool's current TradingFee (e.g. 500 = 0.5%)

Examples:
  Just won slot (slot_ratio=0.0): effective_fee = 0%
  12h elapsed  (slot_ratio=0.5): effective_fee = base_fee * 0.5
  Slot expired (slot_ratio=1.0): effective_fee = base_fee (no discount)
```

```python
from xrpl.models.transactions import AMMBid

async def bid_for_auction_slot(
    wallet,
    currency: str,
    issuer: str,
    lp_token_bid: str,  # LP token amount to bid
    authorized_accounts: list,  # accounts that share the discount
    client
):
    """
    Bid LP tokens for the auction slot.
    Winner pays effective trading fee of 0% for 24 hours.
    """
    
    lp_token_info = await get_lp_token_info(currency, issuer, client)
    
    tx = AMMBid(
        account=wallet.address,
        asset={"currency": "XRP"},
        asset2={"currency": currency, "issuer": issuer},
        bid_min={
            "currency": lp_token_info["currency"],
            "issuer": lp_token_info["issuer"],
            "value": lp_token_bid
        },
        auth_accounts=[{"account": acc} for acc in authorized_accounts[:4]],
        fee="12"
    )
    
    signed = await autofill_and_sign(tx, wallet, client)
    result = await submit_and_wait(signed, client)
    
    if result.result["meta"]["TransactionResult"] == "tesSUCCESS":
        print(f"Auction slot won! Reduced fee for 24 hours.")
        # Fee reduction formula: effective_fee = (1 - slot_ratio) * base_fee
        # slot_ratio = time_elapsed / 24h (0.0 at start, 1.0 at end)
        # At slot_ratio=0 (just won): effective_fee = 1.0 * 0 = 0% (full discount)
        # At slot_ratio=0.5 (halfway): effective_fee = 0.5 * base_fee
        # At slot_ratio=1.0 (expired): slot reverts to base_fee
    return result

async def get_lp_token_info(currency, issuer, client):
    resp = await client.request(AMMInfo(
        asset={"currency": "XRP"},
        asset2={"currency": currency, "issuer": issuer}
    ))
    return resp.result["amm"]["lp_token"]
```

---

## 10. AMM Swap Simulation

Before executing, simulate the swap outcome:

```python
def simulate_amm_swap(
    pool_xrp: float,
    pool_token: float,
    sell_xrp: float,
    fee_bps: int = 500  # 500 = 0.5%
) -> dict:
    """
    Calculate output when selling XRP into the AMM.
    fee_bps: fee in 1/100000 units (same as trading_fee field)
    """
    fee = fee_bps / 100000
    effective_input = sell_xrp * (1 - fee)
    
    # constant product formula
    token_out = pool_token * effective_input / (pool_xrp + effective_input)
    
    # Price impact
    price_before = pool_token / pool_xrp
    price_after = (pool_token - token_out) / (pool_xrp + sell_xrp)
    price_impact_pct = abs(price_after - price_before) / price_before * 100
    
    return {
        "xrp_in": sell_xrp,
        "token_out": token_out,
        "price_before": price_before,
        "price_after": price_after,
        "price_impact_pct": price_impact_pct,
        "effective_rate": token_out / sell_xrp
    }

# Example
result = simulate_amm_swap(
    pool_xrp=100000,     # 100k XRP in pool
    pool_token=50000,    # 50k tokens in pool
    sell_xrp=1000,       # swap 1000 XRP
    fee_bps=500          # 0.5% fee
)
print(f"Expected output: {result['token_out']:.4f} tokens")
print(f"Price impact: {result['price_impact_pct']:.3f}%")
```

---

## Related Files

- `knowledge/04-xrpl-dex.md` — DEX order-book interaction
- `knowledge/05-xrpl-amm.md` — AMM mechanics
- `knowledge/41-xrpl-bots-patterns.md` — general bot architecture
