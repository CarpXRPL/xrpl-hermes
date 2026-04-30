# XRPL Bot Architecture Patterns

## Design Principles

1. **Never trust a single endpoint.** Rotate between at least 3 XRPL nodes.
2. **Track sequence numbers locally.** Re-fetching AccountInfo on every tx is slow; maintain a local counter and refresh on `tefPAST_SEQ`.
3. **Use LastLedgerSequence.** Without it, transactions can stay pending forever.
4. **Prefer WebSocket for subscriptions, JSON-RPC for queries.** WS has lower latency for ledger events; JSON-RPC is simpler for one-off requests.
5. **All errors are recoverable until proven otherwise.** Classify before panicking.

---

## Core Bot Class

```python
import xrpl, time, logging, os
from xrpl.clients import JsonRpcClient, WebsocketClient
from xrpl.models.requests import AccountInfo, Tx, ServerInfo
from xrpl.models.response import ResponseStatus
from xrpl.wallet import Wallet

logger = logging.getLogger("xrpl-bot")

ENDPOINTS = [
    "https://xrplcluster.com",
    "https://s1.ripple.com:51234",
    "https://s2.ripple.com:51234",
]


class XRPLBot:
    def __init__(self, secret: str, endpoints: list[str] = ENDPOINTS):
        self.wallet = Wallet.from_secret(secret)
        self.clients = [JsonRpcClient(e) for e in endpoints]
        self._idx = 0
        self._sequence: int | None = None
        self._last_ledger: int = 0

    @property
    def client(self) -> JsonRpcClient:
        return self.clients[self._idx]

    def rotate(self):
        self._idx = (self._idx + 1) % len(self.clients)
        logger.info(f"Rotated to endpoint {self._idx}: {ENDPOINTS[self._idx]}")

    def sequence(self) -> int:
        """Get current sequence number, fetching from chain if not cached."""
        if self._sequence is None:
            self._sequence = self._fetch_sequence()
        return self._sequence

    def _fetch_sequence(self) -> int:
        resp = self.client.request(AccountInfo(
            account=self.wallet.classic_address,
            ledger_index="current",
        ))
        return resp.result["account_data"]["Sequence"]

    def bump_sequence(self):
        self._sequence = (self._sequence or 0) + 1

    def reset_sequence(self):
        self._sequence = None  # Force re-fetch on next use

    def last_ledger_sequence(self, buffer: int = 20) -> int:
        """Safe LastLedgerSequence = current validated + buffer ledgers."""
        resp = self.client.request(ServerInfo())
        self._last_ledger = resp.result["info"]["validated_ledger"]["seq"]
        return self._last_ledger + buffer

    def submit(self, tx) -> tuple[bool, dict]:
        """
        Submit a transaction, poll for validation, handle common errors.
        Returns (success: bool, result: dict).
        """
        # Auto-fill sequence if not set
        if not hasattr(tx, 'sequence') or tx.sequence is None:
            tx = tx.to_dict()
            tx['Sequence'] = self.sequence()
            tx['LastLedgerSequence'] = self.last_ledger_sequence()
            from xrpl.models.transactions import Transaction
            tx = Transaction.from_dict(tx)

        for attempt in range(3):
            try:
                resp = self.client.submit(tx, self.wallet)
                prelim = resp.result.get("engine_result", "")

                if prelim == "tesSUCCESS" or prelim.startswith("ter") or prelim.startswith("tec"):
                    # Tx entered the queue — poll for validation
                    tx_hash = resp.result["tx_json"]["hash"]
                    self.bump_sequence()
                    return self._poll_validation(tx_hash)

                elif prelim == "tefPAST_SEQ":
                    self.reset_sequence()
                    time.sleep(1)
                    continue

                elif prelim == "tefMAX_LEDGER":
                    logger.warning("LastLedgerSequence expired, resubmit with new window")
                    return False, {"error": prelim}

                elif prelim == "telCAN_NOT_QUEUE":
                    time.sleep(2 ** attempt)
                    self.rotate()
                    continue

                elif prelim == "tooBusy":
                    self.rotate()
                    time.sleep(1)
                    continue

                else:
                    logger.error(f"Submit failed: {prelim}")
                    return False, resp.result

            except Exception as e:
                logger.warning(f"Submit exception (attempt {attempt+1}): {e}")
                self.rotate()
                time.sleep(2 ** attempt)

        return False, {"error": "Max retries exceeded"}

    def _poll_validation(self, tx_hash: str, max_wait: int = 30) -> tuple[bool, dict]:
        """Poll until tx is validated or timeout."""
        for _ in range(max_wait):
            time.sleep(1)
            try:
                resp = self.client.request(Tx(transaction=tx_hash))
                if resp.status == ResponseStatus.SUCCESS and resp.result.get("validated"):
                    result = resp.result["meta"]["TransactionResult"]
                    return result == "tesSUCCESS", resp.result
            except Exception as e:
                logger.debug(f"Poll error: {e}")
                self.rotate()

        return False, {"error": f"Timeout waiting for {tx_hash}"}
```

