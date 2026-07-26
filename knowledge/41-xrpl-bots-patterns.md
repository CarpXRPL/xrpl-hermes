# XRPL bot patterns

XRPL-Hermes supplies reads, streams, and unsigned builders. A bot built around it must keep authorization policy and wallet custody outside the agent.

## Read loop

```bash
xrpl-hermes server-info
xrpl-hermes account rACCOUNT
xrpl-hermes account-tx rACCOUNT 20
xrpl-hermes amm-info XRP TOKEN:rISSUER
xrpl-hermes book-offers XRP TOKEN:rISSUER
```

Record endpoint, network, validated ledger index, fetch time, and missing fields. A failed read is an unavailable decision input, not permission to use stale fixtures silently.

## Stream loop

```bash
xrpl-hermes subscribe streams=ledger,transactions duration=120
xrpl-hermes subscribe streams=accounts accounts=rACCOUNT duration=120
xrpl-hermes subscribe streams=books books='XRP/TOKEN:rISSUER' duration=120
```

Persist checkpoints, deduplicate transaction hashes, resubscribe after reconnect, and recover missed ledgers before resuming alerts.

## Intent generation

Bots may prepare unsigned actions:

```bash
xrpl-hermes build-payment --from rSOURCE --to rDESTINATION --amount 1000000
xrpl-hermes build-offer --from rTRADER --sell XRP:1000000 --buy TOKEN:rISSUER:10
```

Before wallet handoff, enforce network, asset/issuer, amount, fee, slippage, destination, frequency, daily-loss, and expiry policy. Human or separately accepted policy-gated wallet authorization remains outside Hermes.

## Verification loop

1. Store the reviewed intent and wallet handoff ID.
2. Receive the transaction hash from the external wallet.
3. Run `tx-info HASH` until validated or expired.
4. Check engine result and delivered amount where applicable.
5. Re-read affected account, order, AMM, trust-line, or NFT state.
6. Reconcile gross amount, fees, and net effect.

XRPL-Hermes does not ship an unattended trading executor, key store, signer, broadcaster, or profit guarantee.
