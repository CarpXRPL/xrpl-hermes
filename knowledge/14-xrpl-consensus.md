# XRPL Consensus Protocol

## Overview

The XRP Ledger uses a variant of Byzantine Fault Tolerant (BFT) consensus called the **XRP Ledger Consensus Protocol (XRPLCP)**. It achieves finality in 3–5 seconds without mining, without proof-of-work, and with deterministic outcomes. Validators agree on a canonical ledger state using a series of voting rounds.

---

## 1. Core Concepts

### Validators

Validators are rippled nodes that participate in consensus. They:
- Broadcast proposed transaction sets
- Vote on which transactions to include
- Sign ledger closes with their validation keys

Validators are **not miners**: they earn no rewards. They are run by exchanges, universities, market makers, developers, Ripple, and the community.

### Unique Node List (UNL)

Each validator has a **UNL** — the set of validators whose votes it trusts. For the network to converge safely:
- UNLs must overlap significantly (≥ 60% recommended overlap)
- The "default UNL" published by Ripple is used by most nodes
- XRPL Foundation publishes an alternative UNL

```
# validators.txt excerpt
[validators]
nHBidG3pZK11zQD6kpNDoAhDmfSVRr... # Validator A
nHBvr9VoakWEjkSR7cbq3NN4cqyvB7... # Validator B
nHDH7bQJpVfDhVSqdui3Z8GPvKEBQpo... # Validator C

[validator_list_sites]
https://vl.ripple.com
https://vl.xrplf.org
```

---

## 2. Consensus Phases

### Phase 1: Open Ledger

```
[New Ledger Opens]
    │
    ▼
Transactions stream in from clients
rippled applies them to "open ledger" (tentative)
Transactions broadcast to peers
    │
    ▼ (every ~1s, network triggers close)
[Open Ledger Closes → Proposal Phase]
```

- Transactions in the open ledger are **not final** — anyone can submit
- Duplicate or conflicting transactions queued

### Phase 2: Consensus Round

```
[Proposal Phase]
Each validator proposes a transaction set
    │
    ▼
[Voting Rounds] (typically 2–5 rounds)
Validators vote on proposed sets
Each round: remove transactions with < threshold% agreement
    │
Threshold progression:
  Round 1: 50%
  Round 2: 65%
  Round N: 80%
    │
    ▼
[Consensus Achieved: ≥ 80% agree on transaction set]
```

Validators exchange:
1. Proposals (transaction set hash)
2. Validations (signed ledger hash after applying agreed set)

### Phase 3: Validation

```
[Validation Phase]
Each validator applies agreed transaction set to last closed ledger
Produces candidate closed ledger hash
Broadcasts validation message (signed hash)
    │
    ▼
[Quorum Check: ≥ 80% UNL validators signed same hash]
    │
    ▼
[Ledger Validated] — FINAL, IMMUTABLE
```

---

## 3. The 80% Threshold

For a ledger to be validated:
- ≥ 80% of validators on your UNL must have signed the same ledger hash
- This provides Byzantine fault tolerance for f = floor((n-1)/5) faulty nodes

```
n validators, quorum = ceil(0.8 × n)

n=5:  quorum=4  (tolerates 1 faulty)
n=10: quorum=8  (tolerates 2 faulty)
n=34: quorum=28 (tolerates 6 faulty)
```

---

## 4. Finality

XRPL achieves **deterministic finality** in 3–5 seconds:
- No forks: once validated, never reverted
- No probabilistic finality (unlike PoW chains)
- Every validated ledger builds on the previous canonical ledger

```
Ledger N (validated) → Ledger N+1 (open) → Ledger N+1 (consensus) → Ledger N+1 (validated)
         ↑____________________________________________↑
                      ~3-5 seconds
```

Tracking finality in code:

```python
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import Ledger

client = JsonRpcClient("https://xrplcluster.com")

# Wait for a specific transaction to be validated
def wait_for_validation(tx_hash: str, timeout_ledgers: int = 20):
    from xrpl.models.requests import Tx
    import time
    
    for _ in range(timeout_ledgers * 4):  # poll every ~1s
        resp = client.request(Tx(transaction=tx_hash))
        if resp.result.get("validated"):
            return resp.result
        time.sleep(1)
    raise TimeoutError("Transaction not validated in time")
```

---

## 5. Ledger Structure

