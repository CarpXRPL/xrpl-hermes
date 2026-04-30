# XRPL Rate Limits & Retry Strategies

## Overview

All public XRPL endpoints enforce rate limits. This document covers per-endpoint limits, retry logic with exponential backoff, multi-client failover, and parallel request throttling for production use.

---

## 1. Public Endpoint Rate Limits

### XRPL RPC/WebSocket Nodes

| Endpoint | Type | Limit |
|----------|------|-------|
| `xrplcluster.com` (Clio) | HTTP/WS | ~20 req/s per IP |
| `s1.ripple.com` | WS full history | ~20 req/s per IP |
| `s2.ripple.com` | WS full history | ~20 req/s per IP |
| `xrpl.ws` | WS community | ~10 req/s per IP |
| `xrpl-mainnet.g.alchemy.com` | HTTP | Plan-based |

### xrpl.to API

| Endpoint | Limit |
|----------|-------|
| `/v1/tokens` | 30 req/min |
| `/v1/amm` | 30 req/min |
| `/v1/quote` | 30 req/min |
| `/v1/token/{currency}/{issuer}` | 30 req/min |
| Global per IP | 60 req/min |

### XRPSCAN API

| Endpoint | Limit |
|----------|-------|
| `/api/v1/account/{address}` | 120 req/min |
| `/api/v1/transactions` | 60 req/min |
| `/api/v1/ledger` | 120 req/min |
| Global per IP | 120 req/min |
| Pro API (API key) | 1200 req/min |

### Bithomp API

| Endpoint | Limit |
|----------|-------|
| `/api/v2/address/{address}` | 20 req/min |
| `/api/v2/amms/search` | 20 req/min |
| `/api/v2/nfts` | 20 req/min |
| API key (paid) | 2000 req/min |

### CoinGecko

| Endpoint | Limit |
|----------|-------|
| `/api/v3/simple/price` | 10–50 req/min (free) |
| `/api/v3/coins/ripple` | 10–50 req/min (free) |
| Pro API | 500 req/min |

### XRPLMeta

| Endpoint | Limit |
|----------|-------|
| `/token/{currency}+{issuer}` | 60 req/min |
| No authentication | Public |

---

## 2. Exponential Backoff Implementation

```python
import asyncio
import httpx
import random
from typing import Any

class RateLimitError(Exception):
    pass

async def request_with_backoff(
    url: str,
    payload: dict,
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True
) -> Any:
    """
    Exponential backoff with full jitter.
    Delay = min(max_delay, base_delay × 2^attempt) × random(0.5, 1.5)
    """
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(url, json=payload)
                
                if resp.status_code == 429:
                    retry_after = float(resp.headers.get("Retry-After", base_delay))
                    raise RateLimitError(f"Rate limited, retry after {retry_after}s")
                
                resp.raise_for_status()
                data = resp.json()
                
                if "error" in data.get("result", {}):
                    error = data["result"]["error"]
                    if error in ("slowDown", "tooBusy", "noNetwork"):
                        raise RateLimitError(f"Server overloaded: {error}")
                    raise ValueError(f"API error: {error}")
                
                return data["result"]
        
        except (RateLimitError, httpx.TimeoutException, httpx.ConnectError) as e:
            if attempt == max_retries - 1:
                raise
            
            delay = min(max_delay, base_delay * (2 ** attempt))
            if jitter:
                delay *= random.uniform(0.5, 1.5)
            
            print(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s")
            await asyncio.sleep(delay)
    
    raise RuntimeError("Max retries exceeded")
```

---

## 3. Multi-Client Failover

### Round-Robin Failover Pool

