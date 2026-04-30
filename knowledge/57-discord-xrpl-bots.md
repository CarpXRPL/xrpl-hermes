# 57 — Discord XRPL Bots

Build Discord bots with slash commands for XRPL queries, AMM monitoring, and rich transaction embeds.

---

## Stack

- `discord.py>=2.0` (slash commands via app_commands)
- `xrpl-py>=2.0.0`
- `aiohttp` for async HTTP (included with discord.py)

```bash
pip install discord.py xrpl-py
```

---

## Bot Setup

1. Create application at https://discord.com/developers/applications
2. Add bot, enable `applications.commands` scope
3. Copy `DISCORD_BOT_TOKEN`

```python
import discord
from discord import app_commands

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")

client.run("YOUR_BOT_TOKEN")
```

---

## Slash Commands

### /balance

```python
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountInfo
from xrpl.utils import drops_to_xrp

XRPL = JsonRpcClient("https://xrplcluster.com")

@tree.command(name="balance", description="Check XRP balance for an address")
@app_commands.describe(address="XRPL r-address")
async def balance_cmd(interaction: discord.Interaction, address: str):
    await interaction.response.defer()
    try:
        resp = XRPL.request(AccountInfo(account=address, ledger_index="validated"))
        xrp = drops_to_xrp(str(resp.result["account_data"]["Balance"]))
        embed = discord.Embed(title="XRPL Account", color=0x00CED1)
        embed.add_field(name="Address", value=f"`{address}`", inline=False)
        embed.add_field(name="Balance", value=f"{xrp:,.6f} XRP", inline=True)
        embed.add_field(name="Sequence", value=str(resp.result["account_data"]["Sequence"]), inline=True)
        embed.set_footer(text="xrpl-hermes")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"Error: {e}")
```

---

### /tx

Display transaction details in a rich embed:

```python
from xrpl.models.requests import Tx

@tree.command(name="tx", description="Look up a transaction by hash")
@app_commands.describe(hash="Transaction hash (64 hex chars)")
async def tx_cmd(interaction: discord.Interaction, hash: str):
    await interaction.response.defer()
    try:
        resp = XRPL.request(Tx(transaction=hash))
        tx = resp.result
        result_code = tx.get("meta", {}).get("TransactionResult", "unknown")
        color = 0x00FF00 if result_code == "tesSUCCESS" else 0xFF0000

        embed = discord.Embed(
            title=f"Transaction: {tx.get('TransactionType', 'Unknown')}",
            color=color
        )
        embed.add_field(name="Hash", value=f"`{hash[:16]}...`", inline=False)
        embed.add_field(name="Account", value=f"`{tx.get('Account', '?')}`", inline=True)
        embed.add_field(name="Result", value=result_code, inline=True)
        embed.add_field(name="Ledger", value=str(tx.get("inLedger", "?")), inline=True)

        amt = tx.get("Amount", "")
        if isinstance(amt, str):
            embed.add_field(name="Amount", value=f"{int(amt)/1_000_000:.6f} XRP", inline=True)

        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"Error: {e}")
```

---

## AMM Pool Event Monitoring

Watch an AMM pool for large trades and post alerts to a channel:

```python
import asyncio
import websockets
import json

AMM_ASSET1_ISSUER = "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh"
ALERT_CHANNEL_ID = 123456789  # your Discord channel ID
LARGE_TRADE_XRP = 10000  # alert if trade > 10,000 XRP

async def amm_monitor(client_bot: discord.Client):
    channel = client_bot.get_channel(ALERT_CHANNEL_ID)
    async with websockets.connect("wss://xrplcluster.com") as ws:
        await ws.send(json.dumps({"command": "subscribe", "streams": ["transactions"]}))
        async for raw in ws:
            msg = json.loads(raw)
            if msg.get("type") != "transaction":
                continue
            tx = msg.get("transaction", {})
            if tx.get("TransactionType") not in ("OfferCreate", "AMMDeposit", "AMMWithdraw"):
                continue
            amt = tx.get("Amount", "0")
            drops = int(amt) if isinstance(amt, str) else 0
            if drops > LARGE_TRADE_XRP * 1_000_000:
                embed = discord.Embed(title="Large AMM Trade Detected", color=0xFFAA00)
                embed.add_field(name="Type", value=tx["TransactionType"], inline=True)
                embed.add_field(name="Amount", value=f"{drops/1_000_000:,.0f} XRP", inline=True)
                embed.add_field(name="Account", value=f"`{tx.get('Account','?')[:12]}...`", inline=True)
                if channel:
                    await channel.send(embed=embed)

# In on_ready: asyncio.create_task(amm_monitor(client))
```

---

## Embed Formatting Patterns

```python
# Success embed
embed = discord.Embed(title="Payment Sent", color=discord.Color.green())
embed.set_thumbnail(url="https://xrpl.org/assets/img/xrp-symbol.svg")
embed.add_field(name="Amount", value="100 XRP", inline=True)
embed.add_field(name="Status", value="tesSUCCESS", inline=True)
embed.set_footer(text="Powered by xrpl-hermes | XRPL Mainnet")

# Error embed
embed = discord.Embed(title="Transaction Failed", color=discord.Color.red())
embed.description = "tecINSUF_RESERVE_LINE: not enough XRP to cover reserve"

# Info embed with explorer link
embed = discord.Embed(
    title="Transaction",
    url=f"https://livenet.xrpl.org/transactions/{tx_hash}",
    color=0x0088CC
)
```

---

## Full Bot Skeleton

```python
#!/usr/bin/env python3
import os
import asyncio
import discord
from discord import app_commands
from xrpl.clients import JsonRpcClient

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
XRPL = JsonRpcClient("https://xrplcluster.com")

# ... add slash commands here ...

@client.event
async def on_ready():
    await tree.sync()
    print(f"Ready: {client.user}")

def main():
    client.run(os.environ["DISCORD_BOT_TOKEN"])

if __name__ == "__main__":
    main()
```

---

## Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install discord.py xrpl-py
COPY bot.py .
CMD ["python3", "bot.py"]
```

```bash
docker run -d -e DISCORD_BOT_TOKEN=... xrpl-discord-bot
```

---

## References

- discord.py docs: https://discordpy.readthedocs.io/
- Discord developer portal: https://discord.com/developers/applications
- XRPL WebSocket subscribe: https://xrpl.org/subscribe.html