---

## WebSocket Account Monitor

```python
import asyncio, json, websockets, logging

logger = logging.getLogger("ws-monitor")

WS_ENDPOINTS = [
    "wss://xrplcluster.com",
    "wss://s1.ripple.com:51233",
    "wss://s2.ripple.com:51233",
]


async def subscribe_account(
    address: str,
    on_tx: callable,
    endpoint_idx: int = 0,
):
    """Subscribe to account transactions with auto-reconnect."""
    endpoints = WS_ENDPOINTS
    idx = endpoint_idx
    backoff = 1

    while True:
        url = endpoints[idx % len(endpoints)]
        try:
            async with websockets.connect(
                url,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=5,
            ) as ws:
                # Subscribe to account
                await ws.send(json.dumps({
                    "command": "subscribe",
                    "accounts": [address],
                    "streams": ["ledger"],  # Also track ledger closes
                }))
                resp = json.loads(await ws.recv())
                if resp.get("status") != "success":
                    raise ConnectionError(f"Subscribe failed: {resp}")

                logger.info(f"Subscribed to {address} on {url}")
                backoff = 1  # Reset on success

                async for raw in ws:
                    msg = json.loads(raw)
                    msg_type = msg.get("type")

                    if msg_type == "transaction":
                        tx = msg["transaction"]
                        meta = msg.get("meta", {})
                        validated = msg.get("validated", False)
                        if validated:
                            await on_tx(tx, meta)

                    elif msg_type == "ledgerClosed":
                        logger.debug(f"Ledger closed: {msg['ledger_index']}")

        except (websockets.WebSocketException, OSError, ConnectionError) as e:
            wait = min(backoff, 60)
            logger.warning(f"WS disconnected ({url}): {e} — retry in {wait}s")
            idx += 1
            backoff = min(backoff * 2, 60)
            await asyncio.sleep(wait)


# Usage example
async def my_tx_handler(tx: dict, meta: dict):
    tx_type = tx.get("TransactionType")
    result = meta.get("TransactionResult")
    logger.info(f"Received {tx_type}: {result}")

    if tx_type == "Payment" and result == "tesSUCCESS":
        amount = tx.get("Amount")
        if isinstance(amount, str):
            xrp = int(amount) / 1e6
            logger.info(f"Payment: {xrp:.6f} XRP")


asyncio.run(subscribe_account("rMyAddress...", my_tx_handler))
```

---

## Multi-Account Fleet Management

```python
from dataclasses import dataclass, field
from threading import Lock
import queue

@dataclass
class ManagedWallet:
    wallet: Wallet
    label: str
    sequence: int = 0
    in_flight: int = 0
    lock: Lock = field(default_factory=Lock)


class WalletFleet:
    def __init__(self, secrets: dict[str, str]):
        """secrets: {label: secret}"""
        self.wallets: dict[str, ManagedWallet] = {}
        for label, secret in secrets.items():
            w = Wallet.from_secret(secret)
            self.wallets[label] = ManagedWallet(wallet=w, label=label)

    def refresh_all(self, client: JsonRpcClient):
        for label, mw in self.wallets.items():
            try:
                acc = client.request(AccountInfo(
                    account=mw.wallet.classic_address,
                    ledger_index="current",
                ))
                with mw.lock:
                    mw.sequence = acc.result["account_data"]["Sequence"]
                logger.info(f"Refreshed {label}: seq={mw.sequence}")
            except Exception as e:
                logger.error(f"Failed to refresh {label}: {e}")

    def acquire_sequence(self, label: str) -> int:
        mw = self.wallets[label]
        with mw.lock:
            seq = mw.sequence
            mw.sequence += 1
            mw.in_flight += 1
        return seq

    def release(self, label: str):
        with self.wallets[label].lock:
            self.wallets[label].in_flight -= 1

    def get_wallet(self, label: str) -> Wallet:
        return self.wallets[label].wallet
```

---

## DEX Arbitrage Bot Pattern

