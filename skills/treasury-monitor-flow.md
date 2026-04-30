# Treasury Monitor Flow

Multisig treasury monitoring with alerts — track balances, pending multisig transactions, and send notifications when thresholds are breached.

## Architecture

```
Cron / long-poll loop
  ├── AccountInfo (balance, reserve)
  ├── AccountObjects (SignerList, Tickets, Escrows)
  ├── AccountTx (recent transactions)
  └── If alert condition met → send notification
```

---

## Step 1 — Configure Multisig Treasury

Set up the signer list on the treasury account:

```bash
python3 scripts/xrpl_tools.py build-signer-list-set \
  --from rTREASURY \
  --quorum 3 \
  --signers "rSIGNER1:2,rSIGNER2:2,rSIGNER3:1,rSIGNER4:1"
```

```python
from xrpl.models.transactions import SignerListSet
from xrpl.models.transactions.signer_list_set import SignerEntry

tx = SignerListSet(
    account="rTREASURY",
    signer_quorum=3,
    signer_entries=[
        SignerEntry(account="rSIGNER1", signer_weight=2),
        SignerEntry(account="rSIGNER2", signer_weight=2),
        SignerEntry(account="rSIGNER3", signer_weight=1),
        SignerEntry(account="rSIGNER4", signer_weight=1),
    ],
)
```

Verify the signer list:
```bash
python3 scripts/xrpl_tools.py account_objects rTREASURY signer_list
```

---

## Step 2 — Query Treasury State

```python
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountInfo, AccountObjects, AccountTx
from xrpl.utils import drops_to_xrp
from decimal import Decimal

client = JsonRpcClient("https://xrplcluster.com")
TREASURY = "rTREASURY"

def get_treasury_state(address: str) -> dict:
    info_resp = client.request(AccountInfo(account=address, ledger_index="validated"))
    acct = info_resp.result.get("account_data", {})

    balance_drops = int(acct.get("Balance", 0))
    sequence = acct.get("Sequence", 0)
    flags = acct.get("Flags", 0)

    obj_resp = client.request(AccountObjects(
        account=address, ledger_index="validated", limit=50
    ))
    objects = obj_resp.result.get("account_objects", [])

    signer_lists = [o for o in objects if o.get("LedgerEntryType") == "SignerList"]
    escrows = [o for o in objects if o.get("LedgerEntryType") == "Escrow"]
    tickets = [o for o in objects if o.get("LedgerEntryType") == "Ticket"]

    return {
        "balance_xrp": float(drops_to_xrp(str(balance_drops))),
        "balance_drops": balance_drops,
        "sequence": sequence,
        "signer_list": signer_lists[0] if signer_lists else None,
        "escrows": escrows,
        "tickets": tickets,
        "reserve_items": len(objects),
    }

state = get_treasury_state(TREASURY)
print(f"Balance: {state['balance_xrp']:.2f} XRP")
print(f"Signers: {len(state['signer_list'].get('SignerEntries', [])) if state['signer_list'] else 0}")
print(f"Escrows: {len(state['escrows'])}")
```

---

## Step 3 — Check Recent Transactions

```python
def get_recent_txs(address: str, limit: int = 20) -> list:
    resp = client.request(AccountTx(
        account=address, limit=limit, ledger_index_min=-1, ledger_index_max=-1
    ))
    txs = resp.result.get("transactions", [])
    return [
        {
            "hash": t["tx"].get("hash", ""),
            "type": t["tx"].get("TransactionType", ""),
            "result": t["meta"].get("TransactionResult", ""),
            "ledger": t["tx"].get("ledger_index", 0),
            "account": t["tx"].get("Account", ""),
            "amount": t["tx"].get("Amount", ""),
        }
        for t in txs
    ]

recent = get_recent_txs(TREASURY)
for tx in recent:
    print(f"{tx['ledger']}: {tx['type']} — {tx['result']}")
```

---

## Step 4 — Alert Conditions

