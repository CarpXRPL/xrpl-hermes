# RWA Tokenization on XRPL — Real-World Assets

## Overview

**Real-World Asset (RWA) tokenization** is the process of representing ownership rights in physical or off-chain assets (real estate, bonds, commodities, private equity, receivables) as digital tokens on a blockchain. XRPL's native features — low fees, trustlines, DEX, MPTs, Clawback, and RequireAuth — make it well-suited for compliant, institutional-grade RWA issuance.

**Why XRPL for RWA?**
- Sub-cent transaction fees (no gas auctions)
- 3-5 second settlement finality
- Native compliance tools: Freeze, Clawback, RequireAuth, TransferRate
- Built-in DEX for secondary market liquidity
- Multi-Purpose Tokens (MPTs, XLS-33) for regulatory-grade issuance
- ISO 20022 compatible payment metadata via Memos

---

## Legal Framework

### Structure: SPV + Token Representation

Most compliant RWA issuances use a **Special Purpose Vehicle (SPV)** to hold the underlying asset and issue tokens representing shares or debt interests.

```
Real Asset (Property / Bond / Invoice)
        │
        ▼
    SPV (LLC / Cayman / BVI trust)
    ├── Holds legal title to the asset
    ├── Issues "Participation Notes" or equity interests
    ├── Audited by independent accountant
    └── Governed by issuance agreement
        │
        ▼
    Token Issuer Account (XRPL)
    ├── Represents SPV shares as XRPL tokens
    ├── RequireAuth — only KYC'd investors hold tokens
    ├── Clawback — regulatory recovery capability
    ├── TransferRate — secondary market fee to SPV
    └── 1 token = 1 SPV unit (e.g., 1 USD of asset NAV)
        │
        ▼
    Investors (XRPL addresses with authorized trustlines)
```

### Key Legal Documents

| Document | Purpose |
|---|---|
| **Token Purchase Agreement** | Defines investor rights, token = legal interest |
| **SPV Operating Agreement** | Governs the SPV, defines unit-holder rights |
| **Offering Memorandum / PPM** | Discloses risks, regulatory status, redemption terms |
| **Custody Agreement** | Third-party custodian for underlying asset |
| **Audit Reports** | Periodic NAV confirmation by independent accountant |
| **Redemption Agreement** | How and when tokens can be redeemed for USD/asset |

---

## Token Design Patterns

### Pattern A: IOU Tokens (Classic Trustlines)

Best for: Simple debt instruments, stablecoins backed by bonds, invoice financing.

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


### Pattern B: Multi-Purpose Tokens (MPTs, XLS-33)

Best for: Securities with complex transfer restrictions, regulatory-grade issuance, transferability controls.

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## Fractionalization Patterns

### Real Estate Fractionalization

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## Transfer Restrictions

### On-Chain Transfer Controls

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## Redemption Patterns

### Token Burn on Redemption

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## Audit Trail

XRPL's immutable ledger provides a complete, timestamped audit trail. Every issuance, transfer, freeze, and redemption is permanently recorded.

```python
async def generate_rwa_audit_report(
    issuer_address: str,
    token_code: str,
    from_ledger: Optional[int] = None,
    to_ledger: Optional[int] = None,
) -> dict:
    """
    Generate an on-chain audit report for a RWA token.
    Returns: total issuance, total redeemed, current supply, all events.
    """
    async with AsyncJsonRpcClient(XRPL_RPC) as client:
        from xrpl.models import AccountTx, GatewayBalances

        # Current supply
        supply_req = GatewayBalances(account=issuer_address, ledger_index="validated")
        supply_resp = await client.request(supply_req)
        current_supply = supply_resp.result.get("obligations", {}).get(token_code, "0")

        # Transaction history
        tx_req = AccountTx(
            account=issuer_address,
            ledger_index_min=from_ledger or -1,
            ledger_index_max=to_ledger or -1,
            limit=400,
        )
        tx_resp = await client.request(tx_req)
        transactions = tx_resp.result.get("transactions", [])

        issuances = []
        redemptions = []
        freezes = []
        clawbacks = []

        for tx_wrapper in transactions:
            tx = tx_wrapper.get("tx", {})
            tx_type = tx.get("TransactionType")
            amt = tx.get("Amount", {})

            if tx_type == "Payment" and isinstance(amt, dict) and amt.get("currency") == token_code:
                if tx.get("Destination") == issuer_address:
                    redemptions.append({"amount": amt["value"], "from": tx["Account"], "hash": tx.get("hash")})
                elif tx.get("Account") == issuer_address:
                    issuances.append({"amount": amt["value"], "to": tx["Destination"], "hash": tx.get("hash")})
            elif tx_type == "TrustSet" and tx.get("Account") == issuer_address:
                flags = tx.get("Flags", 0)
                if flags & 0x00100000:  # tfSetFreeze
                    freezes.append({"address": tx.get("LimitAmount", {}).get("issuer"), "hash": tx.get("hash")})
            elif tx_type == "Clawback":
                clawbacks.append({"amount": tx.get("Amount", {}).get("value"), "from": tx.get("Amount", {}).get("issuer"), "hash": tx.get("hash")})

        total_issued = sum(float(i["amount"]) for i in issuances)
        total_redeemed = sum(float(r["amount"]) for r in redemptions)
        total_clawedback = sum(float(c["amount"]) for c in clawbacks)

        return {
            "token": token_code,
            "issuer": issuer_address,
            "current_supply": current_supply,
            "total_issued": total_issued,
            "total_redeemed": total_redeemed,
            "total_clawedback": total_clawedback,
            "issuances": len(issuances),
            "redemptions": len(redemptions),
            "freezes_applied": len(freezes),
            "clawbacks": len(clawbacks),
        }
```