Each validated ledger contains:
```json
{
  "ledger_index": 87654321,
  "ledger_hash": "AABBCC...",
  "parent_hash": "DDEEFF...",
  "close_time": 780000000,
  "close_time_human": "2024-09-19T12:00:00",
  "total_coins": "99988733684721300",
  "transaction_hash": "TXROOT...",
  "account_hash": "STATEROOT...",
  "close_flags": 0,
  "close_time_resolution": 10
}
```

- `total_coins`: XRP supply in drops (decreases with transaction fees burned)
- `close_time_resolution`: 10 seconds (ledger timestamps rounded to nearest 10s)
- `account_hash`: Merkle root of all ledger objects

---

## 6. Amendments

Amendments add new ledger features via consensus-based voting:

```
Amendment proposed by developer
    │
    ▼
Validators signal support via SetFlag in validations
    │
    ▼
If ≥ 80% UNL supports for 14 consecutive days → Amendment activates
    │
    ▼
Feature available on mainnet
```

### Querying Amendment Status

```python
from xrpl.models.requests import Feature

resp = client.request(Feature())
amendments = resp.result["features"]

for amendment_id, details in amendments.items():
    print(f"{details.get('name', amendment_id[:8])}: "
          f"{'ENABLED' if details['enabled'] else 'VOTING'} "
          f"({details.get('vote', 'N/A')}% support)")
```

### Key Amendments (as of 2024)

| Amendment | Description | Status |
|-----------|-------------|--------|
| XChainBridge | Cross-chain bridges | Enabled |
| AMM | Automated Market Maker | Enabled |
| NFTokenV1 | NFT support | Enabled |
| MPTokensV1 | Multi-Purpose Tokens | In voting |
| Hooks | Smart contract hooks (Xahau) | Not on mainnet |
| fixReducedOffersV2 | DEX offer fix | Enabled |

---

## 7. Fee Voting

Validators vote on the base transaction fee and reserve requirements:

```json
{
  "base_fee": 10,
  "reserve_base": 10000000,
  "reserve_increment": 2000000
}
```

Fee votes are included in validation messages. The network median determines actual values:

```python
from xrpl.models.requests import ServerInfo

resp = client.request(ServerInfo())
info = resp.result["info"]
print(f"Base fee: {info['validated_ledger']['base_fee_xrp']} XRP")
print(f"Reserve base: {info['validated_ledger']['reserve_base_xrp']} XRP")
print(f"Reserve inc: {info['validated_ledger']['reserve_inc_xrp']} XRP")
```

---

## 8. Negative UNL (nUNL)

If a validator goes offline, it can be added to the **Negative UNL** — temporarily excluded from quorum calculations to prevent the network from stalling:

- Triggered when a validator misses ≥ 67% of recent validations
- nUNL validators excluded from quorum calculation
- Restored when validator returns to activity
- Prevents minority offline nodes from blocking progress

---

## 9. Consensus Safety vs. Liveness

XRPL prioritizes **safety** (no invalid transactions) over **liveness** (always making progress):

- If < 80% agreement, the ledger does NOT close
- Transactions remain in the open ledger for next round
- Network stalls rather than forks
- This is the correct tradeoff for financial systems

---

## 10. Transaction Ordering Within a Ledger

Within a single ledger, transactions are ordered by:
1. Account (alphabetical by base58 address)
2. Sequence number within that account

This is deterministic: every node produces the same ordered set.

---

## 11. Monitoring Validator Health

```bash
# Check your validator's status
rippled server_info

# Check UNL consensus
rippled validators

# Check amendment votes
rippled feature
```

```python
from xrpl.models.requests import Validators

resp = client.request(Validators())
for v in resp.result["validators"]:
    print(f"{v['validation_public_key'][:16]}: "
          f"{'online' if v.get('validated_ledger') else 'offline'}")
```

---

## 12. Attack Resistance

| Attack | Resistance |
|--------|-----------|
| Sybil | UNL = trusted set, not open participation |
| 51% | Need ≥ 80% of UNL, not majority of nodes |
| Double spend | Deterministic finality within 3-5s |
| Censorship | ≥ 20% of UNL can block a transaction |
| Eclipse | Peer diversity + UNL independence |

---

## Related Files

- `knowledge/16-xrpl-clio.md` — Clio non-validating reporting node
- `knowledge/17-xrpl-private-node.md` — running your own validator
- `knowledge/37-xrpl-amendments.md` — amendment voting mechanics
