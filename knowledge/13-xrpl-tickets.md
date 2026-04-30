# XRPL Tickets

## Overview

Tickets allow an account to reserve sequence numbers for out-of-order transaction execution. They solve the problem of needing to submit multiple transactions in parallel when the Sequence field normally requires strict ordering. Critical for high-throughput bots, multi-signing flows, and long-running operations.

---

## 1. The Problem Tickets Solve

Normal XRPL transactions require sequential Sequence numbers:
- Account has Sequence 100
- Submit tx with Seq 100 → succeeds → account now at Seq 101
- Must wait for Seq 100 to confirm before submitting Seq 101

With tickets:
- Reserve tickets 101–110 with one transaction
- Submit 10 transactions with different ticket numbers simultaneously
- No ordering dependency — they can all be in the same ledger

---

## 2. TicketCreate Transaction

```json
{
  "TransactionType": "TicketCreate",
  "Account": "rBOT...",
  "TicketCount": 10,
  "Fee": "12",
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

**Reserve cost**: Each ticket costs 2 XRP reserve (returned when ticket is consumed or cancelled).

---

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
  "Fee": "12"
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
  "Fee": "12"
}
```

Both of these can be submitted in the same ledger round simultaneously.

---

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

---

## 5. Python: High-Throughput Parallel Submission

```python
import asyncio
from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.models.transactions import Payment, TicketCreate
from xrpl.asyncio.transaction import autofill_and_sign, submit_and_wait
from xrpl.wallet import Wallet

async def parallel_payments(destinations: list, amounts: list):
    client = AsyncJsonRpcClient("https://xrplcluster.com")
    wallet = Wallet.from_seed("sn...")
    n = len(destinations)

    # Step 1: Create tickets
    ticket_tx = TicketCreate(
        account=wallet.address,
        ticket_count=n,
        sequence=wallet.sequence
    )
    signed = await autofill_and_sign(ticket_tx, wallet, client)
    result = await submit_and_wait(signed, client)
    assert result.result["meta"]["TransactionResult"] == "tesSUCCESS"

    # Step 2: Get tickets
    from xrpl.models.requests import AccountObjects
    resp = await client.request(AccountObjects(account=wallet.address, type="ticket"))
    ticket_seqs = sorted([t["TicketSequence"] for t in resp.result["account_objects"]])

    # Step 3: Submit all payments in parallel
    async def send_payment(dest, amount, ticket_seq):
        tx = Payment(
            account=wallet.address,
            destination=dest,
            amount=str(amount),
            sequence=0,
            ticket_sequence=ticket_seq,
            fee="12"
        )
        signed = wallet.sign(tx)
        return await submit_and_wait(signed, client)

    tasks = [
        send_payment(destinations[i], amounts[i], ticket_seqs[i])
        for i in range(n)
    ]
    results = await asyncio.gather(*tasks)
    
    for i, r in enumerate(results):
        print(f"Ticket {ticket_seqs[i]}: {r.result['meta']['TransactionResult']}")
    
    await client.close()

asyncio.run(parallel_payments(
    ["rA...", "rB...", "rC..."],
    [1000000, 2000000, 3000000]
))
```

---

## 6. JavaScript: Parallel Submission with Tickets

```javascript
const xrpl = require('xrpl');

async function parallelWithTickets(destinations, amounts) {
  const client = new xrpl.Client('wss://xrplcluster.com');
  await client.connect();

  const wallet = xrpl.Wallet.fromSeed('sn...');
  const n = destinations.length;

  // Create tickets
  const ticketTx = await client.autofill({
    TransactionType: 'TicketCreate',
    Account: wallet.address,
    TicketCount: n
  });
  const { tx_blob } = wallet.sign(ticketTx);
  await client.submitAndWait(tx_blob);

  // Get ticket sequences
  const resp = await client.request({
    command: 'account_objects',
    account: wallet.address,
    type: 'ticket'
  });
  const ticketSeqs = resp.result.account_objects
    .map(t => t.TicketSequence)
    .sort((a, b) => a - b);

  // Submit all payments in parallel
  const promises = destinations.map(async (dest, i) => {
    const tx = {
      TransactionType: 'Payment',
      Account: wallet.address,
      Destination: dest,
      Amount: String(amounts[i]),
      Sequence: 0,
      TicketSequence: ticketSeqs[i],
      Fee: '12'
    };
    const { tx_blob } = wallet.sign(tx);
    return client.submitAndWait(tx_blob);
  });

  const results = await Promise.all(promises);
  results.forEach((r, i) => {
    console.log(`Ticket ${ticketSeqs[i]}: ${r.result.meta.TransactionResult}`);
  });

  await client.disconnect();
}
```

---

## 7. Tickets for Multi-Signing Coordination

Multi-signing often takes minutes (waiting for multiple signers). Use tickets so the master account's sequence doesn't block:

```python
# Coordinator creates 5 tickets for 5 pending multi-sig proposals
# Each proposal gets its own ticket
# Signers can work on proposals in any order
# Once quorum reached, submit with that ticket's sequence

proposals = [
    {"ticket": 101, "tx": payment_tx_1, "sigs": []},
    {"ticket": 102, "tx": nft_mint_tx, "sigs": []},
    {"ticket": 103, "tx": trust_set_tx, "sigs": []},
]

# When proposal gets enough signatures, submit
async def submit_when_ready(proposal):
    while len(proposal["sigs"]) < QUORUM:
        await asyncio.sleep(5)
    
    combined = multisign(proposal["tx"], proposal["sigs"])
    return await submit_and_wait(combined, client)
```

---

## 8. Cancelling Unused Tickets

Unused tickets lock 2 XRP each. Cancel by submitting an `AccountDelete` (not usually practical) or... you cannot directly cancel. Instead submit a trivial transaction using the ticket:

```json
{
  "TransactionType": "AccountSet",
  "Account": "rBOT...",
  "Sequence": 0,
  "TicketSequence": 105,
  "Fee": "12"
}
```

This "wastes" the ticket but releases the 2 XRP reserve.

---

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

---

## 10. Ticket Limits and Reserve

| Parameter | Value |
|-----------|-------|
| Max tickets per TicketCreate | 250 |
| Max outstanding tickets per account | 250 |
| Reserve per ticket | 2 XRP |
| Ticket lifetime | Until used or account deleted |
| TicketCount upper bound cost | 250 × 2 = 500 XRP reserve |

---

## 11. Common Errors

| Error | Cause |
|-------|-------|
| `tecDIR_FULL` | Too many ledger objects (max 250 tickets) |
| `temINVALID` | TicketSequence and Sequence both set |
| `tefNO_TICKET` | Ticket doesn't exist or already used |
| `temBAD_SEQUENCE` | Sequence != 0 when using TicketSequence |