```python
import asyncio
from itertools import cycle
from typing import Optional
import httpx

XRPL_ENDPOINTS = [
    "https://xrplcluster.com",
    "https://xrpl.ws",
    "https://s1.ripple.com",
]

class XRPLClientPool:
    def __init__(self, endpoints: list):
        self.endpoints = endpoints
        self._healthy = {ep: True for ep in endpoints}
        self._health_locks = {ep: asyncio.Lock() for ep in endpoints}
        self._cycle = cycle(endpoints)
        self._semaphores = {ep: asyncio.Semaphore(5) for ep in endpoints}
    
    def _next_healthy(self) -> Optional[str]:
        for _ in range(len(self.endpoints)):
            ep = next(self._cycle)
            if self._healthy[ep]:
                return ep
        return None
    
    async def request(self, method: str, params: dict, max_retries: int = 3) -> dict:
        for attempt in range(max_retries):
            endpoint = self._next_healthy()
            if not endpoint:
                await asyncio.sleep(5)
                # Reset all to healthy and retry
                self._healthy = {ep: True for ep in self.endpoints}
                endpoint = self.endpoints[0]
            
            try:
                async with self._semaphores[endpoint]:
                    async with httpx.AsyncClient(timeout=15) as client:
                        payload = {"method": method, "params": [params]}
                        resp = await client.post(endpoint, json=payload)
                        
                        if resp.status_code == 429:
                            self._healthy[endpoint] = False
                            asyncio.create_task(self._restore_health(endpoint, 30))
                            continue
                        
                        resp.raise_for_status()
                        result = resp.json()
                        self._healthy[endpoint] = True
                        return result["result"]
            
            except (httpx.TimeoutException, httpx.ConnectError):
                self._healthy[endpoint] = False
                asyncio.create_task(self._restore_health(endpoint, 60))
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
        
        raise RuntimeError("All endpoints failed")
    
    async def _restore_health(self, endpoint: str, delay: float):
        await asyncio.sleep(delay)
        self._healthy[endpoint] = True

# Usage
pool = XRPLClientPool(XRPL_ENDPOINTS)
result = await pool.request("account_info", {"account": "rN7n...", "ledger_index": "validated"})
```

### WebSocket Failover

```python
import asyncio
import xrpl

class XRPLWSPool:
    def __init__(self, endpoints: list):
        self.endpoints = endpoints
        self.current_idx = 0
        self.client = None
    
    async def connect(self):
        for i, ep in enumerate(self.endpoints):
            try:
                self.client = xrpl.asyncio.clients.AsyncWebsocketClient(ep)
                await self.client.open()
                self.current_idx = i
                print(f"Connected to {ep}")
                return
            except Exception as e:
                print(f"Failed to connect to {ep}: {e}")
        raise RuntimeError("All WebSocket endpoints failed")
    
    async def ensure_connected(self):
        if self.client is None or not self.client.is_open():
            await self.connect()
    
    async def request(self, req):
        await self.ensure_connected()
        try:
            return await self.client.request(req)
        except Exception:
            # Try next endpoint
            self.current_idx = (self.current_idx + 1) % len(self.endpoints)
            await self.connect()
            return await self.client.request(req)
```

---

## 4. Parallel Request Throttling

Control concurrency to avoid rate limits:

```python
import asyncio
from typing import List, Callable, Any

async def throttled_gather(
    tasks: List[Callable],
    max_concurrent: int = 5,
    delay_between_batches: float = 1.0
) -> List[Any]:
    """Execute tasks with controlled parallelism."""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def controlled_task(coro):
        async with semaphore:
            return await coro
    
    return await asyncio.gather(*[controlled_task(t) for t in tasks])

# Rate-limited batch fetcher
async def fetch_accounts_batch(addresses: List[str]) -> dict:
    pool = XRPLClientPool(XRPL_ENDPOINTS)
    
    async def fetch_one(address: str):
        result = await pool.request("account_info", {
            "account": address,
            "ledger_index": "validated"
        })
        return address, result.get("account_data")
    
    tasks = [fetch_one(addr) for addr in addresses]
    results = await throttled_gather(tasks, max_concurrent=5, delay_between_batches=0.1)
    return dict(results)
```

---

## 5. Token Rate Limit Configuration

### xrpl.to Rate Limiter

```python
import time
from collections import deque

class TokenBucket:
    """Token bucket rate limiter."""
    
    def __init__(self, rate: float, capacity: int):
        self.rate = rate          # tokens per second
        self.capacity = capacity  # max burst size
        self.tokens = capacity
        self.last_refill = time.monotonic()
    
    def acquire(self, tokens: int = 1) -> float:
        """Returns wait time in seconds. 0 if no wait needed."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_refill = now
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return 0.0
        
        wait = (tokens - self.tokens) / self.rate
        self.tokens = 0
        return wait

class XRPLToClient:
    BASE_URL = "https://api.xrpl.to"
    
    def __init__(self):
        # 30 req/min = 0.5 req/s
        self._limiter = TokenBucket(rate=0.5, capacity=5)
    
    async def get_token(self, currency: str, issuer: str) -> dict:
        wait = self._limiter.acquire()
        if wait > 0:
            await asyncio.sleep(wait)
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/v1/token/{currency}/{issuer}"
            )
            resp.raise_for_status()
            return resp.json()
    
    async def get_amm(self, asset1: dict, asset2: dict) -> dict:
        wait = self._limiter.acquire()
        if wait > 0:
            await asyncio.sleep(wait)
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/v1/amm",
                params={
                    "asset1_currency": asset1.get("currency", "XRP"),
                    "asset1_issuer": asset1.get("issuer", ""),
                    "asset2_currency": asset2.get("currency", "XRP"),
                    "asset2_issuer": asset2.get("issuer", "")
                }
            )
            resp.raise_for_status()
            return resp.json()
```

