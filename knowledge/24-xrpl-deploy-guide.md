# XRPL Deployment Guide

## Overview

Deploying XRPL applications involves frontend hosting (static sites, dApps), backend bots (Python/Node.js services), and infrastructure (rippled nodes, databases). This guide covers recommended hosting, VPS configuration, systemd services, monitoring, and SSL.

---

## 1. Frontend Deployment Options

### Vercel (Recommended for Next.js/React)

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd my-xrpl-dapp
vercel --prod

# Environment variables
vercel env add NEXT_PUBLIC_XRPL_NODE=wss://xrplcluster.com production
vercel env add NEXT_PUBLIC_NETWORK=mainnet production
```

`vercel.json`:
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs",
  "rewrites": [
    { "source": "/api/:path*", "destination": "/api/:path*" }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" }
      ]
    }
  ]
}
```

### Netlify

```bash
npm install -g netlify-cli
netlify deploy --prod --dir=dist
```

`netlify.toml`:
```toml
[build]
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

### Arweave Permaweb (Permanent Hosting)

```bash
npm install -g arkb

# Build static site
npm run build

# Deploy to Arweave (costs AR tokens)
arkb deploy dist/ --wallet wallet.json --tag-name App-Name --tag-value "MyXRPLApp"

# Result: permanent URL like https://arweave.net/TXID
```

For Arweave deployment:
- Install wallet: Download from arweave.org
- Get AR tokens from exchanges
- Cost: ~$0.01 per MB (permanent forever)

### IPFS via Fleek

```bash
# Fleek CLI
npm install -g @fleekxyz/cli
fleek login
fleek sites deploy
```

---

## 2. Backend Bot Deployment

### Recommended VPS: Hetzner

| Plan | Specs | Price | Use Case |
|------|-------|-------|----------|
| CX22 | 2 vCPU, 4 GB RAM, 40 GB SSD | ~$5/mo | Light bots, cron jobs |
| CX32 | 4 vCPU, 8 GB RAM, 80 GB SSD | ~$8/mo | Production bots |
| CX42 | 8 vCPU, 16 GB RAM, 160 GB SSD | ~$16/mo | High-throughput bots |
| AX52 | 12 vCPU, 64 GB RAM, 512 GB NVMe | ~$45/mo | rippled node |

```bash
# Initial server setup (Ubuntu 22.04)
ssh root@your-server-ip

# Update and install essentials
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv nodejs npm git ufw fail2ban curl

# Create service user
useradd -m -s /bin/bash xrplbot
su - xrplbot

# Install your bot
git clone https://github.com/yourorg/xrpl-bot.git
cd xrpl-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 3. Systemd Service Files

### Python Bot

```bash
cat > /etc/systemd/system/xrpl-bot.service << 'EOF'
[Unit]
Description=XRPL Trading Bot
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=xrplbot
WorkingDirectory=/home/xrplbot/xrpl-bot
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=/home/xrplbot/xrpl-bot/.env
ExecStart=/home/xrplbot/xrpl-bot/venv/bin/python bot.py
Restart=on-failure
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=xrpl-bot

# Resource limits
LimitNOFILE=65536
MemoryMax=512M

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now xrpl-bot
```

### Node.js Bot

```bash
cat > /etc/systemd/system/xrpl-node-bot.service << 'EOF'
[Unit]
Description=XRPL Node.js Bot
After=network.target

[Service]
Type=simple
User=xrplbot
WorkingDirectory=/home/xrplbot/xrpl-node-bot
EnvironmentFile=/home/xrplbot/xrpl-node-bot/.env
ExecStart=/usr/bin/node /home/xrplbot/xrpl-node-bot/index.js
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
```

### Environment File

```bash
# /home/xrplbot/xrpl-bot/.env
XRPL_NODE=wss://xrplcluster.com
WALLET_SEED=sn...
NETWORK=mainnet
LOG_LEVEL=info
ALERT_WEBHOOK=https://hooks.slack.com/...
```

Secure the env file:
```bash
chmod 600 /home/xrplbot/xrpl-bot/.env
chown xrplbot:xrplbot /home/xrplbot/xrpl-bot/.env
```

---

## 4. Cron Jobs

For scheduled tasks (not continuous bots):