```python
from xrpl.models.transactions import OfferCreate, OfferCancel
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.requests import BookOffers

class ArbBot(XRPLBot):
    def __init__(self, secret: str, base_currency: str, base_issuer: str):
        super().__init__(secret)
        self.base_currency = base_currency
        self.base_issuer = base_issuer

    def get_best_offers(self, taker_pays, taker_gets, limit=5) -> list[dict]:
        """Get top N offers from DEX orderbook."""
        resp = self.client.request(BookOffers(
            taker_pays=taker_pays,
            taker_gets=taker_gets,
            limit=limit,
            ledger_index="validated",
        ))
        return resp.result.get("offers", [])

    def calculate_spread(self) -> dict:
        """Check bid/ask spread for XRP/TOKEN pair."""
        token_spec = {"currency": self.base_currency, "issuer": self.base_issuer}
        xrp_spec = {"currency": "XRP"}

        # Buy side: offers selling TOKEN for XRP (we BUY token with XRP)
        buy_book = self.get_best_offers(
            taker_pays=token_spec,
            taker_gets=xrp_spec,
        )

        # Sell side: offers selling XRP for TOKEN (we SELL token for XRP)
        sell_book = self.get_best_offers(
            taker_pays=xrp_spec,
            taker_gets=token_spec,
        )

        if not buy_book or not sell_book:
            return {"spread": None, "arb": False}

        best_ask = buy_book[0]   # Cheapest price to buy token
        best_bid = sell_book[0]  # Highest price to sell token

        # Compute prices (XRP per token unit)
        ask_xrp = int(best_ask["TakerGets"]) / 1e6
        ask_token = float(best_ask["TakerPays"]["value"])
        ask_price = ask_xrp / ask_token  # XRP per token

        bid_xrp = int(best_bid["TakerPays"]) / 1e6
        bid_token = float(best_bid["TakerGets"]["value"])
        bid_price = bid_xrp / bid_token

        spread = (ask_price - bid_price) / ask_price
        return {
            "ask_price": ask_price,
            "bid_price": bid_price,
            "spread_pct": spread * 100,
            "arb": spread > 0.005,  # 0.5% min spread (accounting for fees)
        }

    def place_arb_offers(self, xrp_amount_drops: int):
        """Execute atomic arbitrage via crossed offer pair."""
        spread = self.calculate_spread()
        if not spread["arb"]:
            return

        ask = spread["ask_price"]
        token_amount = (xrp_amount_drops / 1e6) / ask

        # Buy at ask: give XRP, get token
        buy_tx = OfferCreate(
            account=self.wallet.classic_address,
            taker_pays=IssuedCurrencyAmount(
                currency=self.base_currency,
                issuer=self.base_issuer,
                value=str(round(token_amount, 6)),
            ),
            taker_gets=str(xrp_amount_drops),
            flags=0x00080000,  # tfImmediateOrCancel — only fill at current price
        )
        success, result = self.submit(buy_tx)
        if success:
            profit_check = result.get("meta", {})
            logger.info(f"Arb buy executed. Spread was {spread['spread_pct']:.2f}%")
```

---

## AMM Bot Pattern

```python
from xrpl.models.transactions import AMMDeposit, AMMWithdraw
from xrpl.models.requests import AMMInfo

class AMMBot(XRPLBot):
    def __init__(self, secret: str, asset1: dict, asset2: dict):
        super().__init__(secret)
        self.asset1 = asset1  # e.g. {"currency": "XRP"}
        self.asset2 = asset2  # e.g. {"currency": "USD", "issuer": "rBitstamp..."}

    def get_pool_state(self) -> dict:
        resp = self.client.request(AMMInfo(asset=self.asset1, asset2=self.asset2))
        amm = resp.result.get("amm", {})
        xrp_amt = int(amm.get("amount", "0")) / 1e6
        token_amt = float(amm.get("amount2", {}).get("value", "0"))
        lp_supply = float(amm.get("lp_token", {}).get("value", "0"))
        fee = amm.get("trading_fee", 0)
        return {
            "xrp": xrp_amt,
            "token": token_amt,
            "price": xrp_amt / token_amt if token_amt else 0,
            "lp_supply": lp_supply,
            "fee_bps": fee,
        }

    def rebalance_deposit(self, xrp_amount_drops: int):
        """Deposit proportional liquidity to maintain pool ratio."""
        pool = self.get_pool_state()
        token_ratio = pool["token"] / pool["xrp"] if pool["xrp"] else 1
        xrp_in = xrp_amount_drops / 1e6
        token_in = xrp_in * token_ratio

        deposit = AMMDeposit(
            account=self.wallet.classic_address,
            asset=self.asset1,
            asset2=self.asset2,
            amount=str(xrp_amount_drops),
            amount2=IssuedCurrencyAmount(
                currency=self.asset2["currency"],
                issuer=self.asset2["issuer"],
                value=str(round(token_in, 6)),
            ),
            flags=0x00100000,  # tfTwoAsset
        )
        return self.submit(deposit)

    def withdraw_all(self, lp_token_value: str, lp_issuer: str):
        """Withdraw all liquidity and burn LP tokens."""
        withdraw = AMMWithdraw(
            account=self.wallet.classic_address,
            asset=self.asset1,
            asset2=self.asset2,
            lp_token_in=IssuedCurrencyAmount(
                currency="03930D02208264E2E40EC1B0C09E4DB96EE197B1",
                issuer=lp_issuer,
                value=lp_token_value,
            ),
            flags=0x00010000,  # tfLPToken
        )
        return self.submit(withdraw)
```