---

## 6. API-Specific Patterns

### CoinGecko XRP Price

```python
import httpx
import asyncio

class CoinGeckoClient:
    BASE = "https://api.coingecko.com/api/v3"
    
    def __init__(self, api_key: str = None):
        self.headers = {}
        if api_key:
            self.headers["x-cg-pro-api-key"] = api_key
        # Free: 10-50 req/min; Pro: 500 req/min
        self._limiter = TokenBucket(rate=0.15, capacity=3)  # conservative
    
    async def get_xrp_price(self, vs_currency: str = "usd") -> float:
        wait = self._limiter.acquire()
        if wait > 0:
            await asyncio.sleep(wait)
        
        async with httpx.AsyncClient(headers=self.headers) as client:
            resp = await client.get(
                f"{self.BASE}/simple/price",
                params={"ids": "ripple", "vs_currencies": vs_currency}
            )
            resp.raise_for_status()
            return resp.json()["ripple"][vs_currency]
```

### XRPSCAN

```python
class XRPSCANClient:
    BASE = "https://api.xrpscan.com/api/v1"
    
    def __init__(self, api_key: str = None):
        self.headers = {}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
            rate = 20.0  # 1200/min
        else:
            rate = 2.0   # 120/min
        self._limiter = TokenBucket(rate=rate, capacity=10)
    
    async def get_account(self, address: str) -> dict:
        wait = self._limiter.acquire()
        if wait > 0:
            await asyncio.sleep(wait)
        
        async with httpx.AsyncClient(headers=self.headers) as client:
            resp = await client.get(f"{self.BASE}/account/{address}")
            resp.raise_for_status()
            return resp.json()
```

---

## 7. Retry Budget Pattern

Avoid retry storms with a global retry budget:

```python
import asyncio
from contextlib import asynccontextmanager

class RetryBudget:
    def __init__(self, budget_per_minute: int = 100):
        self.budget = budget_per_minute
        self.used = 0
        self._reset_task = None
    
    def start(self):
        async def reset_loop():
            while True:
                await asyncio.sleep(60)
                self.used = 0
        self._reset_task = asyncio.create_task(reset_loop())
    
    @asynccontextmanager
    async def retry(self):
        if self.used >= self.budget:
            raise RuntimeError("Retry budget exhausted")
        self.used += 1
        try:
            yield
        finally:
            pass

# Usage
budget = RetryBudget(budget_per_minute=50)
budget.start()

async with budget.retry():
    result = await pool.request("account_info", {...})
```

---

## 8. WebSocket Reconnect with Subscription Restore

```javascript
const xrpl = require('xrpl');

class ResilientClient {
  constructor(endpoints) {
    this.endpoints = endpoints;
    this.idx = 0;
    this.client = null;
    this.subscriptions = [];
  }

  async connect() {
    for (let i = 0; i < this.endpoints.length; i++) {
      try {
        const ep = this.endpoints[(this.idx + i) % this.endpoints.length];
        this.client = new xrpl.Client(ep);
        await this.client.connect();
        
        // Restore subscriptions
        for (const sub of this.subscriptions) {
          await this.client.request(sub);
        }
        return;
      } catch (e) {
        console.warn(`Failed to connect: ${e.message}`);
      }
    }
    throw new Error('All endpoints failed');
  }

  async subscribe(req, handler) {
    this.subscriptions.push(req);
    this.client.on('transaction', handler);
    await this.client.request(req);
    
    this.client.on('disconnected', async () => {
      await new Promise(r => setTimeout(r, 2000));
      await this.connect();
    });
  }
}
```
