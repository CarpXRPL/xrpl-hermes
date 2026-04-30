#!/usr/bin/env python3
"""
xrpl-hermes — Discord bot with slash commands for XRPL queries.

Slash commands:
    /balance rADDRESS    — XRP balance with rich embed
    /tx HASH             — transaction details embed
    /price XRP           — Flare FTSOv2 price lookup

Usage:
    pip install discord.py xrpl-py
    export DISCORD_BOT_TOKEN=...
    python3 example-discord-bot.py
"""

import os
import asyncio

from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountInfo, Tx
from xrpl.utils import drops_to_xrp

try:
    import discord
    from discord import app_commands
except ImportError:
    print("Install: pip install discord.py")
    raise

XRPL_CLIENT = JsonRpcClient("https://xrplcluster.com")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@tree.command(name="balance", description="Fetch XRP balance for an XRPL address")
@app_commands.describe(address="XRPL r-address (starts with r)")
async def balance_cmd(interaction: discord.Interaction, address: str):
    await interaction.response.defer()
    try:
        resp = XRPL_CLIENT.request(AccountInfo(account=address, ledger_index="validated"))
        data = resp.result["account_data"]
        xrp = drops_to_xrp(str(data["Balance"]))
        embed = discord.Embed(title="XRPL Account", color=0x00CED1)
        embed.add_field(name="Address", value=f"`{address}`", inline=False)
        embed.add_field(name="Balance", value=f"{xrp:,.6f} XRP", inline=True)
        embed.add_field(name="Sequence", value=str(data["Sequence"]), inline=True)
        embed.set_footer(text="xrpl-hermes | Mainnet")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"Error: {e}")


@tree.command(name="tx", description="Look up an XRPL transaction by hash")
@app_commands.describe(hash="64-character transaction hash")
async def tx_cmd(interaction: discord.Interaction, hash: str):
    await interaction.response.defer()
    try:
        resp = XRPL_CLIENT.request(Tx(transaction=hash))
        tx = resp.result
        result_code = tx.get("meta", {}).get("TransactionResult", "?")
        color = discord.Color.green() if result_code == "tesSUCCESS" else discord.Color.red()

        embed = discord.Embed(
            title=tx.get("TransactionType", "Transaction"),
            url=f"https://livenet.xrpl.org/transactions/{hash}",
            color=color,
        )
        embed.add_field(name="Hash", value=f"`{hash[:20]}...`", inline=False)
        embed.add_field(name="Account", value=f"`{tx.get('Account','?')}`", inline=True)
        embed.add_field(name="Result", value=result_code, inline=True)
        embed.add_field(name="Ledger", value=str(tx.get("inLedger", "?")), inline=True)

        amt = tx.get("Amount", "")
        if isinstance(amt, str) and amt.isdigit():
            embed.add_field(name="Amount", value=f"{int(amt)/1_000_000:,.6f} XRP", inline=True)

        embed.set_footer(text="xrpl-hermes | Mainnet")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"Error: {e}")


@tree.command(name="price", description="Fetch token price from Flare FTSOv2")
@app_commands.describe(symbol="Token symbol (e.g. XRP, BTC, ETH, FLR)")
async def price_cmd(interaction: discord.Interaction, symbol: str):
    await interaction.response.defer()
    try:
        import urllib.request, json as _json
        url = f"https://api.flare.network/price/{symbol.upper()}/USD"
        with urllib.request.urlopen(url, timeout=5) as r:
            data = _json.loads(r.read())
        price = float(data.get("price", 0))
        embed = discord.Embed(title=f"{symbol.upper()} / USD", color=0xFFAA00)
        embed.add_field(name="Price", value=f"${price:,.4f}", inline=True)
        embed.set_footer(text="Flare FTSOv2 | xrpl-hermes")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"Could not fetch price: {e}")


@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user} — slash commands synced")


def main():
    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        print("Set DISCORD_BOT_TOKEN environment variable")
        return
    client.run(token)


if __name__ == "__main__":
    main()
