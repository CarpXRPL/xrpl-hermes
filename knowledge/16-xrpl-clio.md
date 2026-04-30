# XRPL Clio Server

## Overview

Clio is a read-optimized XRPL API server that sits alongside rippled, storing data in **PostgreSQL** or **Cassandra**. It handles historical queries, account data, and ledger scans more efficiently than rippled, offloading read traffic from validators and full-history nodes. Clio is the recommended backend for high-read-volume applications.

---

## 1. Architecture

```
Client
  │
  ├─► Clio (read requests: account_info, tx, ledger_data, etc.)
  │       │
  │       └─► PostgreSQL / Cassandra (historical data)
  │           │
  │           └─► rippled (subscribe to validated ledgers)
  │
  └─► rippled (write requests: submit, subscribe)
```

Clio:
- Subscribes to rippled for new validated ledgers
- Stores data in its own database
- Serves read APIs without hitting rippled
- Falls back to rippled for some APIs (submit, subscribe)

---

## 2. Supported API Endpoints

Clio supports a subset of rippled's API:

| API Method | Supported |
|-----------|-----------|
| `account_info` | ✅ |
| `account_lines` | ✅ |
| `account_offers` | ✅ |
| `account_nfts` | ✅ |
| `account_objects` | ✅ |
| `account_tx` | ✅ |
| `gateway_balances` | ✅ |
| `ledger` | ✅ |
| `ledger_data` | ✅ |
| `ledger_entry` | ✅ |
| `tx` | ✅ |
| `transaction_entry` | ✅ |
| `nft_info` | ✅ |
| `nft_history` | ✅ |
| `amm_info` | ✅ |
| `book_offers` | ✅ |
| `ripple_path_find` | ✅ |
| `subscribe` | ✅ (proxied to rippled) |
| `submit` | ✅ (proxied to rippled) |
| `server_info` | ✅ (returns Clio info) |
| `fee` | ✅ (proxied to rippled) |
| `manifest` | ✅ |
| `server_state` | ❌ |
| `validator_list_sites` | ❌ |

---

## 3. Public Clio Endpoints

| Provider | URL | Notes |
|----------|-----|-------|
| XRPL Foundation | `https://xrplcluster.com` | Primary public Clio cluster |
| Ripple | `wss://s1.ripple.com` | Full history, rippled |
| Ripple | `wss://s2.ripple.com` | Full history, rippled |
| XRPLF Clio | `wss://xrplcluster.com` | WebSocket |
| OnXRP | `https://xrpl.ws` | Community node |

Clio-specific indicator: responses include `"api_version": 1` and the `"type": "clio"` field in `server_info`.

---

## 4. Installing Clio

### Prerequisites

```bash
# Ubuntu 22.04
sudo apt update && sudo apt install -y \
  build-essential cmake ninja-build \
  libssl-dev libboost-all-dev \
  postgresql postgresql-contrib \
  libpq-dev

# Or use Docker:
docker pull ghcr.io/xrplf/clio:latest
```

### Build from Source

```bash
git clone https://github.com/XRPLF/clio
cd clio
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake --build . --parallel $(nproc)
```

---

## 5. Configuration File

```json
{
  "database": {
    "type": "postgres",
    "host": "localhost",
    "port": 5432,
    "database": "clio",
    "user": "clio_user",
    "password": "secure_password",
    "max_connections": 10
  },
  "etl_sources": [
    {
      "ip": "127.0.0.1",
      "ws_port": "6006",
      "grpc_port": "50051"
    }
  ],
  "server": {
    "ip": "0.0.0.0",
    "port": 51233
  },
  "log_level": "info",
  "log_format": "json",
  "num_markers": 48,
  "cache": {
    "num_diffs": 32
  },
  "dos_guard": {
    "max_fetches": 1000000,
    "sweep_interval": 1,
    "max_connections": 20,
    "max_requests_per_second": 20
  }
}
```

### PostgreSQL Setup

```sql
-- Create database and user
CREATE USER clio_user WITH PASSWORD 'secure_password';
CREATE DATABASE clio OWNER clio_user;
GRANT ALL PRIVILEGES ON DATABASE clio TO clio_user;

-- Clio creates its own schema on first run
```

---

## 6. rippled Configuration for Clio

Enable gRPC on rippled (required for Clio ETL):

```ini
# rippled.cfg
[port_grpc]
ip = 0.0.0.0
port = 50051

[port_ws_internal]
ip = 127.0.0.1
port = 6006
protocol = ws
admin = 127.0.0.1
```

---

## 7. Running Clio

```bash
# Start Clio
./clio_server --conf /etc/clio/config.json

# Systemd service
cat > /etc/systemd/system/clio.service << EOF
[Unit]
Description=Clio XRPL Server
After=network.target postgresql.service

[Service]
Type=simple
User=clio
ExecStart=/usr/local/bin/clio_server --conf /etc/clio/config.json
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl enable --now clio
```

---

## 8. API Usage with Rate Limits

Clio enforces connection and request limits:

```python
import httpx
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

CLIO_URLS = [
    "https://xrplcluster.com",
    "https://xrpl.ws"
]

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
async def clio_request(method: str, params: dict, url: str = CLIO_URLS[0]):
    payload = {"method": method, "params": [params]}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data.get("result", {}):
            raise ValueError(f"API error: {data['result']['error']}")
        return data["result"]

# Account info
result = await clio_request("account_info", {
    "account": "rN7n...",
    "ledger_index": "validated"
})
```

---

## 9. Ledger Data / Full Scan

Clio supports `ledger_data` for scanning all ledger objects:

```python
async def scan_all_offers(client_url: str):
    marker = None
    offers = []
    
    while True:
        params = {
            "ledger_index": "validated",
            "type": "offer",
            "limit": 400
        }
        if marker:
            params["marker"] = marker
        
        result = await clio_request("ledger_data", params, client_url)
        
        for obj in result.get("state", []):
            if obj.get("LedgerEntryType") == "Offer":
                offers.append(obj)
        
        marker = result.get("marker")
        if not marker:
            break
        
        await asyncio.sleep(0.1)  # Rate limit
    
    return offers
```

---

## 10. NFT History

Clio's `nft_history` API (not available in rippled):

```python
result = await clio_request("nft_history", {
    "nft_id": "000800006B...",
    "ledger_index_min": -1,
    "ledger_index_max": -1,
    "limit": 50
})

for tx in result["transactions"]:
    print(f"  {tx['tx']['TransactionType']} at ledger {tx['ledger_index']}")
```

---

## 11. Rate Limits (Public Clio)

| Limit Type | Value |
|-----------|-------|
| Max connections per IP | 20 |
| Max requests/second per IP | 20 |
| Max fetches (internal cost) | 1,000,000/sweep |
| Sweep interval | 1 second |

If rate limited: HTTP 429 or WebSocket close with error.

Retry strategy:
```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(min=0.5, max=30),
    retry=retry_if_exception_type((httpx.HTTPStatusError, ValueError))
)
async def safe_clio_request(method, params):
    return await clio_request(method, params)
```

---

## 12. Clio vs rippled Comparison

| Feature | Clio | rippled |
|---------|------|---------|
| Read performance | Excellent (DB-backed) | Good |
| Historical data | Full (if DB has it) | Depends on online_delete |
| Write/submit | Proxied | Native |
| Resource usage | Lower (read only) | Higher |
| `ledger_data` scan | Fast | Slower |
| NFT history | Native | Limited |
| AMM queries | Native | Native |
| Subscription | Proxied | Native |
