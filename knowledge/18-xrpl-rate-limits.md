# XRPL Rate Limits & Retry Strategies

## Overview

All public XRPL endpoints enforce rate limits. This document covers per-endpoint limits, retry logic with exponential backoff, multi-client failover, and parallel request throttling for production use.

---

## 1. Endpoint-limit boundary

Rate limits, plans, routes and authentication requirements change independently of this repository.
No exact third-party limit or explorer/token route is certified in v1.9.0. For every selected XRPL
JSON-RPC/Clio or external provider, read current first-party documentation and observed response
headers; configure conservative limits, backoff and circuit breaking rather than relying on a table.

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

### Provider-neutral token-bucket limiter

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

# Third-party token/AMM clients are intentionally omitted.
# A provider-specific client may be added only after its current documented
# route, schema, auth, pagination, limits, error behavior and timestamp are
# contract-tested. Use XRPL JSON-RPC/Clio methods for supported ledger data.
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

### Third-party explorer boundary

No third-party explorer route or rate-limit figure is certified in this release. Add a client only
after verifying current first-party documentation, authentication, schema, pagination, timestamps,
error behavior and observed limits. Use validated XRPL JSON-RPC/Clio for ledger evidence by default.

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

---

## Related Files

- `knowledge/16-xrpl-clio.md` — Clio request semantics
- `knowledge/17-xrpl-private-node.md` — removing rate limits with own node
- `knowledge/20-xrpl-data-api.md` — off-chain rate limits
