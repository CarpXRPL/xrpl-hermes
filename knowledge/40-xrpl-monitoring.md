# Production Monitoring for XRPL Bots & Services

## Monitoring Architecture

A production XRPL service needs four monitoring layers:
1. **Process health** — is the bot running? (systemd, uptime kuma)
2. **Ledger sync** — is it tracking the live ledger? (gap detection)
3. **Transaction health** — are submitted txs succeeding? (result codes)
4. **Business metrics** — balances, volumes, P&L (custom logic)

---

## Systemd Service Definition

```ini
# /etc/systemd/system/xrpl-arb-bot.service
[Unit]
Description=XRPL Arbitrage Bot
After=network-online.target
Wants=network-online.target
# Restart if rippled dependency is available
Requires=network.target

[Service]
Type=simple
User=xrpl
Group=xrpl
WorkingDirectory=/opt/xrpl-bots/arb-bot
ExecStart=/usr/bin/python3 -u main.py --config /opt/xrpl-bots/arb-bot/config.yaml
ExecReload=/bin/kill -HUP $MAINPID

# Crash recovery
Restart=always
RestartSec=10
StartLimitInterval=60s
StartLimitBurst=5       # 5 restarts within 60s → give up and alert

# Logging
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1
Environment=LOG_LEVEL=INFO

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ReadOnlyPaths=/etc
ReadWritePaths=/opt/xrpl-bots/arb-bot/data

[Install]
WantedBy=multi-user.target
```

```bash
# Deploy
sudo systemctl daemon-reload
sudo systemctl enable xrpl-arb-bot
sudo systemctl start xrpl-arb-bot

# Verify
sudo systemctl status xrpl-arb-bot
sudo journalctl -u xrpl-arb-bot -f

# Reload config without full restart
sudo systemctl reload xrpl-arb-bot
```

---

## Health Check Endpoint (FastAPI)

Embed a health server in your bot process:

```python
import asyncio, time
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn, threading

class BotState:
    start_time: float = time.time()
    last_ledger_index: int = 0
    last_ledger_time: float = 0
    tx_submitted: int = 0
    tx_success: int = 0
    tx_failed: int = 0
    last_error: str = ""
    balances: dict = {}

state = BotState()
app = FastAPI()

class HealthResponse(BaseModel):
    status: str
    ledger_index: int
    ledger_lag_s: float
    uptime_s: float
    tx_success_rate: float
    tx_submitted: int
    tx_failed: int
    last_error: str
    balances: dict

@app.get("/health", response_model=HealthResponse)
def health():
    now = time.time()
    lag = now - state.last_ledger_time
    total = state.tx_submitted or 1
    status = "ok" if lag < 30 else "degraded"

    return HealthResponse(
        status=status,
        ledger_index=state.last_ledger_index,
        ledger_lag_s=round(lag, 1),
        uptime_s=round(now - state.start_time, 0),
        tx_success_rate=round(state.tx_success / total, 3),
        tx_submitted=state.tx_submitted,
        tx_failed=state.tx_failed,
        last_error=state.last_error,
        balances=state.balances,
    )

@app.get("/ready")
def ready():
    """Kubernetes readiness probe — fail if lag > 60s."""
    lag = time.time() - state.last_ledger_time
    if lag > 60:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=503, content={"status": "not_ready", "lag_s": lag})
    return {"status": "ready"}

def start_health_server(port=8080):
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")

# Start in background thread
threading.Thread(target=start_health_server, daemon=True).start()
```

---

## Prometheus Metrics Integration

