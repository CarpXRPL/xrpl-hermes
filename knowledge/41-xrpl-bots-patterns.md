# XRPL Bot Architecture Patterns

## Design Principles

1. **Never trust a single endpoint.** Rotate between at least 3 XRPL nodes.
2. **Track sequence numbers locally.** Re-fetching AccountInfo on every tx is slow; maintain a local counter and refresh on `tefPAST_SEQ`.
3. **Use LastLedgerSequence.** Without it, transactions can stay pending forever.
4. **Prefer WebSocket for subscriptions, JSON-RPC for queries.** WS has lower latency for ledger events; JSON-RPC is simpler for one-off requests.
5. **All errors are recoverable until proven otherwise.** Classify before panicking.

---

## Core Bot Class

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


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

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## DEX Arbitrage Bot Pattern

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## AMM Bot Pattern

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


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

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


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
