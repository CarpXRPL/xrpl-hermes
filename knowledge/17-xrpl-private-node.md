# XRPL Private Node Setup

## Overview

Running your own rippled node (and optionally Clio) gives you: unlimited API access, no rate limits, historical data control, and sovereignty from public endpoints. This guide covers full validator and stock node setup on a VPS.

---

## 1. Node Types

| Type | Description | Use Case |
|------|-------------|----------|
| Stock Node | Follows network, serves API | Development, production apps |
| Validator | Participates in consensus | Network health, business validation |
| Full History | Keeps all ledger data | Data archival, analytics |

---

## 2. VPS Specifications

### Minimum (Stock Node)

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 4 vCPU | 8 vCPU |
| RAM | 16 GB | 32 GB |
| Disk | 500 GB NVMe SSD | 2 TB NVMe SSD |
| Network | 100 Mbps | 1 Gbps |
| OS | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |

**Hetzner CX32** (~$16/mo): 4 vCPU, 8 GB RAM — fine for light dev nodes
**Hetzner AX102** (~$75/mo): 24 vCPU, 128 GB RAM — production validator

### Full History Node

- Disk: 6–12 TB NVMe (growing ~1 TB/year)
- RAM: 64 GB minimum

---

## 3. Installing rippled

### Ubuntu 22.04

```bash
# Add Ripple repo
sudo apt install -y apt-transport-https ca-certificates wget gnupg
wget -q https://repos.ripple.com/repos/api/gpg/key/public -O- | sudo apt-key add -

echo "deb https://repos.ripple.com/repos/rippled-deb jammy stable" | \
  sudo tee /etc/apt/sources.list.d/ripple.list

sudo apt update
sudo apt install -y rippled

# Verify
rippled --version
```

### From Docker

```bash
docker pull rippleci/rippled:latest
docker run -d \
  --name rippled \
  -p 51235:51235 \
  -p 6005:6005 \
  -v /data/rippled:/var/lib/rippled \
  -v /etc/rippled:/etc/opt/ripple \
  rippleci/rippled:latest
```

---

## 4. Configuration File (`/etc/opt/ripple/rippled.cfg`)

```ini
# rippled.cfg — Stock Node (no validation)

[server]
port_rpc_admin_local
port_ws_public
port_peer

[port_rpc_admin_local]
ip = 127.0.0.1
port = 5005
protocol = http
admin = 127.0.0.1

[port_ws_public]
ip = 0.0.0.0
port = 6006
protocol = ws,wss
echo = true
# limit = 512

[port_peer]
ip = 0.0.0.0
port = 51235
protocol = peer

# For Clio ETL:
[port_grpc]
ip = 0.0.0.0
port = 50051

[node_db]
type = NuDB
path = /var/lib/rippled/db/nudb
# Keep last 2000 ledgers (~2.8 days)
online_delete = 2000
advisory_delete = 0

[database_path]
/var/lib/rippled/db

[debug_logfile]
/var/log/rippled/debug.log

[sntp_servers]
time.windows.com
time.apple.com
time.nist.gov

[ips]
# Known peers — add reliable nodes
r.ripple.com 51235
zaphod.alloy.ee 51235

[validators_file]
/etc/opt/ripple/validators.txt

[rpc_startup]
{ "command": "log_level", "severity": "warning" }

[ssl_verify]
0
```

### Online Delete Configuration

```ini
# Aggressive (saves disk, loses history):
online_delete = 512      # ~12 hours

# Conservative (keeps ~2 weeks):
online_delete = 100000

# Full history (never delete):
# Comment out online_delete entirely
# and set advisory_delete = 0
```

---

## 5. Validators File (`/etc/opt/ripple/validators.txt`)

```ini
[validator_list_sites]
https://vl.ripple.com
https://vl.xrplf.org

[validator_list_keys]
ED2677ABFFD1B33AC6FBC3062B71F1E8397C1505E1C42C64D11AD1B28FF73F4D5
ED45D1840EE724BE327ABE9146503D5848EFD5F38B6D5FEDE71E80ACCE5E6E738
```

Update validator list:
```bash
# Fetch latest validator list
rippled validators
```

---

## 6. Running as Validator

```bash
# Generate validator token
rippled validation_create

# Output:
# {
#   "status": "success",
#   "validation_key": "BODE CALL GAZE...",
#   "validation_private_key": "...",
#   "validation_public_key": "nHBidG3pZ...",
#   "validation_seed": "shGZU..."
# }
```

