# Private XRPL Node — Docker Deployment

Run your own rippled + Clio stack for a private, high-performance XRPL endpoint.

**Cost**: ~$5–7/month on Hetzner CX22 or Contabo VPS S  
**Sync time**: ~24 hours for full ledger history  
**Privacy**: your queries never hit public endpoints

---

## Requirements

- VPS with 4 GB RAM, 80 GB SSD minimum (Hetzner CX22: 4 GB / 80 GB SSD, ~€4/mo)
- Docker Engine + Docker Compose v2
- Ports 5005, 6006, 51233, 51234 open in firewall

---

## Quick Deploy

```bash
# 1. Clone the repo
git clone https://github.com/CarpXRPL/xrpl-hermes-v1.0.git
cd xrpl-hermes-v1.0/deploy

# 2. Start the stack
docker compose up -d

# 3. Watch sync progress (takes ~24h on first run)
docker logs -f xrpl_rippled 2>&1 | grep -i "ledger\|sync\|error"
```

---

## Hetzner Setup Walkthrough

```bash
# On your local machine — create a Hetzner CX22
# (4 vCPU, 8 GB RAM, 80 GB SSD, ~€5/mo)

# SSH into the VPS
ssh root@YOUR_VPS_IP

# Install Docker
curl -fsSL https://get.docker.com | sh
systemctl enable docker

# Open required ports
ufw allow 22/tcp   # SSH
ufw allow 5005/tcp # rippled RPC
ufw allow 6006/tcp # rippled WS
ufw allow 51233/tcp # Clio RPC
ufw allow 51234/tcp # Clio WS
ufw enable

# Clone and deploy
git clone https://github.com/CarpXRPL/xrpl-hermes-v1.0.git
cd xrpl-hermes-v1.0/deploy
docker compose up -d
```

---

## Contabo VPS S (~$5–6/mo)

Contabo VPS S provides 4 vCPU, 8 GB RAM, 200 GB SSD — more than enough.  
Same setup steps as Hetzner above.

---

## Verify Sync Status

```bash
# Check rippled is synced
curl -s -X POST http://localhost:5005 \
  -H "Content-Type: application/json" \
  -d '{"method":"server_info","params":[{}]}' \
  | python3 -m json.tool | grep -A3 "server_state\|complete_ledgers"

# Check Clio is responding
curl -s -X POST http://localhost:51233 \
  -H "Content-Type: application/json" \
  -d '{"method":"server_info","params":[{}]}' \
  | python3 -m json.tool
```

Expected `server_state`: `"full"` or `"proposing"` once synced.

---

## Connect xrpl-hermes to Your Node

```bash
export XRPL_PRIVATE_RPC=http://YOUR_VPS_IP:5005
python3 scripts/xrpl_tools.py server-info
```

Or for Clio (preferred — supports historical queries):

```bash
export XRPL_PRIVATE_RPC=http://YOUR_VPS_IP:51233
python3 scripts/xrpl_tools.py server-info
```

---

## Disk Usage Over Time

| Ledger Age | Approximate Size |
|---|---|
| Full history (~2013–present) | ~20 TB (use online_delete) |
| Recent 256 ledgers only | ~2 GB |
| 1 year of history | ~200 GB |

For most use cases, the default `online_delete` of 256 ledgers is sufficient.  
To keep more history, add to `rippled.cfg`:

```ini
[ledger_history]
12400000
```

---

## Troubleshooting

| Issue | Fix |
|---|---|
| Clio exits immediately | rippled not fully started — wait 2 min and `docker compose restart clio` |
| `server_state: connected` after 1h | Check internet and UNL connectivity: `docker logs xrpl_rippled` |
| Postgres auth error | Delete postgres_data volume and restart: `docker compose down -v && docker compose up -d` |
| Port already in use | Check: `ss -tlnp \| grep 5005` — another process owns the port |
