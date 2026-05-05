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

## Advanced Embed Examples

Use embeds for bot outputs that users scan repeatedly. Keep each field short, put hashes behind explorer URLs, and use color only for state.

### Account Health Embed

```python
def account_health_embed(address: str, account_data: dict) -> discord.Embed:
    balance_drops = int(account_data.get("Balance", "0"))
    owner_count = int(account_data.get("OwnerCount", 0))
    reserve_drops = 10_000_000 + owner_count * 2_000_000
    spendable = max(balance_drops - reserve_drops, 0) / 1_000_000

    embed = discord.Embed(title="Account Health", color=0x2ECC71)
    embed.add_field(name="Address", value=f"`{address}`", inline=False)
    embed.add_field(name="Balance", value=f"{balance_drops / 1_000_000:,.6f} XRP", inline=True)
    embed.add_field(name="Owner Count", value=str(owner_count), inline=True)
    embed.add_field(name="Spendable", value=f"{spendable:,.6f} XRP", inline=True)
    embed.add_field(name="Sequence", value=str(account_data.get("Sequence", "?")), inline=True)
    embed.add_field(name="Flags", value=str(account_data.get("Flags", 0)), inline=True)
    embed.set_footer(text="Validated ledger data")
    return embed
```

### Payment Embed

```python
def payment_embed(tx: dict, meta: dict) -> discord.Embed:
    result = meta.get("TransactionResult", "unknown")
    color = 0x2ECC71 if result == "tesSUCCESS" else 0xE74C3C
    tx_hash = tx.get("hash", "")

    embed = discord.Embed(
        title="Payment",
        url=f"https://livenet.xrpl.org/transactions/{tx_hash}" if tx_hash else None,
        color=color,
    )
    embed.add_field(name="Result", value=result, inline=True)
    embed.add_field(name="From", value=f"`{tx.get('Account', '?')}`", inline=False)
    embed.add_field(name="To", value=f"`{tx.get('Destination', '?')}`", inline=False)
    amount = tx.get("Amount")
    if isinstance(amount, str):
        embed.add_field(name="Amount", value=f"{int(amount) / 1_000_000:,.6f} XRP", inline=True)
    elif isinstance(amount, dict):
        value = f"{amount.get('value')} {amount.get('currency')}"
        embed.add_field(name="Amount", value=value, inline=True)
        embed.add_field(name="Issuer", value=f"`{amount.get('issuer')}`", inline=False)
    return embed
```

### Token Balance Embed

```python
def token_balance_embed(address: str, lines: list[dict]) -> discord.Embed:
    embed = discord.Embed(title="XRPL Tokens", color=0x3498DB)
    embed.add_field(name="Account", value=f"`{address}`", inline=False)
    for line in lines[:20]:
        name = f"{line.get('currency', '?')} balance"
        value = f"{line.get('balance', '0')} issued by `{line.get('account', '?')}`"
        embed.add_field(name=name, value=value, inline=False)
    if len(lines) > 20:
        embed.set_footer(text=f"Showing 20 of {len(lines)} trust lines")
    return embed
```

## Slash Command Patterns

Use one command per high-value action. Defer immediately for network calls so Discord does not treat the interaction as timed out.

```python
@tree.command(name="account", description="Show XRPL account status")
@app_commands.describe(address="XRPL r-address")
async def account_cmd(interaction: discord.Interaction, address: str):
    await interaction.response.defer(ephemeral=True)
    resp = XRPL.request(AccountInfo(account=address, ledger_index="validated"))
    await interaction.followup.send(embed=account_health_embed(address, resp.result["account_data"]))
```

```python
@tree.command(name="trustlines", description="Show token trust lines")
@app_commands.describe(address="XRPL r-address", currency="Optional currency filter")
async def trustlines_cmd(interaction: discord.Interaction, address: str, currency: str | None = None):
    await interaction.response.defer(ephemeral=True)
    req = {"command": "account_lines", "account": address, "ledger_index": "validated"}
    resp = XRPL.request(req)
    lines = resp.result.get("lines", [])
    if currency:
        lines = [line for line in lines if line.get("currency") == currency.upper()]
    await interaction.followup.send(embed=token_balance_embed(address, lines))
```

