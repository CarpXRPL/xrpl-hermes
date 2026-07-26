# XRPL Token Issuance: Step by Step

## Overview

Complete guide to issuing a fungible token on the XRPL mainnet. Covers wallet setup, issuer configuration, trust line setup, token distribution, AMM creation, and optional blackholing.

---

## 1. Architecture

```
    [ISSUER WALLET]           [DISTRIBUTION WALLET]
    - AccountSet flags         - Hold initial supply
    - Sets DefaultRipple       - Create DEX offers
    - Sets TransferRate        - Manage liquidity
    - Issues to distributor
    - (Optionally blackholed)
```

Keep issuer and distributor separate. The issuer is a cold wallet; the distributor is the hot operational wallet.

---

## 2. Fund Wallets

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## 3. Configure the Issuer Account

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## 4. Optional: Require Authorization (KYC)

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## 5. Distributor Creates Trust Line

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


If `RequireAuth` is enabled, issuer must authorize first:
> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## 6. Issue Tokens

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## 7. Create AMM Pool

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## 8. Create DEX Offers (Optional)

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## 9. Blackhole the Issuer

Only after confirming all tokens are issued correctly:

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## 10. Verify on Explorer

```python
# Verify issuer account flags
from xrpl.models.requests import AccountInfo

resp = client.request(AccountInfo(
    account=issuer_wallet.address,
    ledger_index="validated"
))
acct = resp.result["account_data"]
flags = acct["Flags"]

# Check flags
lsf_default_ripple = 0x00800000
lsf_disable_master = 0x00100000
lsf_no_freeze = 0x00200000

print(f"DefaultRipple: {bool(flags & lsf_default_ripple)}")
print(f"MasterDisabled: {bool(flags & lsf_disable_master)}")
print(f"NoFreeze: {bool(flags & lsf_no_freeze)}")
print(f"TransferRate: {acct.get('TransferRate', 'Not set')}")
print(f"TickSize: {acct.get('TickSize', 'Not set')}")
print(f"Domain: {bytes.fromhex(acct.get('Domain', '')).decode()}")
```

Verify issuer state through validated XRPL JSON-RPC/Clio reads (`account`, `trustlines`, `account_objects`).
Any explorer is optional external context and requires separate current contract/security acceptance.

---

## 11. Register Token Metadata

External metadata listings are optional dependencies, not certified issuance steps. Verify each
provider's current first-party process, schema, fees and security before sending issuer metadata.
- TOML file at `https://yourdomain.com/.well-known/xrp-ledger.toml`

```toml
# .well-known/xrp-ledger.toml
[METADATA]
modified = 2024-01-01

[[ACCOUNTS]]
address = "rISSUER..."
desc = "MYTKN issuer account"

[[CURRENCIES]]
code = "MYTKN"
issuer = "rISSUER..."
display_decimals = 6
name = "My Token"
desc = "The utility token for MyProject"
icon = "https://mytoken.com/icon.png"
```

---

## Related Files

- `knowledge/03-xrpl-trustlines.md` — trust line authorisation
- `knowledge/07-xrpl-clawback.md` — enabling clawback on the issuer
- `knowledge/21-xrpl-token-model.md` — issuer model background
- `knowledge/25-xrpl-audit-security.md` — issuer hardening checklist
- `knowledge/38-xrpl-minting-ops.md` — operational minting playbook
