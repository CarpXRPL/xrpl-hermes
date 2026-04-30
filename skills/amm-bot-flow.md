# AMM Bot Flow

Arbitrage bot pattern using XRPL AMM pools combined with DEX order book pathfinding.

## Architecture

```
Bot wallet
  ├── Monitor AMM pool spot price (AMMInfo)
  ├── Monitor DEX best bid/ask (BookOffers)
  ├── Calculate arbitrage spread
  └── If spread > threshold:
        ├── Path A: Buy cheap on DEX → sell into AMM
        └── Path B: Buy cheap from AMM → sell on DEX
```

---

## Step 1 — Query AMM Pool State

```python
import httpx, json

def get_amm_info(asset1: dict, asset2: dict, endpoint="https://xrplcluster.com"):
    """Fetch AMM pool info. asset1/asset2 are currency objects."""
    payload = {
        "method": "amm_info",
        "params": [{"asset": asset1, "asset2": asset2, "ledger_index": "validated"}]
    }
    resp = httpx.post(endpoint, json=payload, timeout=10)
    return resp.json().get("result", {}).get("amm", {})

# XRP/USD pool
amm = get_amm_info(
    {"currency": "XRP"},
    {"currency": "USD", "issuer": "rhub8VRN55s94qWKDv6jmDy1pUykJzF3wq"}
)
pool = amm.get("amount", {}), amm.get("amount2", {})
lp_token = amm.get("lp_token", {})
trading_fee = amm.get("trading_fee", 0)  # in units of 1/1000th of 1%
print(f"XRP pool: {pool[0]}, USD pool: {pool[1]}")
print(f"Spot price: {float(pool[1].get('value', 0)) / (int(pool[0]) / 1e6):.6f} USD/XRP")
print(f"Trading fee: {trading_fee / 1000:.3f}%")
```

---

## Step 2 — Query DEX Order Book

```bash
python3 scripts/xrpl_tools.py book-offers USD:rhub8VRN55s94qWKDv6jmDy1pUykJzF3wq XRP
```

```python
from xrpl.models.requests import BookOffers
from xrpl.models.currencies import XRP as XRPCurrency, IssuedCurrency

def get_best_offer(client, taker_gets, taker_pays, limit=5):
    req = BookOffers(taker_gets=taker_gets, taker_pays=taker_pays, limit=limit)
    resp = client.request(req)
    offers = resp.result.get("offers", [])
    if not offers:
        return None
    best = offers[0]
    gets = best.get("TakerGets", {})
    pays = best.get("TakerPays", {})
    return {"offer": best, "gets": gets, "pays": pays}

best_ask = get_best_offer(
    client,
    taker_gets=IssuedCurrency(currency="USD", issuer="rhub8VRN55s94qWKDv6jmDy1pUykJzF3wq"),
    taker_pays=XRPCurrency(),
)
```

---

## Step 3 — Arbitrage Calculation

```python
def calculate_amm_spot(xrp_pool_drops: int, usd_pool_val: float) -> float:
    """AMM constant-product spot price: USD per XRP."""
    return usd_pool_val / (xrp_pool_drops / 1e6)

def calculate_dex_price(offer: dict) -> float:
    """DEX best ask price: USD per XRP from taker_gets/taker_pays."""
    gets_usd = float(offer["gets"].get("value", 0))
    pays_xrp = int(offer["pays"]) / 1e6 if isinstance(offer["pays"], str) else 0
    return gets_usd / pays_xrp if pays_xrp > 0 else 0

def find_arbitrage(amm_price: float, dex_price: float, fee_bps: float) -> dict:
    spread = (dex_price - amm_price) / amm_price
    net_spread = spread - (fee_bps / 10000)
    return {
        "amm_price": amm_price,
        "dex_price": dex_price,
        "gross_spread": spread,
        "net_spread_after_fee": net_spread,
        "direction": "buy_amm_sell_dex" if net_spread > 0 else "buy_dex_sell_amm",
        "profitable": abs(net_spread) > 0.001,  # > 0.1% net
    }
```

---

## Step 4 — Execute Arbitrage via Path Payment

When AMM is cheaper than DEX (buy from AMM, sell on DEX):