---

## Regulatory Considerations by Jurisdiction

### United States

| Asset Type | Regulatory Framework | Registration |
|---|---|---|
| Real estate equity | Securities Act 1933, Reg D / Reg A+ / Reg CF | SEC / FINRA |
| Debt / bonds | Securities Exchange Act 1934 | SEC |
| Commodities | CFTC | CFTC registration |
| Money market / Treasury | Investment Company Act 1940 | SEC |

**Key exemptions for tokenized assets:**
- **Reg D 506(b):** Up to 35 non-accredited investors, no general solicitation
- **Reg D 506(c):** Accredited investors only, general solicitation allowed
- **Reg A+:** Up to $75M/year offering, lighter disclosure, non-accredited allowed
- **Reg CF:** Crowdfunding up to $5M/year

**Transfer restrictions (Reg D):** 1-year lockup for Reg D. Enforce on-chain via:
1. Freeze investor trustline for 12 months from issuance date
2. Unfreeze after lockup expiry (can be automated)

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


### European Union

- **MiCA (Markets in Crypto-Assets):** Applies to asset-referenced tokens and e-money tokens. Whitepaper required. ESMA oversight.
- **AIFMD:** Real estate fund structures may require Alternative Investment Fund Manager registration
- **GDPR:** KYC data must be handled with data minimization; on-chain memos must not contain PII

### Singapore (MAS)

- **Digital Token offering:** May qualify as Capital Markets Products under SFA
- **MAS Regulatory Sandbox:** Available for innovative tokenization projects
- **Recognized Market Operator:** Required to operate a secondary market platform

### Cayman Islands / BVI

Popular for offshore SPV structures:
- No capital gains tax
- Flexible fund structures (Segregated Portfolio Company)
- No restrictions on token holder nationality
- Must comply with FATF standards for AML/KYC

---

## On-Chain NAV Updates

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## Secondary Market via XRPL DEX

> **Quarantined direct-sign recipe.** The former block handled key material or signed/submitted inside the process. Use the corresponding `build-*` command for unsigned JSON, a compatible user-owned external signer, and `tx-info` for validated-result verification.


---

## Full RWA Issuance Checklist

### Pre-Launch
- [ ] Legal structure: SPV formed, jurisdiction selected
- [ ] Offering memorandum / PPM finalized with legal counsel
- [ ] Regulatory filing (Reg D / Reg A+ / MiCA whitepaper) completed
- [ ] KYC/AML provider integrated (Synaps, Sumsub, Jumio)
- [ ] Custodian agreement for underlying asset signed
- [ ] Independent auditor engaged for NAV attestation
- [ ] Travel Rule provider integrated (Notabene / Sygna)

### On-Chain Setup
- [ ] Issuer account created (separate cold wallet recommended)
- [ ] RequireAuth enabled
- [ ] DefaultRipple enabled
- [ ] Clawback enabled (irreversible — do this intentionally)
- [ ] TransferRate set (0.5-1% typical for admin fee)
- [ ] Domain set and verified (`xrp-ledger.toml` with token info)

### Issuance
- [ ] Investor completes KYC → off-chain approval
- [ ] Sanctions screen (Chainalysis / Elliptic)
- [ ] Investor creates trustline (self-funded XRPL account)
- [ ] Issuer authorizes trustline
- [ ] Issuer sends tokens (pro-rata to subscription)
- [ ] Reg D lockup freeze applied if applicable

### Ongoing Operations
- [ ] Quarterly NAV updates published on-chain
- [ ] Annual audit report linked in memo / Arweave
- [ ] Monthly/quarterly income distributions (rental/coupon)
- [ ] Monitoring: large transfers, frozen accounts, redemptions
- [ ] Travel Rule compliance for institutional transfers

---

## Resources

- XRPL Authorized Trust Lines: https://xrpl.org/authorized-trust-lines.html
- XRPL Clawback: https://xrpl.org/clawback.html
- XRPL MPTs (XLS-33): https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0033d-multi-purpose-tokens
- XRPL Domain Verification: https://xrpl.org/xrp-ledger-toml.html
- SEC Reg D: https://www.sec.gov/regulation-d
- MiCA Regulation: https://www.esma.europa.eu/esmas-activities/digital-finance-and-innovation/markets-crypto-assets-regulation-mica
- Notabene Travel Rule: https://notabene.id
- Chainalysis: https://www.chainalysis.com
- IVMS101 standard: https://intervasp.org/

---

## Related Files

- `07-xrpl-clawback.md` — Clawback amendment technical details
- `08-xrpl-mpts.md` — Multi-Purpose Tokens for regulatory issuance
- `21-xrpl-token-model.md` — Core trustline and token model
- `24-xrpl-deploy-guide.md` — Token deployment workflow
- `25-xrpl-audit-security.md` — Security and audit checklist
- `52-xrpl-l1-reference.md` — Full L1 transaction reference
- `58-rlusd-operations.md` — RLUSD as payment/settlement currency for RWA income
- `47-xrpl-arweave-storage.md` — Permanent storage for audit documents
