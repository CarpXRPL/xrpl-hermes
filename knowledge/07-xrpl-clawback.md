# XRPL Clawback (XLS-39)

## Overview

The **Clawback** amendment (XLS-39) gives token issuers the ability to **reclaim** (claw back) tokens from holders under certain conditions. This feature was designed primarily for regulated financial institutions and compliance use cases, where issuers must be able to recover tokens in cases of fraud, regulatory action, or error.

## Amendment Status

The Clawback amendment was enabled on the XRP Ledger mainnet via the `Clawback` amendment (v1.12.0+). It is a **per-account opt-in** feature — issuers must explicitly enable it.

## Enabling Clawback

### lsfAllowTrustLineClawback Flag

To enable clawback, an account must set the `lsfAllowTrustLineClawback` flag using an `AccountSet` transaction:

```json
{
  "TransactionType": "AccountSet",
  "Account": "rIssuerAddress",
  "SetFlag": 16  // asfAllowTrustLineClawback
}
```

**IMPORTANT: This flag is PERMANENT.** Once set, it can never be unset. Enabling clawback signals to the market that the issuer retains the right to reclaim tokens.

### Flag Value

| Flag Name | Hex Value | Decimal |
|---|---|---|
| `lsfAllowTrustLineClawback` | 0x20000000 | 536870912 |

## The Clawback Transaction

The `Clawback` transaction type allows an issuer to reclaim tokens from a holder.

### Fields

| Field | Required | JSON Type | Description |
|---|---|---|---|
| `Account` | ✅ | String | The issuer's address (who is performing the clawback) |
| `Amount` | ✅ | Object | The amount to claw back (must specify currency, issuer, and value) |

### Important Rules

1. **Issuer-only**: Only the token issuer can initiate a clawback
2. **Partial clawback supported**: The `Amount.value` field specifies how much to claw back. If the value exceeds the holder's balance, it claws back the entire balance. You are not required to claw back the full trust line.
3. **Trust line creation window**: Clawback only applies to trust lines created AFTER the `lsfAllowTrustLineClawback` flag was set on the issuer's account
4. **No XRP clawback**: XRP cannot be clawed back — only issued tokens
5. **No AMM LP tokens**: LP tokens from AMM pools cannot be clawed back

### Example: Clawback Tokens

```json
{
  "TransactionType": "Clawback",
  "Account": "rIssuerAddress",
  "Amount": {
    "currency": "USD",
    "issuer": "rHolderAddress",
    "value": "1000"
  },
  "Fee": "10",
  "Sequence": 50
}
```

This claws back 1000 USD from `rHolderAddress` that was originally issued by `rIssuerAddress`.

### Python Example

```python
from xrpl.transaction import submit_and_wait
from xrpl.models.transactions import Clawback
from xrpl.models.amounts import IssuedCurrencyAmount

clawback_tx = Clawback(
    account="rIssuerAddress",
    amount=IssuedCurrencyAmount(
        currency="USD",
        issuer="rHolderAddress",
        value="1000",
    ),
)
response = submit_and_wait(clawback_tx, client, issuer_wallet)
```

### JavaScript Example

```javascript
const { Clawback } = require('xrpl');

const clawback = {
  TransactionType: 'Clawback',
  Account: 'rIssuerAddress',
  Amount: {
    currency: 'USD',
    issuer: 'rHolderAddress',
    value: '1000',
  },
};
const response = await client.submitAndWait(clawback, { wallet: issuerWallet });
```

## Trust Line Creation Window

The clawback mechanism only affects trust lines created **after** the `lsfAllowTrustLineClawback` flag was enabled. Trust lines that existed before the flag was set are **grandfathered** and cannot be clawed back.

### Why This Matters

1. An issuer decides to enable clawback for compliance reasons
2. Existing holders' trust lines are unaffected — their tokens cannot be clawed back
3. Any new trust lines created after the flag is set are subject to clawback
4. This gives existing holders time to decide whether they want to continue holding the token

### Checking if a Trust Line is Clawback-Eligible

There is no direct flag on trust lines indicating clawback eligibility. Instead:
1. Check if the issuer has `lsfAllowTrustLineClawback` set
2. Compare the trust line creation ledger sequence with the flag's activation ledger
3. If the trust line was created after the flag, it's eligible for clawback

## Use Cases

### 1. Regulated Tokens (Security Tokens)

Issuers of security tokens (e.g., tokenized stocks, bonds) may need to:
- Recover tokens from accounts that are no longer qualified investors
- Comply with court orders or regulatory actions
- Handle dividend/interest recalculations