```python
from prometheus_client import Counter, Gauge, Histogram, start_http_server
import time

# Start metrics endpoint (separate port from health)
start_http_server(9090)

# Metrics
TX_SUBMITTED = Counter("xrpl_tx_submitted_total", "Total transactions submitted", ["type"])
TX_SUCCESS = Counter("xrpl_tx_success_total", "Successful transactions", ["type"])
TX_FAILED = Counter("xrpl_tx_failed_total", "Failed transactions", ["type", "error_code"])
TX_LATENCY = Histogram(
    "xrpl_tx_latency_seconds",
    "Time from submit to validated",
    buckets=[1, 2, 4, 8, 16, 30, 60],
)
LEDGER_INDEX = Gauge("xrpl_last_ledger_index", "Most recent validated ledger index")
LEDGER_LAG = Gauge("xrpl_ledger_lag_seconds", "Seconds since last ledger close observed")
WALLET_BALANCE_XRP = Gauge("xrpl_wallet_balance_xrp", "Wallet XRP balance", ["address", "label"])
WALLET_BALANCE_TOKEN = Gauge("xrpl_wallet_balance_token", "Wallet token balance", ["address", "currency"])
AMM_POOL_XRP = Gauge("xrpl_amm_pool_xrp", "AMM pool XRP reserves", ["pool_id"])
AMM_POOL_TOKEN = Gauge("xrpl_amm_pool_token", "AMM pool token reserves", ["pool_id", "currency"])
OFFER_COUNT = Gauge("xrpl_open_offers", "Number of open DEX offers", ["account"])
ARBITRAGE_PROFIT = Counter("xrpl_arb_profit_xrp_total", "Total arbitrage profit in XRP")


def record_tx(tx_type: str, result_code: str, latency: float):
    TX_SUBMITTED.labels(type=tx_type).inc()
    TX_LATENCY.observe(latency)
    if result_code == "tesSUCCESS":
        TX_SUCCESS.labels(type=tx_type).inc()
    else:
        TX_FAILED.labels(type=tx_type, error_code=result_code).inc()


def update_balance_metrics(client, wallets: list[dict]):
    """wallets: [{"address": "r...", "label": "hot-wallet"}]"""
    from xrpl.models.requests import AccountInfo, AccountLines

    for w in wallets:
        try:
            acc = client.request(AccountInfo(account=w["address"], ledger_index="validated"))
            drops = int(acc.result["account_data"]["Balance"])
            WALLET_BALANCE_XRP.labels(address=w["address"], label=w["label"]).set(drops / 1e6)

            # Token balances
            lines = client.request(AccountLines(account=w["address"], ledger_index="validated"))
            for line in lines.result.get("lines", []):
                WALLET_BALANCE_TOKEN.labels(
                    address=w["address"],
                    currency=line["currency"],
                ).set(float(line["balance"]))
        except Exception as e:
            state.last_error = str(e)
```

### Prometheus Scrape Config
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'xrpl-bot'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 15s

  - job_name: 'xrpl-bot-health'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['localhost:8080']
```

---

## Grafana Dashboard JSON (Key Panels)

```json
{
  "panels": [
    {
      "title": "Tx Success Rate (1m avg)",
      "type": "stat",
      "targets": [{
        "expr": "rate(xrpl_tx_success_total[1m]) / rate(xrpl_tx_submitted_total[1m])",
        "legendFormat": "Success Rate"
      }],
      "fieldConfig": {"defaults": {"unit": "percentunit", "min": 0, "max": 1}}
    },
    {
      "title": "Ledger Lag",
      "type": "timeseries",
      "targets": [{"expr": "xrpl_ledger_lag_seconds", "legendFormat": "Lag (s)"}],
      "alert": {
        "name": "Ledger lag > 30s",
        "conditions": [{"evaluator": {"type": "gt", "params": [30]}}]
      }
    },
    {
      "title": "Wallet Balance (XRP)",
      "type": "table",
      "targets": [{"expr": "xrpl_wallet_balance_xrp", "legendFormat": "{{label}}"}]
    },
    {
      "title": "Tx Failures by Error Code",
      "type": "piechart",
      "targets": [{"expr": "sum by (error_code) (xrpl_tx_failed_total)"}]
    }
  ]
}
```

---

## Alert Rules

```yaml
# alerting-rules.yml
groups:
  - name: xrpl_bot
    rules:
      - alert: LedgerLagHigh
        expr: xrpl_ledger_lag_seconds > 30
        for: 1m
        severity: warning
        annotations:
          summary: "Bot not receiving ledger updates (lag={{ $value }}s)"

      - alert: LedgerLagCritical
        expr: xrpl_ledger_lag_seconds > 120
        for: 30s
        severity: critical
        annotations:
          summary: "Bot disconnected from XRPL (lag={{ $value }}s) — investigate"

      - alert: TxFailureRateHigh
        expr: |
          rate(xrpl_tx_failed_total[5m]) /
          (rate(xrpl_tx_submitted_total[5m]) + 0.001) > 0.1
        for: 2m
        severity: warning
        annotations:
          summary: "More than 10% of transactions failing (rate={{ $value }})"

      - alert: WalletLowBalance
        expr: xrpl_wallet_balance_xrp{label="hot-wallet"} < 10
        for: 5m
        severity: critical
        annotations:
          summary: "Hot wallet balance critically low: {{ $value }} XRP"

      - alert: BotProcessDown
        expr: up{job="xrpl-bot"} == 0
        for: 1m
        severity: critical
        annotations:
          summary: "XRPL bot process is down"