```python
from datetime import datetime, timezone

ALERT_THRESHOLDS = {
    "balance_min_xrp": 1000,        # alert if below 1000 XRP
    "balance_max_xrp": 10_000_000,  # alert if above 10M XRP (anomaly)
    "escrow_count_max": 10,          # alert if too many open escrows
    "large_tx_xrp": 50_000,         # alert on any TX moving >50K XRP
}

def check_alerts(state: dict, recent_txs: list) -> list[str]:
    alerts = []
    bal = state["balance_xrp"]

    if bal < ALERT_THRESHOLDS["balance_min_xrp"]:
        alerts.append(f"LOW BALANCE: {bal:.2f} XRP (threshold: {ALERT_THRESHOLDS['balance_min_xrp']} XRP)")

    if bal > ALERT_THRESHOLDS["balance_max_xrp"]:
        alerts.append(f"ANOMALOUS HIGH BALANCE: {bal:.2f} XRP")

    if len(state["escrows"]) > ALERT_THRESHOLDS["escrow_count_max"]:
        alerts.append(f"TOO MANY ESCROWS: {len(state['escrows'])}")

    for tx in recent_txs:
        if tx["type"] == "Payment" and isinstance(tx["amount"], str):
            amt_xrp = int(tx["amount"]) / 1e6
            if amt_xrp > ALERT_THRESHOLDS["large_tx_xrp"]:
                alerts.append(f"LARGE TX: {amt_xrp:.0f} XRP moved in {tx['hash'][:16]}...")

    return alerts
```

---

## Step 5 — Send Notifications

**Telegram alert (see `knowledge/56-telegram-integration.md`):**

```python
import httpx

def send_telegram_alert(bot_token: str, chat_id: str, message: str):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    httpx.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"})

alerts = check_alerts(state, recent)
if alerts:
    msg = f"*Treasury Alert* — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n"
    msg += "\n".join(f"⚠️ {a}" for a in alerts)
    send_telegram_alert(BOT_TOKEN, CHAT_ID, msg)
```

**Discord alert:**

```python
import httpx

def send_discord_alert(webhook_url: str, alerts: list[str]):
    content = "**Treasury Alert**\n" + "\n".join(f"> {a}" for a in alerts)
    httpx.post(webhook_url, json={"content": content})
```

---

## Step 6 — Monitor Loop

```python
import time

POLL_INTERVAL = 60  # seconds

last_seen_tx = None

while True:
    try:
        state = get_treasury_state(TREASURY)
        recent = get_recent_txs(TREASURY, limit=5)

        # New TX detection
        if recent and recent[0]["hash"] != last_seen_tx:
            last_seen_tx = recent[0]["hash"]
            print(f"New TX: {recent[0]['type']} — {recent[0]['result']}")

        alerts = check_alerts(state, recent)
        if alerts:
            send_telegram_alert(BOT_TOKEN, CHAT_ID, "\n".join(alerts))
            print(f"Alerts sent: {alerts}")

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Balance: {state['balance_xrp']:.2f} XRP")

    except Exception as e:
        print(f"Monitor error: {e}")

    time.sleep(POLL_INTERVAL)
```

---

## Step 7 — Pre-Signing Multisig Workflow

When a treasury TX needs signing by multiple parties:

```bash
# 1. Build the base TX (any signer builds it)
python3 scripts/xrpl_tools.py build-payment \
  --from rTREASURY \
  --to rDESTINATION \
  --amount 1000000000

# 2. Each required signer signs independently (xrpl-py)
python3 -c "
from xrpl.wallet import Wallet
from xrpl.transaction import multisign, sign

tx_json = {...}  # from step 1 output
wallet1 = Wallet.from_seed('sSIGNER1_SEED')
signed1 = sign(tx_from_dict(tx_json), wallet1, multisign=True)
print(signed1.to_xrpl())  # Share with signer 2
"

# 3. Combine signatures and submit
python3 -c "
from xrpl.transaction import multisign
combined = multisign(tx_from_dict(tx_json), [signed1, signed2, signed3])
result = client.request(Submit(tx_blob=combined.to_xrpl()))
print(result.result)
"
```

---

## Common Mistakes

| Mistake | Fix |
|---|---|
| Not accounting for reserve when computing spendable balance | `spendable = balance - (base_reserve + reserve_per_item * objects)` |
| Signers sign stale sequence numbers | Always fetch fresh sequence before signing |
| Missing signers in combined TX | Must meet SignerQuorum weight threshold |
| Alerting on own outbound TX | Filter by `account != TREASURY` for inbound alerts |
| Polling too fast | 1 ledger ≈ 4 seconds — poll every 4–60s max |

---

## Reserve Calculation

```python
BASE_RESERVE_XRP = 10  # current mainnet
RESERVE_PER_ITEM_XRP = 2

def spendable_xrp(balance_xrp: float, object_count: int) -> float:
    reserve = BASE_RESERVE_XRP + (RESERVE_PER_ITEM_XRP * object_count)
    return max(0, balance_xrp - reserve)

print(f"Spendable: {spendable_xrp(state['balance_xrp'], state['reserve_items']):.2f} XRP")
```