### 2. Error Recovery

If tokens were accidentally sent to the wrong address, the issuer can:
- Verify the error (wrong address, wrong amount)
- Execute a clawback to reclaim the mistakenly sent tokens
- Re-issue to the correct address

### 3. Fraud and Theft

In cases of:
- Stolen tokens
- Account compromise
- Phishing attacks

The issuer can freeze (if they have freeze capability) and then claw back the affected tokens.

### 4. Compliance and Sanctions

For tokens used in regulated environments:
- Sanctions screening failures
- KYC/AML compliance violations
- Account closures

## Risks and Considerations

### For Issuers

1. **Market trust**: Enabling clawback may reduce trust in your token — holders may prefer non-clawback tokens
2. **Liquidity impact**: Tokens with clawback may trade at a discount compared to non-clawback alternatives
3. **Irreversibility**: Once `lsfAllowTrustLineClawback` is set, it can never be disabled
4. **Reputation**: Improper use of clawback can damage your reputation as an issuer

### For Holders

1. **Loss risk**: Your balance can be reduced to zero at any time (only for eligible trust lines)
2. **Due diligence**: Check if an issuer has clawback enabled before acquiring their tokens
3. **Alternative tokens**: Consider holding tokens from issuers without clawback enabled
4. **Grandfathering**: If you held tokens before clawback was enabled, you're protected

## Technical Implementation Details

### Ledger Entry Changes

When `lsfAllowTrustLineClawback` is set, the AccountRoot ledger entry includes this flag in the `Flags` field. No new ledger entry types are needed.

### Transaction Execution

When a `Clawback` transaction executes:
1. Protocol verifies the sender is the issuer (the account in `Amount.issuer`... wait, no — the sender (Account field) must be the issuer)
2. Protocol verifies the trust line exists
3. Protocol checks the trust line was created after the clawback flag
4. Protocol transfers the full balance from holder's trust line to issuer's trust line
5. The holder's trust line balance becomes 0

### Result Codes

| Code | Description |
|---|---|
| `tesSUCCESS` | Clawback successful |
| `tecNO_LINE` | Trust line doesn't exist |
| `tecNO_PERMISSION` | Sender is not authorized (not the issuer, or trust line grandfathered) |
| `temDISABLED` | Clawback amendment not activated |
| `temBAD_AMOUNT` | Invalid amount specified |
| `tecINSUF_RESERVE` | Clawback would leave holder below reserve |

## Comparison with Freeze

| Feature | Freeze | Clawback |
|---|---|---|
| What happens | Tokens become untransferable | Tokens are returned to issuer |
| Partial | Can freeze specific trust lines | Full balance only |
| Reversible | Yes (unfreeze) | No (irreversible for that balance) |
| Grandfathering | No | Yes (pre-existing trust lines exempt) |
| Required flag | `lsfGlobalFreeze` (or per-trust-line) | `lsfAllowTrustLineClawback` |
| Permanence | Can be unfrozen | Flag is permanent |

## Regulatory Compliance

### For MiCA (EU Crypto Regulation)

Under MiCA, issuers of asset-referenced tokens and e-money tokens must have:
- Redemption rights
- Ability to freeze assets in certain circumstances
- Clawback capability for error/illegal transactions

XLS-39 clawback, combined with freeze capabilities, helps satisfy these requirements.

### For FATF Travel Rule

Virtual Asset Service Providers (VASPs) may need:
- Ability to reverse suspicious transactions
- Compliance with court orders for asset recovery
- Sanctions screening response mechanisms

## Best Practices

### For Issuers

1. **Communicate clearly**: Disclose clawback capability in your token documentation
2. **Use responsibly**: Only claw back for legitimate reasons (fraud, compliance, error)
3. **Provide notice**: If possible, notify affected holders before clawing back
4. **Keep records**: Document the reason and authorization for each clawback
5. **Consider alternatives**: Freeze first, investigate, then clawback if warranted

### For Developers

1. **Check the flag**: In your app, check if an issuer has `lsfAllowTrustLineClawback` set
2. **Display warnings**: Show holders when a token has clawback enabled
3. **Handle gracefully**: Design UI/UX that accounts for potential balance changes
4. **Monitor events**: Set up webhook/alerts for clawback transactions on tokens you hold

### Checking if an Issuer Has Clawback Enabled

```json
{
  "method": "account_info",
  "params": [{
    "account": "rIssuerAddress"
  }]
}
```

Check the `Flags` field:
- If `Flags & 536870912` is non-zero, clawback is enabled
- If not, clawback is disabled
