# XRPL Multi-Signing

## Overview

Multi-signing allows a set of accounts to collectively authorize transactions for a master account. The master account's SignerList defines who can sign and how much weight each signer contributes. Transactions require signatures whose total weight meets or exceeds the quorum.

---

## 1. SignerListSet Transaction

Establishes or updates the signer list:

```json
{
  "TransactionType": "SignerListSet",
  "Account": "rMASTER...",
  "SignerQuorum": 3,
  "SignerEntries": [
    {
      "SignerEntry": {
        "Account": "rSIGNER1...",
        "SignerWeight": 2
      }
    },
    {
      "SignerEntry": {
        "Account": "rSIGNER2...",
        "SignerWeight": 2
      }
    },
    {
      "SignerEntry": {
        "Account": "rSIGNER3...",
        "SignerWeight": 1
      }
    }
  ],
  "Fee": "12",
  "Sequence": 1
}
```

Rules:
- `SignerQuorum`: minimum total weight required (1–4,294,967,295)
- `SignerEntries`: 1–32 signers
- Each `SignerWeight`: 1–65,535
- All signers must have funded accounts on the XRPL

Quorum configurations:
| Scheme | Signers | Weights | Quorum | Description |
|--------|---------|---------|--------|-------------|
| 2-of-3 | A(1), B(1), C(1) | 1 each | 2 | Any 2 of 3 |
| 3-of-5 | A-E(1 each) | 1 each | 3 | Any 3 of 5 |
| Weighted 2-of-3 | A(2), B(2), C(1) | — | 3 | A+C or B+C or A+B |
| CEO+CFO | CEO(3), CFO(2), Auditor(1) | — | 3 | CEO alone or CFO+Auditor |

---

## 2. Deleting a Signer List

Set `SignerQuorum: 0` and omit `SignerEntries`:

```json
{
  "TransactionType": "SignerListSet",
  "Account": "rMASTER...",
  "SignerQuorum": 0,
  "Fee": "12",
  "Sequence": 2
}
```

---

## 3. Multi-Signed Transaction Format

Multi-signed transactions use the `Signers` array instead of a single `TxnSignature`:

```json
{
  "TransactionType": "Payment",
  "Account": "rMASTER...",
  "Destination": "rDEST...",
  "Amount": "1000000",
  "Fee": "36",
  "Sequence": 10,
  "SigningPubKey": "",
  "Signers": [
    {
      "Signer": {
        "Account": "rSIGNER1...",
        "TxnSignature": "3045...",
        "SigningPubKey": "ED...signer1_pubkey..."
      }
    },
    {
      "Signer": {
        "Account": "rSIGNER2...",
        "TxnSignature": "3045...",
        "SigningPubKey": "ED...signer2_pubkey..."
      }
    }
  ]
}
```

Important:
- `SigningPubKey` must be `""` (empty string) in the transaction body
- `Signers` must be sorted by Account address (ascending)
- `Fee` = base_fee × (N_signers + 1) minimum

Fee calculation:
```python
n_signers = 2
base_fee = 12  # drops
min_fee = base_fee * (n_signers + 1)  # = 36 drops
```

---

## 4. Python: Building a Multi-Signed Transaction

```python
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import Payment
from xrpl.wallet import Wallet
from xrpl.transaction import (
    autofill,
    sign,
    submit_and_wait
)
from xrpl.core.keypairs import sign as keypairs_sign
from xrpl.models.transactions.transaction import Signer

client = JsonRpcClient("https://xrplcluster.com")

# Wallets
signer1 = Wallet.from_seed("sn...")
signer2 = Wallet.from_seed("sn...")

# Build transaction
tx = Payment(
    account="rMASTER...",
    destination="rDEST...",
    amount="1000000",
    signing_pub_key="",      # empty for multisig
    sequence=10,
    fee="36",
    last_ledger_sequence=client.get_ledger_index() + 20
)

# Each signer independently signs
def sign_multisig(tx, wallet):
    return wallet.sign(tx.to_xrpl(), multisign=True)

sig1 = sign_multisig(tx, signer1)
sig2 = sign_multisig(tx, signer2)

# Combine signatures (must be in sorted Account order)
from xrpl.transaction import multisign
signed_tx = multisign(tx, [sig1, sig2])

result = submit_and_wait(signed_tx, client)
print(result.result["meta"]["TransactionResult"])
```

---

## 5. JavaScript: Multi-Signing with xrpl.js