```python
@tree.command(name="watch_amm", description="Register an AMM alert threshold")
@app_commands.describe(pair="Pair label, for example XRP/USD", threshold_xrp="Alert threshold")
async def watch_amm_cmd(interaction: discord.Interaction, pair: str, threshold_xrp: int):
    await interaction.response.defer(ephemeral=True)
    # Persist guild_id, channel_id, pair, and threshold_xrp in a database.
    embed = discord.Embed(title="AMM Watch Added", color=0x2ECC71)
    embed.add_field(name="Pair", value=pair.upper(), inline=True)
    embed.add_field(name="Threshold", value=f"{threshold_xrp:,} XRP", inline=True)
    await interaction.followup.send(embed=embed, ephemeral=True)
```

Autocomplete helps prevent invalid currency and pair inputs:

```python
SUPPORTED_PAIRS = ["XRP/USD", "XRP/EUR", "XRP/BTC", "SOLO/XRP", "RLUSD/XRP"]

@watch_amm_cmd.autocomplete("pair")
async def pair_autocomplete(interaction: discord.Interaction, current: str):
    current = current.upper()
    return [
        app_commands.Choice(name=pair, value=pair)
        for pair in SUPPORTED_PAIRS
        if current in pair
    ][:25]
```

## AMM Monitoring Details

A production monitor should track validated transactions, not proposed transactions. Proposed transactions can fail or change before validation.

```python
def is_amm_relevant(tx: dict) -> bool:
    return tx.get("TransactionType") in {
        "AMMCreate",
        "AMMDeposit",
        "AMMWithdraw",
        "AMMVote",
        "AMMBid",
        "OfferCreate",
        "OfferCancel",
    }
```

```python
def extract_xrp_volume(tx: dict) -> int:
    fields = ["Amount", "Amount2", "TakerGets", "TakerPays"]
    volume = 0
    for field in fields:
        value = tx.get(field)
        if isinstance(value, str) and value.isdigit():
            volume += int(value)
    return volume
```

```python
async def send_amm_alert(channel: discord.abc.Messageable, tx: dict, tx_hash: str, drops: int):
    embed = discord.Embed(
        title="AMM Activity",
        url=f"https://livenet.xrpl.org/transactions/{tx_hash}",
        color=0xF1C40F,
    )
    embed.add_field(name="Type", value=tx.get("TransactionType", "?"), inline=True)
    embed.add_field(name="XRP Volume", value=f"{drops / 1_000_000:,.2f} XRP", inline=True)
    embed.add_field(name="Account", value=f"`{tx.get('Account', '?')}`", inline=False)
    await channel.send(embed=embed)
```

Monitor reconnects should back off to avoid hammering public infrastructure:

```python
async def run_monitor_forever(bot: discord.Client):
    delay = 1
    while True:
        try:
            await amm_monitor(bot)
            delay = 1
        except Exception as exc:
            print(f"monitor error: {exc}")
            await asyncio.sleep(delay)
            delay = min(delay * 2, 60)
```

## Error Embeds

Return consistent errors so users can understand whether they supplied bad input or the ledger returned a failure.

```python
def error_embed(title: str, message: str, *, code: str | None = None) -> discord.Embed:
    embed = discord.Embed(title=title, description=message[:3500], color=0xE74C3C)
    if code:
        embed.add_field(name="Code", value=f"`{code}`", inline=True)
    embed.set_footer(text="No transaction was submitted")
    return embed
```

```python
async def send_user_error(interaction: discord.Interaction, message: str):
    await interaction.followup.send(
        embed=error_embed("Invalid Request", message),
        ephemeral=True,
    )
```

```python
async def send_ledger_error(interaction: discord.Interaction, exc: Exception):
    await interaction.followup.send(
        embed=error_embed("XRPL Request Failed", str(exc), code=type(exc).__name__),
        ephemeral=True,
    )
```

Map common XRPL result codes to user-facing text:

| Result | Meaning |
|---|---|
| `tesSUCCESS` | The transaction succeeded |
| `tecINSUF_RESERVE_LINE` | The account needs more XRP reserve |
| `tecNO_DST_INSUF_XRP` | The destination account does not exist and the payment is too small |
| `tefPAST_SEQ` | The sequence number is already used |
| `terQUEUED` | The transaction was queued for later validation |

