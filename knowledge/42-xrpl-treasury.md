# Treasury Management Patterns on XRPL

## Wallet Hierarchy Architecture

A well-designed treasury uses defense-in-depth: the cold wallet never touches the internet, the hot wallet has limited authority, and all large operations require multi-signature.

```
COLD WALLET (Air-gapped hardware)
  ├── Master key: 3-of-5 hardware security keys (Ledger Nano / YubiKey)
  ├── Flags: RequireDestTag=ON, DefaultRipple=OFF, DisallowXRP=OFF
  ├── Balance: Minimum XRP (just enough for reserve)
  └── Signs: Key rotation, SignerList changes, emergency recovery
  
  └── TREASURY WALLET (Semi-Hot, Multi-Sig)
       ├── RegularKey → rotated weekly
       ├── SignerList: 2-of-3 for amounts > 10K XRP
       ├── Flags: DepositPreAuth=ON (whitelist outflows)
       └── Disburses to:
            ├── HOT WALLET → daily operations (<1K XRP limit)
            ├── LIQUIDITY WALLET → DEX/AMM ops (<50K XRP)
            └── RESERVE WALLET → 90-day lock via Escrow
```

---

## Account Setup: Security Flags

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## Multi-Signature Setup

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


### Submitting a Multi-Sig Transaction

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## Regular Key Management

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


### Rotation Schedule Enforcer

```python
import time, json
from pathlib import Path

KEY_ROTATION_INTERVAL = 7 * 24 * 3600  # 1 week

def check_key_rotation_needed(state_file: str = "key_state.json") -> bool:
    try:
        state = json.loads(Path(state_file).read_text())
        last_rotation = state.get("last_rotation", 0)
        return time.time() - last_rotation > KEY_ROTATION_INTERVAL
    except FileNotFoundError:
        return True

def record_rotation(state_file: str = "key_state.json"):
    Path(state_file).write_text(json.dumps({
        "last_rotation": time.time(),
        "rotated_at_ledger": client.request(xrpl.models.requests.ServerInfo()).result["info"]["validated_ledger"]["seq"],
    }))
```

---

## Escrow Vault (Time-Locked Reserves)

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## Payment Channels for High-Frequency Disbursements

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## Spending Limit Enforcement

```python
import sqlite3, time
from contextlib import contextmanager

class SpendingLimiter:
    LIMITS = {
        "hot":        {"daily_xrp": 5_000,   "single_xrp": 1_000},
        "liquidity":  {"daily_xrp": 50_000,  "single_xrp": 10_000},
        "treasury":   {"daily_xrp": 500_000, "single_xrp": 100_000},
    }

    def __init__(self, db_path: str = "treasury.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS spend_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wallet_label TEXT,
                amount_xrp REAL,
                tx_hash TEXT,
                timestamp REAL DEFAULT (unixepoch())
            )
        """)
        self.conn.commit()

    def daily_spend(self, label: str) -> float:
        cutoff = time.time() - 86400
        row = self.conn.execute(
            "SELECT COALESCE(SUM(amount_xrp), 0) FROM spend_log WHERE wallet_label=? AND timestamp > ?",
            (label, cutoff)
        ).fetchone()
        return row[0]

    def can_spend(self, label: str, amount_xrp: float) -> tuple[bool, str]:
        limits = self.LIMITS.get(label, {})
        if not limits:
            return False, f"Unknown wallet label: {label}"

        single_limit = limits["single_xrp"]
        daily_limit = limits["daily_xrp"]

        if amount_xrp > single_limit:
            return False, f"Exceeds single-tx limit ({single_limit} XRP)"

        daily = self.daily_spend(label)
        if daily + amount_xrp > daily_limit:
            return False, f"Exceeds daily limit: {daily:.2f}/{daily_limit} XRP spent"

        return True, "OK"

    def record_spend(self, label: str, amount_xrp: float, tx_hash: str):
        self.conn.execute(
            "INSERT INTO spend_log (wallet_label, amount_xrp, tx_hash) VALUES (?, ?, ?)",
            (label, amount_xrp, tx_hash)
        )
        self.conn.commit()


# Usage
limiter = SpendingLimiter()
ok, reason = limiter.can_spend("hot", 500)
if not ok:
    raise PermissionError(f"Spend rejected: {reason}")
# ... submit tx ...
limiter.record_spend("hot", 500, tx_hash)
```

---

## DCA (Dollar-Cost Averaging) Pattern

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## DepositPreAuth (Whitelist Incoming Payments)

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## Treasury Health Report

```python
from decimal import Decimal
from xrpl.models.requests import AccountInfo, AccountLines, AccountOffers, EscrowObjects, ServerInfo

def get_validated_reserve_settings(client) -> tuple[Decimal, Decimal]:
    response = client.request(ServerInfo())
    ledger = response.result.get("info", {}).get("validated_ledger", {})
    try:
        return Decimal(str(ledger["reserve_base_xrp"])), Decimal(str(ledger["reserve_inc_xrp"]))
    except KeyError as exc:
        raise RuntimeError("validated ledger did not return reserve settings") from exc

def treasury_report(client, wallets: dict[str, str]) -> dict:
    """
    wallets: {label: address}
    Returns full balance + open positions report.
    """
    report = {}

    for label, address in wallets.items():
        wallet_data = {}

        # XRP balance
        acc = client.request(AccountInfo(account=address, ledger_index="validated"))
        drops = int(acc.result["account_data"]["Balance"])
        reserve_base, reserve_inc = get_validated_reserve_settings(client)
        reserve = reserve_base + int(acc.result["account_data"].get("OwnerCount", 0)) * reserve_inc
        balance_xrp = Decimal(drops) / Decimal(1_000_000)
        wallet_data["xrp_balance"] = str(balance_xrp)
        wallet_data["xrp_available"] = str(balance_xrp - reserve)

        # Token balances
        lines = client.request(AccountLines(account=address, ledger_index="validated"))
        wallet_data["tokens"] = {
            f"{l['currency']}@{l['account'][:8]}": float(l["balance"])
            for l in lines.result.get("lines", [])
        }

        # Open DEX offers
        offers = client.request(AccountOffers(account=address))
        wallet_data["open_offers"] = len(offers.result.get("offers", []))

        report[label] = wallet_data

    return report
```

---

## Related Files
- `knowledge/09-xrpl-escrow.md` — escrow mechanics in depth
- `knowledge/11-xrpl-payment-channels.md` — payment channel guide
- `knowledge/12-xrpl-multisig.md` — multi-signature setup
- `knowledge/25-xrpl-audit-security.md` — security best practices
- `knowledge/41-xrpl-bots-patterns.md` — bot patterns used with treasury wallets
