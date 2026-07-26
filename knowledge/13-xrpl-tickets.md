# XRPL Tickets

## Overview

Tickets allow an account to reserve sequence numbers for out-of-order transaction execution. They solve the problem of needing to submit multiple transactions in parallel when the Sequence field normally requires strict ordering. Critical for high-throughput bots, multi-signing flows, and long-running operations.

## 1. The Problem Tickets Solve

Normal XRPL transactions require sequential Sequence numbers:
- Account has Sequence 100
- Submit tx with Seq 100 → succeeds → account now at Seq 101
- Must wait for Seq 100 to confirm before submitting Seq 101

With tickets:
- Reserve tickets 101–110 with one transaction
- Submit 10 transactions with different ticket numbers simultaneously
- No ordering dependency — they can all be in the same ledger

## 2. TicketCreate Transaction

```json
{
  "TransactionType": "TicketCreate",
  "Account": "rBOT...",
  "TicketCount": 10,
  "Fee": "<autofill>",
  "Sequence": 100
}
```

| Field | Description |
|-------|-------------|
| `TicketCount` | Number of tickets to create (1–250 per transaction) |

After this transaction succeeds:
- Account Sequence advances to 111 (100 + 1 + 10)
- 10 ticket objects are created on ledger
- Each ticket has a `TicketSequence` value: 101, 102, ... 110

**Reserve cost**: Each owned Ticket adds one live incremental owner-reserve unit until consumed or removed with the account.

## 3. Using a Ticket

A transaction using a ticket sets `Sequence: 0` and `TicketSequence` to the reserved number:

```json
{
  "TransactionType": "Payment",
  "Account": "rBOT...",
  "Destination": "rDEST1...",
  "Amount": "1000000",
  "Sequence": 0,
  "TicketSequence": 101,
  "Fee": "<autofill>"
}
```

```json
{
  "TransactionType": "Payment",
  "Account": "rBOT...",
  "Destination": "rDEST2...",
  "Amount": "2000000",
  "Sequence": 0,
  "TicketSequence": 102,
  "Fee": "<autofill>"
}
```

Both of these can be submitted in the same ledger round simultaneously.

## 4. Querying Available Tickets

```python
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountObjects

client = JsonRpcClient("https://xrplcluster.com")

resp = client.request(AccountObjects(
    account="rBOT...",
    type="ticket"
))

tickets = resp.result["account_objects"]
ticket_sequences = [t["TicketSequence"] for t in tickets]
print(f"Available tickets: {sorted(ticket_sequences)}")
```

Response ticket object:
```json
{
  "LedgerEntryType": "Ticket",
  "Account": "rBOT...",
  "TicketSequence": 101,
  "index": "AABBCC..."
}
```

## 8. Cancelling Unused Tickets

There is no `TicketCancel` transaction. To consume an unused Ticket, build a legitimate reviewed transaction that uses `Sequence: 0` and that `TicketSequence`; do not create a meaningless value-moving transaction merely to release reserve. Authorization and submission remain in the user's external signer.

```json
{
  "TransactionType": "AccountSet",
  "Account": "rBOT...",
  "Sequence": 0,
  "TicketSequence": 105,
  "Fee": "<autofill>"
}
```

After the externally authorized transaction is validated, re-read account state to confirm the Ticket is gone and reserve accounting changed as expected.

## 9. Out-of-Order Execution Use Cases

### High-Throughput NFT Minting Bot

```python
# Mint 50 NFTs in parallel
ticket_batch_size = 50

async def mint_batch(metadata_uris: list):
    # Create 50 tickets
    await create_tickets(len(metadata_uris))
    tickets = await get_tickets()
    
    # Mint all NFTs simultaneously
    tasks = [
        mint_nft(uri, ticket)
        for uri, ticket in zip(metadata_uris, tickets)
    ]
    results = await asyncio.gather(*tasks)
    return results
```

### Token Airdrop Bot

```python
# Airdrop to 100 wallets, 10 at a time
async def airdrop(recipients: list, amount: int):
    for batch_start in range(0, len(recipients), 10):
        batch = recipients[batch_start:batch_start + 10]
        await create_tickets(len(batch))
        tickets = await get_tickets()
        
        tasks = [
            send_token(recipient, amount, ticket)
            for recipient, ticket in zip(batch, tickets)
        ]
        await asyncio.gather(*tasks)
        # Wait for reserve to recover before next batch
        await asyncio.sleep(4)
```

## 10. Ticket Limits and Reserve

| Parameter | Value |
|-----------|-------|
| Max tickets per TicketCreate | 250 |
| Max outstanding tickets per account | 250 |
| Reserve per ticket | One live incremental owner-reserve unit |
| Ticket lifetime | Until used or account deleted |
| TicketCount upper bound cost | Query live increment × requested TicketCount |

## 11. Common Errors

| Error | Cause |
|-------|-------|
| `tecDIR_FULL` | Too many ledger objects (max 250 tickets) |
| `temINVALID` | TicketSequence and Sequence both set |
| `tefNO_TICKET` | Ticket doesn't exist or already used |
| `temBAD_SEQUENCE` | Sequence != 0 when using TicketSequence |

## Related Files

- `knowledge/02-xrpl-payments.md` — parallel payment submission
- `knowledge/15-xrpl-transaction-format.md` — TicketSequence vs Sequence
- `knowledge/41-xrpl-bots-patterns.md` — high-throughput bot ticket pools