## Production Deployment

Use environment variables for credentials and network URLs:

```bash
export DISCORD_BOT_TOKEN="..."
export XRPL_RPC_URL="https://xrplcluster.com"
export XRPL_WS_URL="wss://xrplcluster.com"
export ALERT_CHANNEL_ID="123456789"
```

Use a minimal requirements file:

```txt
discord.py>=2.3.0
xrpl-py>=2.5.0
websockets>=12.0
python-dotenv>=1.0.0
```

Use a health check task for container platforms:

```python
last_ledger_seen = 0

async def health_tick():
    global last_ledger_seen
    while True:
        try:
            resp = XRPL.request({"command": "ledger_current"})
            last_ledger_seen = int(resp.result["ledger_current_index"])
        except Exception as exc:
            print(f"health check failed: {exc}")
        await asyncio.sleep(30)
```

Operational checklist:

- Sync slash commands on startup, but avoid syncing on every reconnect.
- Store guild-specific settings in SQLite, Postgres, or Redis.
- Keep bot tokens out of source control.
- Use ephemeral responses for private account lookups.
- Use public channel posts only for configured alerts.
- Rate-limit commands by user and guild.
- Separate read-only ledger queries from any signing flow.
- Never ask users to paste seeds, private keys, or mnemonics into Discord.
- Link to Xaman or another wallet for signing instead of custodying keys.
- Log command names and result classes, not full account histories.
- Pin the Docker image tag for repeatable deployments.
- Add process supervision through systemd, Docker restart policies, or a platform worker.

Example systemd unit:

```ini
[Unit]
Description=XRPL Discord Bot
After=network-online.target

[Service]
WorkingDirectory=/opt/xrpl-discord-bot
EnvironmentFile=/opt/xrpl-discord-bot/.env
ExecStart=/usr/bin/python3 bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

---

## References

- discord.py docs: https://discordpy.readthedocs.io/
- Discord developer portal: https://discord.com/developers/applications
- XRPL WebSocket subscribe: https://xrpl.org/subscribe.html

---

## Related Files

- `knowledge/41-xrpl-bots-patterns.md` — bot architecture patterns
- `knowledge/56-telegram-xrpl-bots.md` — Telegram bot equivalent
- `knowledge/53-xrpl-wallets-auth.md` — wallet auth in chat bots

## Slash Command Auto-Registration Patterns

Register commands at startup for development guilds and during deployment for global commands.

```python
@bot.tree.command(name='watch', description='Watch an XRPL account')
async def watch(interaction, address: str):
    await interaction.response.defer(ephemeral=True)
    await add_watch(interaction.user.id, address)
    await interaction.followup.send(f'Watching {address}', ephemeral=True)
```

## Embed Examples for Trades and Balances

```python
embed = discord.Embed(title='XRPL Trade', color=0x2f80ed)
embed.add_field(name='Pair', value='XRP/USD')
embed.add_field(name='Amount', value='250 XRP')
embed.add_field(name='Ledger', value=str(ledger_index))
```

## AMM Monitoring Examples

- Subscribe to transactions and classify `AMMDeposit`, `AMMWithdraw`, `AMMVote`, and `AMMBid`.
- Query pool state after every AMM event before posting a summary.
- Include trading fee, LP token changes, and affected assets in the embed.

## Error Embeds

```python
embed = discord.Embed(title='XRPL Error', description='The stream reconnected and is replaying missed ledgers.', color=0xff5555)
embed.add_field(name='Action', value='No user action needed')
```

### Discord Production Pattern 1

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 2

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 3

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 4

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 5

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 6

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 7

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 8

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 9

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 10

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 11

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 12

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 13

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 14

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 15

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 16

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 17

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 18

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 19

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 20

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 21

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 22

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 23

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 24

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 25

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 26

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 27

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 28

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 29

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 30

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 31

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 32

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 33

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 34

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 35

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 36

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 37

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 38

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 39

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 40

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.

### Discord Production Pattern 41

- Use ephemeral responses for account setup and public embeds for channel alerts.
- Store guild ID, channel ID, user ID, watched address, and notification type separately.
- Batch high-volume AMM and DEX events so channels do not get flooded.