```bash
# Run price check every minute
crontab -e -u xrplbot

# Add:
* * * * * /home/xrplbot/xrpl-bot/venv/bin/python /home/xrplbot/xrpl-bot/price_check.py >> /var/log/xrplbot/price_check.log 2>&1

# Hourly report
0 * * * * /home/xrplbot/xrpl-bot/venv/bin/python /home/xrplbot/xrpl-bot/hourly_report.py

# Daily cleanup at 3am
0 3 * * * /home/xrplbot/xrpl-bot/venv/bin/python /home/xrplbot/xrpl-bot/cleanup.py
```

---

## 5. Monitoring with Uptime Kuma

Uptime Kuma is a self-hosted monitoring tool:

```bash
# Docker installation
docker run -d \
  --name uptime-kuma \
  --restart unless-stopped \
  -p 3001:3001 \
  -v uptime-kuma:/app/data \
  louislam/uptime-kuma:1

# Access at http://your-server:3001
```

Monitor your XRPL services:
- **HTTP monitor**: Check your bot's health endpoint
- **TCP monitor**: Check rippled port 51235
- **WebSocket monitor**: Check wss://your-node:6006

Webhook alerts to Discord:
```
Webhook URL: https://discord.com/api/webhooks/...
```

---

## 6. Cloudflare SSL + Reverse Proxy

```nginx
# /etc/nginx/sites-available/xrpl-api
server {
    listen 80;
    server_name api.yourxrplapp.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name api.yourxrplapp.com;

    ssl_certificate /etc/letsencrypt/live/api.yourxrplapp.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourxrplapp.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # XRPL WebSocket proxy
    location /xrpl-ws {
        proxy_pass wss://127.0.0.1:6006;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

```bash
# Install certbot
apt install -y certbot python3-certbot-nginx

# Get SSL cert
certbot --nginx -d api.yourxrplapp.com

# Auto-renew
systemctl enable --now certbot.timer
```

### Cloudflare Proxy Setup

1. Add site to Cloudflare
2. Update DNS nameservers
3. Enable "Proxy" (orange cloud) for DNS records
4. SSL mode: **Full (strict)**
5. Enable: "Always Use HTTPS", "Automatic HTTPS Rewrites"

---

## 7. Firewall Configuration

```bash
# UFW setup
ufw default deny incoming
ufw default allow outgoing

ufw allow ssh
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
ufw allow 51235/tcp  # XRPL peer (if running rippled)

# Optional: restrict SSH to your IP
ufw allow from YOUR_IP to any port 22

ufw enable
ufw status verbose
```

```bash
# Fail2ban for SSH protection
cat > /etc/fail2ban/jail.local << 'EOF'
[sshd]
enabled = true
port = ssh
maxretry = 5
bantime = 3600
findtime = 600
EOF

systemctl enable --now fail2ban
```

---

## 8. Log Management

```bash
# View bot logs
journalctl -u xrpl-bot -f
journalctl -u xrpl-bot --since "1 hour ago"
journalctl -u xrpl-bot -n 100

# Logrotate for custom log files
cat > /etc/logrotate.d/xrplbot << 'EOF'
/var/log/xrplbot/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
    su xrplbot xrplbot
}
EOF
```

---

## 9. Docker Compose Setup

For multi-service XRPL applications:

```yaml
# docker-compose.yml
version: '3.8'

services:
  xrpl-bot:
    build: ./bot
    restart: unless-stopped
    env_file: .env
    volumes:
      - ./data:/app/data
    depends_on:
      - redis
    networks:
      - xrpl-net

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis-data:/data
    networks:
      - xrpl-net

  api:
    build: ./api
    restart: unless-stopped
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      - redis
    networks:
      - xrpl-net

volumes:
  redis-data:

networks:
  xrpl-net:
```

```bash
# Deploy
docker compose up -d

# View logs
docker compose logs -f xrpl-bot

# Update
git pull
docker compose build
docker compose up -d --force-recreate
```

---

## 10. Health Check Endpoint

Add to your bot:

```python
from fastapi import FastAPI
import asyncio

app = FastAPI()

bot_state = {
    "last_ledger": 0,
    "last_tx_hash": None,
    "errors_last_hour": 0,
    "started_at": None
}

@app.get("/health")
async def health():
    from xrpl.models.requests import ServerInfo
    try:
        resp = client.request(ServerInfo())
        ledger = resp.result["info"]["validated_ledger"]["seq"]
        return {
            "status": "healthy",
            "xrpl_connected": True,
            "current_ledger": ledger,
            "bot_last_ledger": bot_state["last_ledger"],
            "errors_last_hour": bot_state["errors_last_hour"]
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}, 503
```