---

## Sequence Drift Recovery

```python
def detect_and_fix_sequence_drift(bot: XRPLBot) -> bool:
    """
    Detect if local sequence is ahead of chain (common after failed batch ops).
    Returns True if drift was detected and fixed.
    """
    local_seq = bot._sequence
    chain_seq = bot._fetch_sequence()

    if local_seq is None:
        bot._sequence = chain_seq
        return False

    drift = local_seq - chain_seq
    if drift > 0:
        logger.warning(f"Sequence drift detected: local={local_seq}, chain={chain_seq}, drift={drift}")
        # Wait for in-flight transactions to settle
        time.sleep(drift * 4)  # Worst case: 4s per ledger per tx
        bot._sequence = bot._fetch_sequence()
        logger.info(f"Sequence reset to {bot._sequence}")
        return True

    return False
```

---

## Offer Book Snapshot

```python
def snapshot_order_book(
    client: JsonRpcClient,
    taker_pays: dict,
    taker_gets: dict,
    depth: int = 20,
) -> list[dict]:
    """Fetch full order book up to `depth` levels."""
    all_offers = []
    marker = None

    while len(all_offers) < depth:
        req = BookOffers(
            taker_pays=taker_pays,
            taker_gets=taker_gets,
            limit=min(100, depth - len(all_offers)),
            ledger_index="validated",
        )
        if marker:
            req.marker = marker

        resp = client.request(req)
        offers = resp.result.get("offers", [])
        all_offers.extend(offers)

        marker = resp.result.get("marker")
        if not marker or not offers:
            break

    return all_offers[:depth]
```

---

## Reconnect Loop (Production-Grade)

```python
import signal, sys

class GracefulShutdown:
    def __init__(self):
        self.shutdown = False
        signal.signal(signal.SIGTERM, self._handler)
        signal.signal(signal.SIGINT, self._handler)

    def _handler(self, signum, frame):
        logger.info("Shutdown signal received")
        self.shutdown = True


async def main_loop():
    shutdown = GracefulShutdown()
    bot = ArbBot(os.environ["BOT_SECRET"], "USD", "rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B")

    while not shutdown.shutdown:
        try:
            spread = bot.calculate_spread()
            logger.debug(f"Spread: {spread.get('spread_pct', 0):.2f}%")

            if spread["arb"]:
                bot.place_arb_offers(xrp_amount_drops=int(5e6))  # 5 XRP

            # Sleep until next ledger close (~4s)
            await asyncio.sleep(4)

        except Exception as e:
            logger.error(f"Main loop error: {e}", exc_info=True)
            await asyncio.sleep(10)

    logger.info("Bot shut down cleanly")


asyncio.run(main_loop())
```

---

## Common Error Handling Matrix

| Error Code | Cause | Action |
|-----------|-------|--------|
| `tesSUCCESS` | Validated success | Record and continue |
| `tefPAST_SEQ` | Sequence too low | Reset sequence, retry |
| `tefMAX_LEDGER` | LastLedgerSeq expired | Resubmit with new window |
| `telCAN_NOT_QUEUE` | Queue full | Back off, rotate endpoint |
| `tooBusy` | Node overloaded | Rotate endpoint immediately |
| `tecUNFUNDED_PAYMENT` | Wallet too low | Alert: fund wallet |
| `tecPATH_DRY` | No DEX path | Skip this trade |
| `tecOFFER_NOT_FOUND` | Race condition | Normal; don't retry |
| `tefBAD_AUTH` | Wrong signing key | Alert: check key config |
| `terNO_ACCOUNT` | Account doesn't exist | Check address |
| `tecINSUFF_RESERVE_LINE` | Reserve too low to create trust line | Fund wallet more |

---

## Related Files
- `knowledge/18-xrpl-rate-limits.md` — rate limit handling
- `knowledge/40-xrpl-monitoring.md` — alerts and monitoring
- `knowledge/34-xrpl-amm-bots.md` — AMM-specific bot patterns
- `knowledge/42-xrpl-treasury.md` — multi-wallet treasury management
