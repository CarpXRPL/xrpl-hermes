#!/usr/bin/env python3
"""
xrpl-hermes — Telegram bot with XRPL balance, tx, and sign-link commands.

Commands:
    /balance rADDRESS    — fetch XRP balance
    /tx HASH             — look up a transaction
    /pay rDEST AMOUNT    — generate Xaman sign link

Usage:
    pip install python-telegram-bot xrpl-py
    export TELEGRAM_BOT_TOKEN=...
    python3 example-telegram-bot.py
"""

import os
import json
from urllib.parse import quote

from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountInfo, Tx
from xrpl.utils import drops_to_xrp

try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, ContextTypes
except ImportError:
    print("Install: pip install python-telegram-bot")
    raise

XRPL_CLIENT = JsonRpcClient("https://xrplcluster.com")


def xaman_url(tx_json: dict) -> str:
    return "Use the xaman-payload CLI tool with this TX JSON"


async def balance(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: /balance rADDRESS")
        return
    address = ctx.args[0]
    try:
        resp = XRPL_CLIENT.request(AccountInfo(account=address, ledger_index="validated"))
        xrp = drops_to_xrp(str(resp.result["account_data"]["Balance"]))
        seq = resp.result["account_data"]["Sequence"]
        await update.message.reply_text(
            f"`{address}`\n"
            f"Balance: *{xrp:,.6f} XRP*\n"
            f"Sequence: {seq}",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def tx_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: /tx HASH")
        return
    tx_hash = ctx.args[0]
    try:
        resp = XRPL_CLIENT.request(Tx(transaction=tx_hash))
        tx = resp.result
        result_code = tx.get("meta", {}).get("TransactionResult", "?")
        tx_type = tx.get("TransactionType", "?")
        account = tx.get("Account", "?")
        ledger = tx.get("inLedger", "?")
        await update.message.reply_text(
            f"*{tx_type}*\n"
            f"Hash: `{tx_hash[:16]}...`\n"
            f"Account: `{account}`\n"
            f"Result: `{result_code}`\n"
            f"Ledger: {ledger}\n"
            f"[View on explorer](https://livenet.xrpl.org/transactions/{tx_hash})",
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def pay(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 2:
        await update.message.reply_text("Usage: /pay rDEST AMOUNT_IN_DROPS")
        return
    dest, amount = ctx.args[0], ctx.args[1]
    tx_json = {
        "TransactionType": "Payment",
        "Destination": dest,
        "Amount": amount,
    }
    url = xaman_url(tx_json)
    await update.message.reply_text(
        f"[Sign this payment in Xaman]({url})\n"
        f"Dest: `{dest}` | Amount: {int(amount)/1_000_000:.6f} XRP",
        parse_mode="Markdown",
    )


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Set TELEGRAM_BOT_TOKEN environment variable")
        return

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("tx", tx_cmd))
    app.add_handler(CommandHandler("pay", pay))

    print("Bot running. Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()