Add to `rippled.cfg`:
```ini
[validator_token]
PASTE_MULTI_LINE_TOKEN_HERE
```

**Security**: Never share the private key. Keep the seed offline. Rotate regularly.

---

## 7. Systemd Service

```bash
# Enable and start
systemctl enable rippled
systemctl start rippled

# Check status
systemctl status rippled
journalctl -u rippled -f

# Restart after config change
systemctl restart rippled
```

Custom service override:
```ini
# /etc/systemd/system/rippled.service.d/override.conf
[Service]
# Increase file descriptor limit
LimitNOFILE=65536
# Restart on failure
Restart=on-failure
RestartSec=30
```

---

## 8. Clio + PostgreSQL Setup

### PostgreSQL

```bash
sudo apt install -y postgresql postgresql-contrib
sudo systemctl enable --now postgresql

sudo -u postgres psql << EOF
CREATE USER clio WITH PASSWORD 'strong_password';
CREATE DATABASE clio OWNER clio;
GRANT ALL PRIVILEGES ON DATABASE clio TO clio;
EOF
```

PostgreSQL tuning (`/etc/postgresql/14/main/postgresql.conf`):

```ini
shared_buffers = 4GB
effective_cache_size = 12GB
maintenance_work_mem = 1GB
work_mem = 64MB
wal_buffers = 64MB
checkpoint_completion_target = 0.9
random_page_cost = 1.1
max_connections = 200
```

```bash
sudo systemctl restart postgresql
```

### Clio Config (`/etc/clio/config.json`)

```json
{
  "database": {
    "type": "postgres",
    "host": "127.0.0.1",
    "port": 5432,
    "database": "clio",
    "user": "clio",
    "password": "strong_password",
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
  "cache": {
    "num_diffs": 32
  }
}
```

---

## 9. Log Rotation

```bash
# /etc/logrotate.d/rippled
/var/log/rippled/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    copytruncate
}
```

```bash
# Test log rotation
logrotate -f /etc/logrotate.d/rippled
```

---

## 10. Database Recovery

### NuDB Corruption

```bash
# Stop rippled
systemctl stop rippled

# Delete and re-sync from scratch
rm -rf /var/lib/rippled/db/nudb/*

# Restart — rippled will sync from peers
systemctl start rippled

# Monitor sync progress
rippled server_info | grep complete_ledgers
```

### Check sync status

```bash
rippled server_info
# Look for: "complete_ledgers": "87000000-87654321"
# Or: "complete_ledgers": "empty" (still syncing)
```

### Force re-sync from specific peer

```bash
rippled connect <peer_ip> 51235
```

---

## 11. Firewall Rules

```bash
# UFW setup
ufw allow 22/tcp        # SSH
ufw allow 51235/tcp     # XRPL peer protocol
ufw allow 6006/tcp      # WebSocket public (optional)
ufw allow 51233/tcp     # Clio public (optional)

# Block admin port from public
ufw deny 5005/tcp       # RPC admin — localhost only
ufw deny 50051/tcp      # gRPC — localhost only

ufw enable
```

---

## 12. Monitoring

### Prometheus + rippled

```bash
# rippled exposes metrics at:
curl http://127.0.0.1:5005/ -d '{"method":"get_counts"}'
```

### Health check script

```bash
#!/bin/bash
# /usr/local/bin/rippled-health.sh

STATUS=$(rippled server_info 2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
info = data['result']['info']
print(info['server_state'], info['complete_ledgers'])
" 2>/dev/null)

if [[ "$STATUS" == *"full"* ]] || [[ "$STATUS" == *"proposing"* ]]; then
    echo "OK: $STATUS"
    exit 0
else
    echo "CRITICAL: $STATUS"
    exit 2
fi
```

```bash
# Cron: check every minute
* * * * * /usr/local/bin/rippled-health.sh >> /var/log/rippled-health.log 2>&1
```

---

## 13. Performance Tuning

```ini
# rippled.cfg additions

[io_threads]
6

[workers]
6

[fetch_depth]
full

# Increase peer count for better sync
[peers_max]
40

# Tune transaction queue
[transaction_queue]
ledgers_in_queue = 20
minimum_txn_in_ledger_standalone = 7
minimum_txn_in_ledger = 5
target_txn_in_ledger = 15
normal_consensus_increase_percent = 25
slow_consensus_decrease_percent = 50
maximum_txn_in_queue = 1000
maximum_txn_per_account = 10
```
