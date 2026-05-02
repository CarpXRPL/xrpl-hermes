# XRPL Transaction Format

## Overview

All XRPL transactions share a set of common fields and have type-specific fields. Understanding the full format is critical for correct transaction construction, fee estimation, and error handling.

---

## 1. Common Fields (All Transaction Types)

```json
{
  "TransactionType": "Payment",
  "Account": "rN7n3473SaZBCG4dFL83w7PB5MBhpqAzn",
  "Fee": "12",
  "Sequence": 42,
  "LastLedgerSequence": 87654350,
  "AccountTxnID": "OPTIONAL_PREV_TX_HASH",
  "Flags": 0,
  "Memos": [
    {
      "Memo": {
        "MemoData": "48656C6C6F",
        "MemoType": "746578742F706C61696E",
        "MemoFormat": ""
      }
    }
  ],
  "NetworkID": 0,
  "SigningPubKey": "ED...",
  "TxnSignature": "3045...",
  "TicketSequence": null
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `TransactionType` | string | Yes | Type name (see below) |
| `Account` | string | Yes | Sender's XRPL address |
| `Fee` | string | Yes | Transaction fee in drops |
| `Sequence` | number | Yes | Account sequence number (0 if using TicketSequence) |
| `LastLedgerSequence` | number | Recommended | TX invalid after this ledger index |
| `Flags` | number | No | Bitfield of flags |
| `Memos` | array | No | Arbitrary data attached to TX |
| `SigningPubKey` | string | Yes | Public key of signer (hex) |
| `TxnSignature` | string | Yes | Signature (hex) |
| `TicketSequence` | number | No | Use instead of Sequence for tickets |
| `AccountTxnID` | string | No | Hash of last tx from this account (for sequencing) |
| `NetworkID` | number | No | Chain ID for sidechains |

---

## 2. Fee

The fee is always in **drops** (1 XRP = 1,000,000 drops).

```python
# Minimum fee: 10 drops for most transactions
# Reference fee from server:
from xrpl.models.requests import ServerInfo
resp = client.request(ServerInfo())
base_fee = resp.result["info"]["validated_ledger"]["base_fee_xrp"]
base_fee_drops = int(float(base_fee) * 1_000_000)  # typically 10

# Escalated fee during high load:
# fee = reference_fee × (fee_level / 256)
# fee_level spikes when transaction queue fills
```

Fee escalation formula:
```
fee = base_fee_level × reference_fee / 256
```

For multi-signed transactions:
```
fee = base_fee × (N_signers + 1)
```

---

## 3. Sequence

- Must equal the account's current Sequence field on ledger
- Increments by 1 for each submitted transaction (even failed)
- To use a ticket instead: `"Sequence": 0` + `"TicketSequence": N`

```python
from xrpl.models.requests import AccountInfo

resp = client.request(AccountInfo(account="rN7n..."))
sequence = resp.result["account_data"]["Sequence"]
```

---

## 4. LastLedgerSequence

Critical for preventing stuck transactions:

```python
def get_last_ledger_sequence(client, buffer=20):
    resp = client.request(ServerInfo())
    current = resp.result["info"]["validated_ledger"]["seq"]
    return current + buffer  # tx invalid after this ledger
```

If not set and the network is congested, your transaction may sit in the queue indefinitely. Always set this.

---

## 5. Memos

Memos store arbitrary data on-chain:

```python
import binascii

def encode_memo(text: str) -> dict:
    return {
        "Memo": {
            "MemoData": binascii.hexlify(text.encode()).decode().upper(),
            "MemoType": binascii.hexlify(b"text/plain").decode().upper(),
        }
    }