```

---

## Transaction Result Code Monitoring

```python
# Critical error codes that need immediate response
CRITICAL_ERRORS = {
    "tecUNFUNDED_PAYMENT",    # Wallet ran out of XRP
    "tecINSUFF_RESERVE_LINE", # Can't create trust line (reserve too low)
    "tefBAD_AUTH",            # Wrong key — possible key compromise
    "tecNO_DST_INSUF_XRP",    # Destination doesn't exist
}

RETRYABLE_ERRORS = {
    "tefPAST_SEQ",            # Sequence number too low → refresh and retry
    "tefMAX_LEDGER",          # Ledger window expired → resubmit
    "telCAN_NOT_QUEUE",       # Queue full → back off
    "tooBusy",                # Node busy → rotate endpoint
}

EXPECTED_FAILURES = {
    "tecPATH_PARTIAL",        # Payment path insufficient — liquidity issue
    "tecPATH_DRY",            # No valid path found
    "tecOFFER_NOT_FOUND",     # Offer already consumed or cancelled
    "tecKILLED",              # tfImmediateOrCancel offer couldn't fill
}


def classify_error(result_code: str) -> str:
    if result_code == "tesSUCCESS":
        return "success"
    if result_code in CRITICAL_ERRORS:
        return "critical"
    if result_code in RETRYABLE_ERRORS:
        return "retryable"
    if result_code in EXPECTED_FAILURES:
        return "expected"
    return "unexpected"


def handle_tx_result(tx_hash: str, result_code: str, tx_type: str):
    category = classify_error(result_code)

    if category == "critical":
        send_alert(f"🚨 CRITICAL: {result_code} on {tx_type} tx {tx_hash[:12]}...")
    elif category == "unexpected":
        send_alert(f"⚠️ Unexpected error: {result_code} on {tx_type}")

    TX_FAILED.labels(type=tx_type, error_code=result_code).inc()
```

---

## Ledger Gap Detection

```python
import asyncio, json, websockets, logging

logger = logging.getLogger("ledger-monitor")

async def monitor_ledger_stream(url: str, on_gap=None):
    """
    Subscribe to ledger_closed stream and detect gaps.
    Calls on_gap(from_ledger, to_ledger) when ledgers are skipped.
    """
    async with websockets.connect(url) as ws:
        await ws.send(json.dumps({
            "command": "subscribe",
            "streams": ["ledger"],
        }))
        first = await ws.recv()
        data = json.loads(first)
        last_seq = data.get("ledger_index", 0)
        logger.info(f"Subscribed at ledger {last_seq}")

        async for raw in ws:
            msg = json.loads(raw)
            if msg.get("type") != "ledgerClosed":
                continue

            current_seq = msg["ledger_index"]
            gap = current_seq - last_seq

            if gap > 1:
                logger.warning(f"Ledger gap: missed {gap - 1} ledgers ({last_seq+1} to {current_seq-1})")
                if on_gap:
                    await on_gap(last_seq + 1, current_seq - 1)

            LEDGER_INDEX.set(current_seq)
            LEDGER_LAG.set(0)
            state.last_ledger_index = current_seq
            state.last_ledger_time = time.time()
            last_seq = current_seq
