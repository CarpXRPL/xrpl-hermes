# XRPL Data APIs

## Overview

Several third-party and ecosystem APIs provide enriched XRPL data beyond the raw ledger: token metadata, AMM pools, DEX quotes, price feeds, and explorer data. This document covers XRPSCAN, xrpl.to, Bithomp, XRPLMeta, and CoinGecko.

---

## 1. XRPSCAN API

Base URL: `https://api.xrpscan.com/api/v1`

### Account Info

```
GET /account/{address}
```

```python
import httpx

async def get_account_xrpscan(address: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://api.xrpscan.com/api/v1/account/{address}"
        )
        resp.raise_for_status()
        return resp.json()

# Response includes:
# account, balance, ownerCount, sequence, 
# username (if set), domain, kyc status,
# activation info, flags
```

Response example:
```json
{
  "account": "rN7n3473SaZBCG4dFL83w7PB5MBhpqAzn",
  "balance": "25000000",
  "ownerCount": 3,
  "sequence": 100,
  "domain": "example.com",
  "emailHash": "...",
  "username": "MyWallet",
  "activation": {
    "ledger_index": 87000000,
    "timestamp": "2024-01-01T00:00:00Z",
    "via": "rFUNDER..."
  }
}
```

### Account Transactions

```
GET /account/{address}/transactions?marker=&limit=50
```

```python
async def get_all_txns(address: str) -> list:
    transactions = []
    marker = None
    
    while True:
        params = {"limit": 200}
        if marker:
            params["marker"] = marker
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://api.xrpscan.com/api/v1/account/{address}/transactions",
                params=params
            )
            data = resp.json()
        
        transactions.extend(data.get("transactions", []))
        marker = data.get("marker")
        if not marker:
            break
    
    return transactions
```

### Ledger Info

```
GET /ledger/{ledger_index}
GET /ledger/validated
```

### Validators

```
GET /validators
GET /validator/{validator_public_key}
```

---

## 2. xrpl.to API

Base URL: `https://api.xrpl.to/v1`  
(also `https://s1.xrpl.to/api/v1` as alternative)

### Token List

```
GET /tokens?page=1&limit=100&sortField=holders&sortOrder=desc
```

```python
async def get_top_tokens(limit: int = 100) -> list:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.xrpl.to/v1/tokens",
            params={
                "page": 1,
                "limit": limit,
                "sortField": "holders",
                "sortOrder": "desc",
                "filter": ""
            }
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("tokens", [])
```

Response per token:
```json
{
  "currency": "USD",
  "issuer": "rhub8VRN55s94qWKDv6jmDy1pUykJzF3wq",
  "name": "Bitstamp USD",
  "trustlines": 45230,
  "holders": 12045,
  "supply": "5000000",
  "price": 1.0002,
  "volume24h": 250000,
  "marketcap": 5001000
}
```

### Single Token Info

```
GET /token/{currency}/{issuer}
```

```python
async def get_token_info(currency: str, issuer: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://api.xrpl.to/v1/token/{currency}/{issuer}"
        )
        resp.raise_for_status()
        return resp.json()
```

### AMM Pools

```
GET /amm?page=1&limit=50&sortField=tvl&sortOrder=desc
```

```python
async def get_top_amm_pools(limit: int = 50) -> list:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.xrpl.to/v1/amm",
            params={
                "page": 1,
                "limit": limit,
                "sortField": "tvl",
                "sortOrder": "desc"
            }
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("amms", [])
```

AMM object:
```json
{
  "id": "AMMID...",
  "asset1": { "currency": "XRP" },
  "asset2": { "currency": "USD", "issuer": "rhub8VRN..." },
  "asset1_amount": "1000000",
  "asset2_amount": "500",
  "tvl_xrp": 2000000,
  "tvl_usd": 1000,
  "fee": 500,
  "lp_token": { "currency": "03930D02...", "issuer": "rAMM..." },
  "volume24h_xrp": 50000
}
```

### DEX Quote

```
GET /quote?source_currency=XRP&dest_currency=USD&dest_issuer=rhub8...&amount=100
```

```python
async def get_quote(
    source_currency: str,
    dest_currency: str,
    amount: str,
    dest_issuer: str = None,
    source_issuer: str = None
) -> dict:
    params = {
        "source_currency": source_currency,
        "dest_currency": dest_currency,
        "amount": amount
    }
    if dest_issuer:
        params["dest_issuer"] = dest_issuer
    if source_issuer:
        params["source_issuer"] = source_issuer
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.xrpl.to/v1/quote",
            params=params
        )
        resp.raise_for_status()
        return resp.json()

# Example: How much USD do I get for 100 XRP?
quote = await get_quote("XRP", "USD", "100", dest_issuer="rhub8VRN...")
print(f"Expected: {quote['dest_amount']} {quote['dest_currency']}")
print(f"Rate: {quote['rate']} XRP/USD")
print(f"Slippage: {quote['slippage_pct']}%")
```

---

## 3. Bithomp API

Base URL: `https://bithomp.com/api/v2`  
API key header: `x-bithomp-token: YOUR_KEY`

### AMM Search

```
GET /amms/search?currency1=XRP&currency2=USD&issuer2=rhub8...
```

```python
async def search_amm(
    currency1: str,
    currency2: str,
    issuer2: str = None,
    issuer1: str = None,
    api_key: str = None
) -> dict:
    headers = {}
    if api_key:
        headers["x-bithomp-token"] = api_key
    
    params = {
        "currency1": currency1,
        "currency2": currency2
    }
    if issuer2:
        params["issuer2"] = issuer2
    if issuer1:
        params["issuer1"] = issuer1
    
    async with httpx.AsyncClient(headers=headers) as client:
        resp = await client.get(
            "https://bithomp.com/api/v2/amms/search",
            params=params
        )
        resp.raise_for_status()
        return resp.json()
```

