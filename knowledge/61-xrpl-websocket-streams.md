# XRPL WebSocket streams

`subscribe` emits XRPL WebSocket events as newline-delimited JSON.

```bash
xrpl-hermes subscribe streams=ledger duration=30
xrpl-hermes subscribe streams=transactions,validations duration=120
xrpl-hermes subscribe streams=accounts accounts=rACCOUNT duration=60
xrpl-hermes subscribe streams=books books='XRP/USD:rISSUER' duration=60
```

Supported arguments:

| Argument | Meaning |
|---|---|
| `streams` | Comma-separated XRPL stream names |
| `accounts` | Comma-separated classic addresses for the accounts subscription |
| `books` | Semicolon-separated pairs in `ASSET/ASSET` form; issued assets use `CODE:rISSUER` |
| `duration` | Stop after this many seconds; `0` runs until interrupted |

## Common streams

- `ledger`: validated-ledger close events and network fee/reserve fields.
- `transactions`: validated transactions observed by the connected server.
- `validations`: validator messages.
- `manifests`: validator manifest changes.
- `peer_status`: peer-state events intended mainly for operators.

Account and book subscriptions are expressed through their dedicated request fields rather than as stream names.

## Consumer design

1. Parse one JSON object per line and tolerate unknown fields.
2. Keep socket work limited to receive, validate, and enqueue.
3. Use bounded worker queues and explicit backpressure.
4. Persist validated ledger indexes and transaction hashes for deduplication.
5. Reconnect with backoff, resubscribe, and recover missed ledger ranges before resuming alerts.
6. Monitor reconnects, queue depth, decode failures, and processing lag.

Treat local databases as caches. Re-read validated ledger state before decisions involving funds or authorization.