# Usage in transaction:
tx = Payment(
    ...
    memos=[encode_memo("Invoice #12345")]
)
```

Limits:
- No hard limit on number of memos, but each byte costs extra fee
- MemoData, MemoType, MemoFormat must each be ≤ 1 KB recommended
- All memo fields are hex-encoded

---

## 6. Flags

Flags control transaction behavior. Each transaction type has its own flags:

### Payment Flags

| Flag | Value | Description |
|------|-------|-------------|
| `tfNoRippleDirect` | 0x00010000 | Don't use the default path |
| `tfPartialPayment` | 0x00020000 | Allow partial payment |
| `tfLimitQuality` | 0x00040000 | Reject if quality below minimum |

### OfferCreate Flags

| Flag | Value | Description |
|------|-------|-------------|
| `tfPassive` | 0x00010000 | Don't consume crossing offers |
| `tfImmediateOrCancel` | 0x00020000 | Cancel if can't fill immediately |
| `tfFillOrKill` | 0x00040000 | Cancel if can't fill completely |
| `tfSell` | 0x00080000 | Sell exact amount |

### TrustSet Flags

| Flag | Value | Description |
|------|-------|-------------|
| `tfSetfAuth` | 0x00010000 | Authorize trust line |
| `tfSetNoRipple` | 0x00020000 | Set no-ripple flag |
| `tfClearNoRipple` | 0x00040000 | Clear no-ripple flag |
| `tfSetFreeze` | 0x00100000 | Freeze trust line |
| `tfClearFreeze` | 0x00200000 | Unfreeze trust line |

### AccountSet Flags (SetFlag/ClearFlag)

| asfFlag | Value | Description |
|---------|-------|-------------|
| `asfRequireDest` | 1 | Require destination tag |
| `asfRequireAuth` | 2 | Require trust line authorization |
| `asfDisallowXRP` | 3 | Disallow XRP payments |
| `asfDisableMaster` | 4 | Disable master key |
| `asfAccountTxnID` | 5 | Track last tx hash |
| `asfNoFreeze` | 6 | Permanently disable freezing |
| `asfGlobalFreeze` | 7 | Freeze all trust lines |
| `asfDefaultRipple` | 8 | Enable rippling on trust lines |
| `asfDepositAuth` | 9 | Only accept pre-authorized deposits |

---

## 7. Transaction Types Reference

| Type | Description |
|------|-------------|
| `Payment` | Send XRP or tokens |
| `OfferCreate` | Place DEX order |
| `OfferCancel` | Cancel DEX order |
| `TrustSet` | Set/modify trust line |
| `AccountSet` | Modify account settings |
| `AccountDelete` | Delete account |
| `SetRegularKey` | Set regular signing key |
| `SignerListSet` | Configure multi-signing |
| `EscrowCreate` | Create time/condition escrow |
| `EscrowFinish` | Release escrow |
| `EscrowCancel` | Cancel expired escrow |
| `PaymentChannelCreate` | Open payment channel |
| `PaymentChannelFund` | Add funds to channel |
| `PaymentChannelClaim` | Redeem channel claim |
| `TicketCreate` | Reserve sequence numbers |
| `NFTokenMint` | Mint NFT |
| `NFTokenBurn` | Burn NFT |
| `NFTokenCreateOffer` | Create NFT sell/buy offer |
| `NFTokenAcceptOffer` | Accept NFT offer |
| `NFTokenCancelOffer` | Cancel NFT offer |
| `AMMCreate` | Create AMM pool |
| `AMMDeposit` | Add liquidity to AMM |
| `AMMWithdraw` | Remove liquidity from AMM |
| `AMMVote` | Vote on AMM trading fee |
| `AMMBid` | Bid on AMM auction slot |
| `AMMDelete` | Delete empty AMM |
| `Clawback` | Claw back issued tokens |
| `DepositPreauth` | Pre-authorize deposit |

---

## 8. Result Codes

### Success

| Code | Meaning |
|------|---------|
| `tesSUCCESS` | Transaction applied successfully |

### tec (Transaction Engine Cost — fee charged, transaction failed)

| Code | Meaning |
|------|---------|
| `tecNO_DST` | Destination account doesn't exist |
| `tecNO_DST_INSUF_XRP` | Destination would need XRP (unfunded) |
| `tecNO_LINE_INSUF_RESERVE` | Not enough XRP to create trust line |
| `tecPATH_DRY` | Path dried up (no liquidity) |
| `tecPATH_PARTIAL` | Partial payment not allowed |
| `tecNO_AUTH` | Trust line not authorized |
| `tecFROZEN` | Trust line or AMM pool frozen |
| `tecUNFUNDED` | Insufficient balance |
| `tecINSUF_RESERVE_LINE` | Reserve too low for trust line |
| `tecINSUF_RESERVE_OFFER` | Reserve too low for offer |
| `tecINSUFF_FEE` | Fee not enough for escalated network |
| `tecOBJECT_NOT_FOUND` | Referenced object doesn't exist |
| `tecAMM_UNFUNDED` | AMM deposit would leave pool dry |
| `tecNO_PERMISSION` | Account not authorized |
| `tecDIR_FULL` | Too many objects on account |
| `tecEXPIRED` | Transaction or object expired |
| `tecDUPLICATE` | Object already exists |
| `tecKILLED` | FillOrKill offer couldn't fill |

### tef (Transaction Engine Failure — fee NOT charged)

| Code | Meaning |
|------|---------|
| `tefALREADY` | Same transaction already applied |
| `tefBAD_AUTH` | Master key required |
| `tefBAD_QUORUM` | Multisig doesn't meet quorum |
| `tefBAD_SIGNATURE` | Signature invalid |
| `tefMASTER_DISABLED` | Master key is disabled |
| `tefNOT_MULTI_SIGNING` | Expected multisig format |
| `tefPAST_SEQ` | Sequence already used |
| `tefNO_TICKET` | Ticket doesn't exist |

### tem (Transaction Engine Malformed — fee NOT charged)

| Code | Meaning |
|------|---------|
| `temBAD_AMOUNT` | Invalid amount |
| `temBAD_FEE` | Fee too low or malformed |
| `temBAD_SEQUENCE` | Sequence not valid |
| `temINVALID` | Transaction structure invalid |
| `temINVALID_FLAG` | Unrecognized flag |
| `temBAD_PATH` | Payment path invalid |
| `temBAD_SIGNATURE` | Signature format invalid |
| `temUNCERTAIN` | Not deterministic (rare) |
| `temUNKNOWN` | Unknown transaction type |

### tel (Transaction Engine Local — node-local, not propagated)

| Code | Meaning |
|------|---------|
| `telINSUF_FEE_P` | Fee below current minimum |
| `telCAN_NOT_QUEUE` | TX queue full |
| `telLOCAL_ERROR` | Node-local error |

### ter (Transaction Engine Retry — should retry)

| Code | Meaning |
|------|---------|
| `terINSUF_FEE_B` | Account balance can't pay fee |
| `terNO_ACCOUNT` | Source account not found |
| `terNO_RIPPLE` | Path blocked by no-ripple |
| `terPRE_SEQ` | Sequence too high (future) |
| `terQUEUED` | Held for future ledger |

---

## 9. Transaction Signing

```python
from xrpl.wallet import Wallet
from xrpl.models.transactions import Payment
from xrpl.transaction import sign, autofill