Response:
```json
{
  "amms": [
    {
      "ammID": "rAMM...",
      "asset1": { "currency": "XRP", "value": "1000000" },
      "asset2": { "currency": "USD", "issuer": "rhub8...", "value": "500" },
      "tradingFee": 500,
      "lpTokenBalance": "707.1068",
      "vote": []
    }
  ]
}
```

### Account Info

```
GET /address/{address}?username=true&service=true
```

```python
async def get_bithomp_account(address: str, api_key: str = None) -> dict:
    headers = {"x-bithomp-token": api_key} if api_key else {}
    
    async with httpx.AsyncClient(headers=headers) as client:
        resp = await client.get(
            f"https://bithomp.com/api/v2/address/{address}",
            params={"username": True, "service": True}
        )
        resp.raise_for_status()
        return resp.json()
```

### NFT Metadata

```
GET /nft/{nft_id}
```

---

## 4. XRPLMeta Token Metadata

Base URL: `https://api.xrplmeta.org`

```
GET /token/{currency}+{issuer}
```

```python
async def get_xrplmeta(currency: str, issuer: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://api.xrplmeta.org/token/{currency}+{issuer}"
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
```

Response:
```json
{
  "currency": "SOLO",
  "issuer": "rHZwvHEs56GCmHupwjA4RY7oPA3EoAJWuN",
  "meta": {
    "name": "Sologenic",
    "icon": "https://...",
    "website": "https://sologenic.com",
    "description": "DEX and tokenization platform",
    "twitter": "@Sologenic",
    "kyc": true
  },
  "metrics": {
    "holders": 5600,
    "supply": "400000000",
    "trustlines": 7800,
    "price_xrp": "0.08"
  }
}
```

### Token List

```
GET /tokens?limit=100&page=1
```

---

## 5. CoinGecko: XRP Price

```python
import httpx

class PriceFeed:
    COINGECKO = "https://api.coingecko.com/api/v3"
    
    def __init__(self, api_key: str = None):
        self.headers = {}
        if api_key:
            self.headers["x-cg-pro-api-key"] = api_key
    
    async def xrp_price_usd(self) -> float:
        async with httpx.AsyncClient(headers=self.headers) as client:
            resp = await client.get(
                f"{self.COINGECKO}/simple/price",
                params={
                    "ids": "ripple",
                    "vs_currencies": "usd",
                    "include_24hr_change": "true",
                    "include_market_cap": "true"
                }
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "price": data["ripple"]["usd"],
                "change_24h": data["ripple"]["usd_24h_change"],
                "market_cap": data["ripple"]["usd_market_cap"]
            }
    
    async def xrp_ohlc(self, days: int = 7) -> list:
        """Returns OHLC data: [timestamp, open, high, low, close]"""
        async with httpx.AsyncClient(headers=self.headers) as client:
            resp = await client.get(
                f"{self.COINGECKO}/coins/ripple/ohlc",
                params={"vs_currency": "usd", "days": days}
            )
            resp.raise_for_status()
            return resp.json()

feed = PriceFeed()
price_data = await feed.xrp_price_usd()
print(f"XRP: ${price_data['price']:.4f} ({price_data['change_24h']:.2f}%)")
```

---

## 6. Combining APIs: Full Token Profile

```python
async def full_token_profile(currency: str, issuer: str) -> dict:
    """Combine multiple APIs for complete token info."""
    
    xrpl_to, xrplmeta, bithomp = await asyncio.gather(
        get_token_info(currency, issuer),
        get_xrplmeta(currency, issuer),
        get_bithomp_account(issuer),
        return_exceptions=True
    )
    
    profile = {
        "currency": currency,
        "issuer": issuer,
    }
    
    if not isinstance(xrpl_to, Exception):
        profile.update({
            "name": xrpl_to.get("name"),
            "holders": xrpl_to.get("holders"),
            "supply": xrpl_to.get("supply"),
            "price_xrp": xrpl_to.get("price"),
            "volume24h": xrpl_to.get("volume24h"),
        })
    
    if not isinstance(xrplmeta, Exception) and xrplmeta:
        meta = xrplmeta.get("meta", {})
        profile.update({
            "website": meta.get("website"),
            "twitter": meta.get("twitter"),
            "icon": meta.get("icon"),
            "kyc": meta.get("kyc", False),
        })
    
    if not isinstance(bithomp, Exception):
        profile["issuer_name"] = bithomp.get("username") or bithomp.get("service", {}).get("name")
    
    return profile
```

---

## 7. Quick Reference: API Endpoints

| Data | API | Endpoint |
|------|-----|---------|
| XRP price | CoinGecko | `/simple/price?ids=ripple` |
| Top tokens | xrpl.to | `/v1/tokens` |
| Token metadata | XRPLMeta | `/token/{currency}+{issuer}` |
| AMM pools | xrpl.to | `/v1/amm` |
| AMM search | Bithomp | `/api/v2/amms/search` |
| DEX quote | xrpl.to | `/v1/quote` |
| Account info | XRPSCAN | `/api/v1/account/{address}` |
| TX history | XRPSCAN | `/api/v1/account/{address}/transactions` |
| NFT metadata | Bithomp | `/api/v2/nft/{nft_id}` |
| Validators | XRPSCAN | `/api/v1/validators` |
| Ledger info | XRPSCAN | `/api/v1/ledger/{index}` |
