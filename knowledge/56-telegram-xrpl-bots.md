# 56 — Telegram XRPL Bots

Build Telegram bots that interact with the XRPL — balance checks, transaction monitoring, price alerts, and Xaman deep-link signing.

---

## Stack

- `python-telegram-bot>=20.0` (async, PTB v20+)
- `xrpl-py>=2.0.0`
- `websockets` (for live ledger streaming)
- Optional: `python-dotenv` for env management

```bash
pip install python-telegram-bot xrpl-py websockets python-dotenv
```

---

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
        await update.message.reply_text(f"`{address}`\nBalance: **{xrp:,.6f} XRP**", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

app = Application.builder().token("YOUR_BOT_TOKEN").build()
app.add_handler(CommandHandler("balance", balance))
app.run_polling()
```

---

## Xaman Deep-Link Signing from Telegram

Xaman (formerly XUMM) can sign transactions via a QR code or mobile deep-link. Generate the link in Python and send it to the user:

```python
import json
from urllib.parse import quote

def xaman_sign_url(tx_json: dict) -> str:
    """Generate a Xaman sign deep-link from a TX JSON dict."""
    payload = quote(json.dumps(tx_json))
    return f"https://xumm.app/sign/{payload}"

# Example: build a payment and send sign link
async def pay(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    tx = {
        "TransactionType": "Payment",
        "Account": "rSENDER",
        "Destination": "rDEST",
        "Amount": "1000000",
    }
    url = xaman_sign_url(tx)
    await update.message.reply_text(
        f"[Sign this payment in Xaman]({url})",
        parse_mode="Markdown"
    )
```

For production, use the [XUMM SDK](https://github.com/XRPL-Labs/XUMM-SDK) to create payloads server-side and get webhook callbacks when signed.

---

## WebSocket Transaction Monitoring

Stream ledger closes and alert on incoming payments to a watched address:

```python
import asyncio
import websockets
import json
from telegram.ext import Application

WATCHED = "rWATCHED_ADDRESS"
WS_URL = "wss://xrplcluster.com"

async def monitor(bot, chat_id: int):
    async with websockets.connect(WS_URL) as ws:
        await ws.send(json.dumps({
            "command": "subscribe",
            "accounts": [WATCHED]
        }))
        async for raw in ws:
            msg = json.loads(raw)
            if msg.get("type") == "transaction":
                tx = msg["transaction"]
                if tx.get("TransactionType") == "Payment" and tx.get("Destination") == WATCHED:
                    amt = tx.get("Amount", "0")
                    drops = int(amt) if isinstance(amt, str) else 0
                    await bot.send_message(
                        chat_id,
                        f"Incoming payment: {drops/1_000_000:.6f} XRP\nTx: `{tx['hash']}`",
                        parse_mode="Markdown"
                    )

# Run monitor alongside the bot:
# asyncio.create_task(monitor(app.bot, CHAT_ID))
```

---

## Price Alert Bot

Poll Flare FTSOv2 price feeds and alert when XRP crosses a threshold:

```python
import asyncio
import aiohttp

XRP_ALERT_ABOVE = 1.50  # USD

async def price_poller(bot, chat_id: int):
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get("https://api.flare.network/price/XRP/USD") as r:
                    data = await r.json()
                    price = float(data.get("price", 0))
                    if price > XRP_ALERT_ABOVE:
                        await bot.send_message(chat_id, f"XRP alert: ${price:.4f} > ${XRP_ALERT_ABOVE}")
            except Exception:
                pass
            await asyncio.sleep(60)
```

---

## Full Bot Skeleton

```python
#!/usr/bin/env python3
import os
from telegram.ext import Application, CommandHandler
# ... handlers above ...

def main():
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("pay", pay))
    app.run_polling()

if __name__ == "__main__":
    main()
```

---

## Deployment

Run the bot as a systemd service or in Docker:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY bot.py .
CMD ["python3", "bot.py"]
```

```bash
docker build -t xrpl-telegram-bot .
docker run -d -e TELEGRAM_BOT_TOKEN=... xrpl-telegram-bot
```

---

## References

- python-telegram-bot docs: https://docs.python-telegram-bot.org/
- XUMM SDK (payload signing): https://github.com/XRPL-Labs/XUMM-SDK
- XRPL WebSocket API: https://xrpl.org/websocket-api-tool.html