```javascript
const xrpl = require('xrpl');

async function multiSign() {
  const client = new xrpl.Client('wss://xrplcluster.com');
  await client.connect();

  const masterAddress = 'rMASTER...';
  const signer1 = xrpl.Wallet.fromSeed('sn...');
  const signer2 = xrpl.Wallet.fromSeed('sn...');

  const tx = {
    TransactionType: 'Payment',
    Account: masterAddress,
    Destination: 'rDEST...',
    Amount: '1000000',
    SigningPubKey: '',
    Sequence: 10,
    Fee: '36',
    LastLedgerSequence: (await client.getLedgerIndex()) + 20
  };

  // Each signer produces their partial signature
  const sig1 = signer1.sign(tx, true);  // true = multisign
  const sig2 = signer2.sign(tx, true);

  // Combine
  const combined = xrpl.multisign([sig1.tx_blob, sig2.tx_blob]);
  const result = await client.submitAndWait(combined);
  console.log(result.result.meta.TransactionResult);

  await client.disconnect();
}
```

---

## 6. Regular Key vs Master Key for Signing

A signer in the SignerList can sign using either their master key or an assigned regular key.

### Assign regular key to signer account:

```json
{
  "TransactionType": "SetRegularKey",
  "Account": "rSIGNER1...",
  "RegularKey": "rREGKEY...",
  "Fee": "12",
  "Sequence": 1
}
```

Then disable master key (optional for security):

```json
{
  "TransactionType": "AccountSet",
  "Account": "rSIGNER1...",
  "SetFlag": 4,
  "Fee": "12",
  "Sequence": 2
}
```

When signing the multisig tx, the regular key's `SigningPubKey` is used but `Account` remains `rSIGNER1`.

---

## 7. Signer List ID

Every SignerList has a `SignerListID` (always 0 for the primary list). Reserved for future multi-list support.

```json
{
  "LedgerEntryType": "SignerList",
  "Account": "rMASTER...",
  "SignerListID": 0,
  "SignerQuorum": 3,
  "SignerEntries": [...],
  "index": "AABB..."
}
```

Query via `account_objects`:

```python
from xrpl.models.requests import AccountObjects

resp = client.request(AccountObjects(
    account="rMASTER...",
    type="signer_list"
))
signer_list = resp.result["account_objects"][0]
```

---

## 8. Corporate Wallet Patterns

### Treasury (3-of-5, equal weight)

```json
{
  "SignerQuorum": 3,
  "SignerEntries": [
    { "SignerEntry": { "Account": "rCFO...", "SignerWeight": 1 } },
    { "SignerEntry": { "Account": "rCEO...", "SignerWeight": 1 } },
    { "SignerEntry": { "Account": "rCTO...", "SignerWeight": 1 } },
    { "SignerEntry": { "Account": "rLegal...", "SignerWeight": 1 } },
    { "SignerEntry": { "Account": "rBoard...", "SignerWeight": 1 } }
  ]
}
```

### Executive Override (CEO alone or 2 others)

```json
{
  "SignerQuorum": 3,
  "SignerEntries": [
    { "SignerEntry": { "Account": "rCEO...", "SignerWeight": 3 } },
    { "SignerEntry": { "Account": "rCFO...", "SignerWeight": 2 } },
    { "SignerEntry": { "Account": "rCTO...", "SignerWeight": 1 } },
    { "SignerEntry": { "Account": "rLegal...", "SignerWeight": 1 } }
  ]
}
```

### Cold/Hot Wallet Split (offline cold signs alone)

```json
{
  "SignerQuorum": 2,
  "SignerEntries": [
    { "SignerEntry": { "Account": "rCOLD_OFFLINE...", "SignerWeight": 2 } },
    { "SignerEntry": { "Account": "rHOT_ONLINE...", "SignerWeight": 1 } },
    { "SignerEntry": { "Account": "rBACKUP...", "SignerWeight": 1 } }
  ]
}
```

---

## 9. Disabling Master Key After Setup

Once signer list is in place, disable the master key for maximum security:

```json
{
  "TransactionType": "AccountSet",
  "Account": "rMASTER...",
  "SetFlag": 4,
  "Fee": "12",
  "Sequence": 5
}
```

> **Warning**: Only do this after confirming your multisig works. Losing access to all signers = permanent loss.

---

## 10. Reserve Impact

Each SignerEntry costs 0.2 XRP reserve:
```
required_reserve = 10 + (2 × N_signers_in_list)
```

5-signer list: 10 + 10 = 20 XRP locked as reserve on master account.

---

## 11. Common Errors

| Error | Cause |
|-------|-------|
| `tecNO_ALTERNATIVE_KEY` | Deleting signer list when master key is disabled |
| `temBAD_SIGNER` | Signer is the master account itself |
| `temBAD_QUORUM` | Quorum > sum of all weights |
| `tefBAD_QUORUM` | Submitted signatures don't meet quorum |
| `tefNOT_MULTI_SIGNING` | Signers array order incorrect |
| `terNO_ACCOUNT` | A signer account doesn't exist on ledger |

---

## Related Files

- `knowledge/01-xrpl-accounts.md` — account flags governing multi-sig
- `knowledge/15-xrpl-transaction-format.md` — Signers field encoding
- `knowledge/25-xrpl-audit-security.md` — key-management hardening
- `knowledge/37-xrpl-amendments.md` — ExpandedSignerList amendment
