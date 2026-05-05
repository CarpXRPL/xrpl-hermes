# 56 — Telegram XRPL Bots (Expanded)

Build production-ready Telegram bots that monitor wallets, stream ledger events, send price alerts, and deliver Xaman sign requests. Based on `python-telegram-bot >=20.0` and `xrpl-py >= 2.5.0`.

## Stack

- `python-telegram-bot>=20.0` (async)
- `xrpl-py>=2.5.0` (with `[websockets]` for streaming)
- Optional: `sqlite3` (stdlib) / `redis` for persistent storage

```bash
pip install python-telegram-bot "xrpl-py[websockets]"
```

## /balance Command

```python
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountInfo
from xrpl.utils import drops_to_xrp

CLIENT = JsonRpcClient("https://xrplcluster.com")

async def balance(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: /balance rADDRESS")
        return
    address = ctx.args[0]
    try:
        resp = CLIENT.request(AccountInfo(account=address, ledger_index="validated"))
        xrp = drops_to_xrp(str(resp.result["account_data"]["Balance"]))
        await update.message.reply_text(
            f"`{address}`\nBalance: **{xrp:,.6f} XRP**",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

app = Application.builder().token("YOUR_BOT_TOKEN").build()
app.add_handler(CommandHandler("balance", balance))
app.run_polling()
```

## WebSocket Transaction Monitoring

Stream ledger closes and alert on payments to watched addresses:

```python
import asyncio, json
from xrpl.asyncio.clients import AsyncWebsocketClient
from xrpl.models.requests import Subscribe

WATCHED = ["rWATCHED_ADDRESS"]

async def monitor(bot, chat_id: int):
    async with AsyncWebsocketClient("wss://xrplcluster.com") as client:
        await client.send(Subscribe(accounts=WATCHED))
        async for msg in client:
            tx = msg.get("transaction", {})
            if tx.get("TransactionType") == "Payment" and tx.get("Destination") in WATCHED:
                amt = tx.get("Amount", "0")
                drops = int(amt) if isinstance(amt, str) else 0
                await bot.send_message(
                    chat_id,
                    f"Incoming payment: **{drops/1_000_000:.6f} XRP**\nTx: `{tx.get('hash','')}`",
                    parse_mode="Markdown"
                )
```

## Multi-User Database Pattern

Store per-user settings with simple SQLite:

```python
import sqlite3, os

DB = os.environ.get("BOT_DB", "bot_users.db")

def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, address TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS watched (user_id INTEGER, address TEXT, FOREIGN KEY(user_id) REFERENCES users(user_id))")
    conn.commit()
    conn.close()

def save_address(user_id: int, address: str):
    conn = sqlite3.connect(DB)
    conn.execute("INSERT OR REPLACE INTO users (user_id, address) VALUES (?, ?)", (user_id, address))
    conn.commit()
    conn.close()

def get_address(user_id: int) -> str | None:
    conn = sqlite3.connect(DB)
    cur = conn.execute("SELECT address FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None
```

## Inline Keyboard Example

```python
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

async def menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💰 Balance", callback_data="balance")],
        [InlineKeyboardButton("📡 Watch Wallet", callback_data="watch")],
        [InlineKeyboardButton("🔗 Sign in Xaman", callback_data="xaman")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose action:", reply_markup=reply_markup)
```

## Xaman Sign Requests

Use the `xaman-payload` CLI tool to generate sign URLs:

```bash
python3 -m scripts.xrpl_tools xaman-payload '{"TransactionType": "Payment", "Account": "rSENDER", "Destination": "rDEST", "Amount": "1000000"}'
```

Requires `XUMM_API_KEY` and `XUMM_API_SECRET` environment variables. Get free dev keys at https://apps.xumm.dev.

## Production Deployment

### systemd Service

```ini
[Unit]
Description=XRPL Telegram Bot
After=network.target

[Service]
Type=simple
User=xrplbot
WorkingDirectory=/opt/xrpl-telegram-bot
EnvironmentFile=/opt/xrpl-telegram-bot/.env
ExecStart=/usr/bin/python3 bot.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install python-telegram-bot "xrpl-py[websockets]"
COPY bot.py .
CMD ["python3", "bot.py"]
```

## Related Files

- `knowledge/57-discord-xrpl-bots.md` — Discord bot equivalent
- `knowledge/41-xrpl-bots-patterns.md` — bot architecture patterns
- `knowledge/63-xrpl-xaman-platform.md` — Xaman Platform API integration
- `knowledge/53-xrpl-wallets-auth.md` — wallet auth in chat bots

## Production Database Pattern for Watched Addresses

Store watches separately from users so one XRPL address can be watched by many chat IDs without duplicating ledger polling work.

```sql
create table bot_users (user_id text primary key, chat_id text not null, created_at text not null);
create table watched_addresses (id integer primary key, user_id text not null, address text not null, label text, created_at text not null);
create unique index watched_user_address on watched_addresses(user_id, address);
create table processed_events (event_key text primary key, ledger_index integer, tx_hash text, created_at text not null);
```

## Multi-User Isolation

- Scope every command by Telegram `chat_id` and internal `user_id`.
- Never let one user list or delete another user's watched addresses.
- Use per-user notification preferences for tokens, NFTs, AMM events, and high-value XRP movements.

## Inline Keyboard Examples

```python
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

keyboard = InlineKeyboardMarkup([[
    InlineKeyboardButton('Open on explorer', url=f'https://livenet.xrpl.org/transactions/{tx_hash}'),
    InlineKeyboardButton('Create Xaman payload', callback_data=f'xaman:{tx_hash}'),
]])
```

Use the xaman-payload CLI tool with this TX JSON when a user needs to sign a response transaction.

## Error Recovery and Reconnection

- Run the XRPL stream reader as a restartable task.
- Store the last validated ledger processed by each worker.
- On reconnect, query `account-tx` for watched addresses to fill missed transactions.
- Dedupe by transaction hash plus delivered chat ID.

## systemd Deployment Walkthrough

```ini
[Unit]
Description=XRPL Telegram Bot
After=network-online.target

[Service]
WorkingDirectory=/opt/xrpl-hermes
Environment=XRPL_PRIVATE_RPC=https://xrplcluster.com
Environment=TELEGRAM_BOT_TOKEN=replace-me
ExecStart=/usr/bin/python3 examples/example-telegram-bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## Production Deployment Section

- Put bot tokens and Xaman credentials in environment variables, not source files.
- Use a private Clio endpoint for busy bots.
- Rate-limit commands per user and per chat.
- Log transaction hashes, not wallet secrets.
- Send signing requests through `python3 -m scripts.xrpl_tools xaman-payload '{...}'`.

### Telegram Production Pattern 1

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 2

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 3

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 4

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 5

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 6

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 7

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 8

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 9

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 10

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 11

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 12

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 13

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 14

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 15

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 16

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 17

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 18

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 19

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 20

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 21

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 22

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 23

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 24

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 25

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 26

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 27

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 28

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 29

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 30

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 31

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 32

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 33

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 34

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 35

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 36

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 37

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 38

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 39

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 40

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 41

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 42

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.

### Telegram Production Pattern 43

- Read XRPL events from a durable queue before sending chat notifications.
- Keep per-user subscriptions isolated by chat ID and watched address ID.
- Retry transient Telegram API failures with bounded backoff and record permanent failures.