```

---

## Balance Monitoring with Thresholds

```python
WALLET_THRESHOLDS = [
    {"label": "hot-wallet",       "address": "rHot...", "min_xrp": 50,    "alert": True},
    {"label": "reserve-wallet",   "address": "rRes...", "min_xrp": 1000,  "alert": True},
    {"label": "treasury",         "address": "rTrx...", "min_xrp": 10000, "alert": True},
]

def check_all_balances(client):
    from xrpl.models.requests import AccountInfo

    alerts = []
    for w in WALLET_THRESHOLDS:
        try:
            acc = client.request(AccountInfo(account=w["address"], ledger_index="validated"))
            drops = int(acc.result["account_data"]["Balance"])
            xrp = drops / 1e6
            WALLET_BALANCE_XRP.labels(address=w["address"], label=w["label"]).set(xrp)

            if xrp < w["min_xrp"] and w["alert"]:
                alerts.append(f"⚠️ {w['label']} ({w['address'][:8]}...): {xrp:.2f} XRP < {w['min_xrp']} XRP threshold")
        except Exception as e:
            alerts.append(f"❌ Failed to check {w['label']}: {e}")

    return alerts

# Run every 5 minutes
import schedule
schedule.every(5).minutes.do(lambda: [send_alert(a) for a in check_all_balances(client)])
```

---

## Telegram & Discord Alerts

```python
import httpx, asyncio

async def send_telegram(message: str, bot_token: str, chat_id: str):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    async with httpx.AsyncClient() as http:
        await http.post(url, json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_notification": False,
        })

async def send_discord(message: str, webhook_url: str):
    async with httpx.AsyncClient() as http:
        await http.post(webhook_url, json={
            "content": message,
            "username": "XRPL Bot Monitor",
        })

def send_alert(message: str):
    """Sync wrapper that fires alerts to all configured channels."""
    import os
    loop = asyncio.new_event_loop()
    tasks = []

    if os.environ.get("TELEGRAM_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"):
        tasks.append(send_telegram(
            message,
            os.environ["TELEGRAM_TOKEN"],
            os.environ["TELEGRAM_CHAT_ID"],
        ))
    if os.environ.get("DISCORD_WEBHOOK"):
        tasks.append(send_discord(message, os.environ["DISCORD_WEBHOOK"]))

    if tasks:
        loop.run_until_complete(asyncio.gather(*tasks))
    loop.close()
```

---

## Log Configuration

```python
import logging, sys
from logging.handlers import RotatingFileHandler

def configure_logging(level: str = "INFO", log_file: str | None = None):
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Always log to stdout (captured by journald)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(fmt)
    root.addHandler(stdout_handler)

    # Optionally also to rotating file
    if log_file:
        file_handler = RotatingFileHandler(log_file, maxBytes=50_000_000, backupCount=5)
        file_handler.setFormatter(fmt)
        root.addHandler(file_handler)
```

```bash
# Journald log viewing
journalctl -u xrpl-arb-bot -f                        # Live tail
journalctl -u xrpl-arb-bot --since "1 hour ago"      # Last hour
journalctl -u xrpl-arb-bot -S today -p err            # Errors only today
journalctl -u xrpl-arb-bot --output json | jq .MESSAGE  # JSON mode
```

---

## Disk and Node Health

```bash
# rippled node disk usage
du -sh /var/lib/rippled/db/nudb/        # NuDB (main ledger data)
du -sh /var/lib/rippled/db/transaction/ # Transaction database
du -sh /var/lib/postgresql/             # Clio's Postgres

# rippled online_delete config — keep last N ledgers
# /etc/rippled/rippled.cfg:
# [node_db]
# online_delete=2000000   # Keep ~2M ledgers (~11 days)
# advisory_delete=0       # Auto-delete (don't require manual trigger)

# Check rippled sync status
curl -s -X POST https://localhost:5005 \
  -H "Content-Type: application/json" \
  -d '{"method":"server_info","params":[{}]}' | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result']['info']['complete_ledgers'])"
```

---

## Related Files
- `knowledge/18-xrpl-rate-limits.md` — rate limit handling
- `knowledge/24-xrpl-deploy-guide.md` — deployment config
- `knowledge/41-xrpl-bots-patterns.md` — bot architecture patterns