client = JsonRpcClient("https://xrplcluster.com")
wallet = Wallet.from_seed("sn...")

tx = Payment(
    account=wallet.address,
    destination="rDEST...",
    amount="1000000"
)

# Autofill fills Sequence, Fee, LastLedgerSequence
tx_autofilled = autofill(tx, client)
tx_signed = sign(tx_autofilled, wallet)

print(tx_signed.to_xrpl())  # JSON ready to submit
```

---

## 10. Inspecting a Submitted Transaction

```python
from xrpl.models.requests import Tx

resp = client.request(Tx(transaction="TXHASH..."))
result = resp.result

print(f"Validated: {result.get('validated', False)}")
print(f"Result: {result['meta']['TransactionResult']}")
print(f"Fee paid: {result['Fee']} drops")
print(f"Ledger: {result.get('ledger_index')}")

# For Payment: check delivered_amount vs Amount
if result['TransactionType'] == 'Payment':
    delivered = result['meta'].get('delivered_amount')
    requested = result.get('Amount')
    print(f"Requested: {requested}, Delivered: {delivered}")
```

---

## 11. Partial Payments

Partial payments can deliver less than the `Amount` field. Always check `meta.delivered_amount`:

```python
# DANGEROUS: Checking Amount without delivered_amount
amount_requested = tx["Amount"]  # may be currency object

# SAFE: Check actual delivered amount
delivered = result["meta"]["delivered_amount"]
```

This is a common exploit vector — see security doc 25.

---

## Related Files

- `knowledge/01-xrpl-accounts.md` — Account/Sequence fields
- `knowledge/02-xrpl-payments.md` — Payment-specific fields
- `knowledge/25-xrpl-audit-security.md` — LastLedgerSequence and replay protection
- `knowledge/30-xrpl-xrplpy.md` — xrpl-py serialization layer
