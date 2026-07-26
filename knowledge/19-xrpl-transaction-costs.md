# XRPL Transaction Fees and Reserves

## Status

**Certified boundary:** XRPL-Hermes reads current validated-ledger fee/reserve fields and builds unsigned transaction intent. Fee levels and reserves are live network state; this file intentionally does not publish fixed “current” XRP values.

XRPL-Hermes does not sign or broadcast transactions. A user-controlled external signer must review the selected network, fee, sequence and intent, then Hermes verifies the returned transaction on a validated ledger.

## Exact conversion

One XRP is exactly `1,000,000` drops. Native XRP transaction amounts and fees use integer drops.

```python
DROPS_PER_XRP = 1_000_000


def xrp_text_to_drops(value: str) -> int:
    from decimal import Decimal
    drops = Decimal(value) * DROPS_PER_XRP
    if drops != drops.to_integral_value():
        raise ValueError("XRP amount must resolve to whole drops")
    return int(drops)
```

Do not use binary floating point to produce a transaction amount or fee.

## Read live values

Use the selected network's validated state immediately before building and authorizing:

```bash
python3 -m scripts.xrpl_tools server-info
python3 -m scripts.xrpl_tools account rADDRESS
```

`server-info` reports observed build/network state plus validated-ledger fee and reserve fields when the selected server supplies them. An application can also call the XRPL `fee` method against its chosen rippled endpoint.

Treat public endpoints as external dependencies. Bound timeouts/retries, record the endpoint and observation time, and reject a response from the wrong network.

## Transaction fee rules

- The `Fee` field is XRP in integer drops and is destroyed, not paid to validators.
- The open-ledger fee can rise with load. Never assume a copied minimum is currently sufficient.
- A signer/wallet may autofill a fee, but the user must still review the resulting upper bound.
- Multisigned and condition-bearing transactions can require a higher fee than a simple transaction.
- `AccountDelete` has a special minimum tied to the network's **current incremental owner reserve**. Query validated network state; do not hard-code an old XRP amount.
- A failed transaction with a `tec` result can still consume its fee and sequence when included in a validated ledger.

XRPL-Hermes builders emit intent for external autofill/authorization. Production policy should cap acceptable fees and reject an authorization response whose fee exceeds the reviewed limit.

## Account reserve

An account's reserve requirement is based on live validated network values:

```text
required reserve = base reserve + (OwnerCount × incremental owner reserve)
```

The base and incremental reserve can change through network governance. Read them from the selected validated ledger rather than embedding historical values.

Many owned ledger objects can increase `OwnerCount`, including trust lines, offers, escrows, checks, tickets, payment channels and NFT pages. Exact ownership/reserve behavior is transaction- and amendment-specific; inspect `account_info` and `account_objects` before assuming an object can be removed.

A conservative spendable-balance calculation is:

```python
def spendable_drops(balance: int, owner_count: int, base: int, increment: int) -> int:
    return max(0, balance - (base + owner_count * increment))
```

Use values from the same selected network and a sufficiently recent validated ledger. If provenance or freshness is missing, report that rather than presenting a spendable balance as current.

## Object cleanup and account deletion

Cleanup is a sequence of reviewed unsigned transactions, not an automatic loop:

1. Read `account_objects` from a validated ledger.
2. Identify obligations and objects by type.
3. Build the specific cancellation/removal transaction with the matching `build-*` command.
4. Review and authorize it in the external signer.
5. Verify `validated: true` and the final engine result.
6. Re-read account state before building the next step.

Before an `AccountDelete` intent, verify current official transaction documentation and validated account state. Requirements include age/sequence constraints, no blocking obligations, an appropriate destination, and the dynamic special fee. Failure can consume a fee; never construct deletion from stale copied values.

## Operational checklist

- Select Testnet explicitly for new flows.
- Capture network, endpoint, ledger index/hash and UTC observation time.
- Query live fee/reserve values.
- Apply a user-approved maximum fee policy.
- Keep amount and fee arithmetic in integers/decimal text.
- Never estimate total cost from fees alone; owned objects also lock reserve.
- Re-read state after every validated transaction.
- Do not retry `tem`, `tel`, `ter` or `tec` results under one generic policy.
- Mainnet value movement requires explicit authorization, bounded value/fees and monitoring.

For exact transaction semantics, use current first-party XRPL documentation and observed validated-ledger state. Historical fee/reserve examples are not release evidence.