```bash
# Find best path
python3 scripts/xrpl_tools.py path-find rBOT rBOT 100 USD:rISSUER

# Execute cross-currency payment through AMM
python3 scripts/xrpl_tools.py build-cross-currency-payment \
  --from rBOT \
  --to rBOT \
  --deliver USD:rhub8VRN55s94qWKDv6jmDy1pUykJzF3wq:100 \
  --send-max XRP:1900000
```

When DEX is cheaper than AMM (buy from DEX, deposit to AMM):

```bash
# Buy USD on DEX first via OfferCreate
python3 scripts/xrpl_tools.py build-offer \
  --from rBOT \
  --sell XRP:1900000 \
  --buy USD:rhub8VRN55s94qWKDv6jmDy1pUykJzF3wq:100

# Then deposit to AMM (single-asset deposit)
python3 scripts/xrpl_tools.py build-amm-deposit \
  --from rBOT \
  --asset1 XRP \
  --asset2 USD:rhub8VRN55s94qWKDv6jmDy1pUykJzF3wq \
  --amount1 USD:rhub8VRN55s94qWKDv6jmDy1pUykJzF3wq:50 \
  --mode single-asset
```

---

## Step 5 — AMM Auction Slot (Advanced)

Bots can bid for the AMM auction slot to get a reduced trading fee for 24 hours:

```bash
python3 scripts/xrpl_tools.py build-amm-bid \
  --from rBOT \
  --asset1 XRP \
  --asset2 USD:rhub8VRN55s94qWKDv6jmDy1pUykJzF3wq \
  --bid-min "03C0A8F4B16F000000000000000000000000000B:rAMMPOOL:10"
```

```python
# Check current auction slot
amm_data = get_amm_info(...)
slot = amm_data.get("auction_slot", {})
print(f"Slot price: {slot.get('price', {})}")
print(f"Slot expiry: {slot.get('expiration', 'N/A')}")
print(f"Discounted fee: {slot.get('discounted_fee', 0) / 1000:.3f}%")
```

---

## Step 6 — Bot Loop Pattern

```python
import time

POLL_INTERVAL = 4  # seconds (one ledger)
MIN_SPREAD = 0.002  # 0.2% net

while True:
    try:
        amm = get_amm_info(XRP_ASSET, USD_ASSET)
        xrp_pool = int(amm["amount"])
        usd_pool = float(amm["amount2"]["value"])
        amm_price = calculate_amm_spot(xrp_pool, usd_pool)

        dex_offer = get_best_offer(client, USD_CURRENCY, XRP_CURRENCY)
        if not dex_offer:
            time.sleep(POLL_INTERVAL)
            continue

        dex_price = calculate_dex_price(dex_offer)
        arb = find_arbitrage(amm_price, dex_price, fee_bps=60)  # 0.6% AMM fee

        if arb["profitable"] and abs(arb["net_spread_after_fee"]) > MIN_SPREAD:
            print(f"Arb found: {arb['direction']}, spread={arb['net_spread_after_fee']:.4f}")
            # Build and sign transaction here
            execute_arbitrage(arb)

    except Exception as e:
        print(f"Bot error: {e}")
    time.sleep(POLL_INTERVAL)
```

---

## Common Mistakes

| Mistake | Fix |
|---|---|
| Not accounting for AMM trading fee | Fee range 0–1% (0–1000 bps) reduces profit |
| Sending exact amount without slippage buffer | Use `SendMax` 5–10% above expected to handle price movement |
| Race condition on ledger close | Check tx result before next action |
| Not monitoring LP position dilution | Other depositors change pool ratio |
| Ignoring transfer rate on issued currency | IOU transferRate reduces received amount |
| Running on testnet data vs mainnet | Check `XRPL_PRIVATE_RPC` env or endpoint |

---

## Verification

```bash
# Check bot wallet balance after each run
python3 scripts/xrpl_tools.py account rBOT
python3 scripts/xrpl_tools.py trustlines rBOT USD

# Monitor recent transactions
python3 -c "
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountTx
client = JsonRpcClient('https://xrplcluster.com')
resp = client.request(AccountTx(account='rBOT', limit=10))
for tx in resp.result.get('transactions', []):
    meta = tx.get('meta', {})
    print(tx['tx']['TransactionType'], meta.get('TransactionResult'))
"
```
