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

```python
import asyncio
from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.models import (
    AccountSet, AccountSetFlag, TrustSet, Payment,
    AMMDeposit, AMMDepositFlag,
)
from xrpl.wallet import Wallet

XRPL_RPC = "https://xrplcluster.com"


async def setup_rwa_issuer(
    issuer_wallet: Wallet,
    token_code: str,          # e.g. "PROP1", "BOND1"
    transfer_rate_pct: float, # e.g. 0.5 = 0.5% fee on transfers
) -> dict:
    """
    Configure an XRPL account as a compliant RWA token issuer.
    Enables: RequireAuth, Clawback, TransferRate, DefaultRipple, Domain.
    """
    async with AsyncJsonRpcClient(XRPL_RPC) as client:
        from xrpl.asyncio.transaction import submit_and_wait
        # Transfer rate: 1000000000 = 0%, 1005000000 = 0.5%
        transfer_rate_raw = int(1_000_000_000 * (1 + transfer_rate_pct / 100))

        tx = AccountSet(
            account=issuer_wallet.address,
            set_flag=AccountSetFlag.ASF_REQUIRE_AUTH,   # KYC gating
            transfer_rate=transfer_rate_raw,
        )
        r1 = await submit_and_wait(tx, client, issuer_wallet)

        tx2 = AccountSet(
            account=issuer_wallet.address,
            set_flag=AccountSetFlag.ASF_DEFAULT_RIPPLE,  # allow rippling
        )
        r2 = await submit_and_wait(tx2, client, issuer_wallet)

        # Enable Clawback (one-time, irreversible)
        tx3 = AccountSet(
            account=issuer_wallet.address,
            set_flag=AccountSetFlag.ASF_ALLOW_TRUSTLINE_CLAWBACK,
        )
        r3 = await submit_and_wait(tx3, client, issuer_wallet)

        return {
            "issuer": issuer_wallet.address,
            "token": token_code,
            "transfer_rate_pct": transfer_rate_pct,
            "require_auth": True,
            "clawback": True,
            "tx_hashes": [
                r1.result.get("hash"),
                r2.result.get("hash"),
                r3.result.get("hash"),
            ],
        }


async def issue_rwa_tokens(
    issuer_wallet: Wallet,
    investor_address: str,
    token_code: str,
    amount: str,
) -> dict:
    """
    Authorize investor trustline and issue tokens.
    Call only after KYC/AML approval and legal subscription documents signed.
    """
    async with AsyncJsonRpcClient(XRPL_RPC) as client:
        from xrpl.asyncio.transaction import submit_and_wait

        # Step 1: Authorize the investor's trustline
        auth_tx = TrustSet(
            account=issuer_wallet.address,
            limit_amount={
                "currency": token_code,
                "issuer": investor_address,
                "value": "0",
            },
            flags=0x00020000,  # tfSetfAuth
        )
        await submit_and_wait(auth_tx, client, issuer_wallet)

        # Step 2: Send tokens to investor (issuance)
        payment_tx = Payment(
            account=issuer_wallet.address,
            destination=investor_address,
            amount={
                "currency": token_code,
                "issuer": issuer_wallet.address,
                "value": amount,
            },
        )
        result = await submit_and_wait(payment_tx, client, issuer_wallet)
        return {
            "investor": investor_address,
            "tokens_issued": amount,
            "currency": token_code,
            "tx_hash": result.result.get("hash"),
        }
```

### Pattern B: Multi-Purpose Tokens (MPTs, XLS-33)

Best for: Securities with complex transfer restrictions, regulatory-grade issuance, transferability controls.

```python
from xrpl.models import MPTokenIssuanceCreate, MPTokenAuthorize, MPTokenIssuanceSet


async def create_rwa_mpt(
    issuer_wallet: Wallet,
    maximum_amount: int,        # total supply cap (in token units)
    asset_scale: int = 2,       # decimal places (2 = cents)
    transfer_fee_bps: int = 50, # basis points (50 = 0.5%)
) -> dict:
    """
    Create an MPT for RWA issuance with:
    - Capped supply
    - Transfer fee
    - RequireAuth (can_transfer flag)
    - Clawback enabled
    """
    async with AsyncJsonRpcClient(XRPL_RPC) as client:
        from xrpl.asyncio.transaction import submit_and_wait

        # MPT flags: tfMPTCanClawback | tfMPTRequireAuth | tfMPTCanTransfer
        MPT_FLAGS = 0x00000002 | 0x00000008 | 0x00000010
        # tfMPTCanClawback = 0x00000002
        # tfMPTRequireAuth  = 0x00000008
        # tfMPTCanTransfer  = 0x00000010

        tx = MPTokenIssuanceCreate(
            account=issuer_wallet.address,
            maximum_amount=maximum_amount,
            asset_scale=asset_scale,
            transfer_fee=transfer_fee_bps,
            flags=MPT_FLAGS,
        )
        result = await submit_and_wait(tx, client, issuer_wallet)
        mpt_issuance_id = result.result.get("meta", {}).get("MPTokenIssuanceID")
        return {
            "mpt_issuance_id": mpt_issuance_id,
            "issuer": issuer_wallet.address,
            "max_supply": maximum_amount,
            "transfer_fee_bps": transfer_fee_bps,
            "tx_hash": result.result.get("hash"),
        }


async def authorize_mpt_investor(
    issuer_wallet: Wallet,
    investor_address: str,
    mpt_issuance_id: str,
) -> dict:
    """Authorize an investor to hold an MPT (post-KYC)."""
    async with AsyncJsonRpcClient(XRPL_RPC) as client:
        from xrpl.asyncio.transaction import submit_and_wait
        tx = MPTokenAuthorize(
            account=issuer_wallet.address,
            holder=investor_address,
            mptoken_issuance_id=mpt_issuance_id,
        )
        result = await submit_and_wait(tx, client, issuer_wallet)
        return {"authorized": investor_address, "tx_hash": result.result.get("hash")}
```

---

## Fractionalization Patterns

### Real Estate Fractionalization

```python
from dataclasses import dataclass
from typing import Optional


@dataclass
class PropertyToken:
    """Metadata for a fractionalized real estate token."""
    property_address: str
    total_value_usd: float
    total_tokens: int           # e.g. 1,000,000 tokens = $1M property
    token_price_usd: float      # = total_value_usd / total_tokens
    annual_yield_pct: float     # projected rental yield
    token_code: str             # e.g. "PROP1"
    spv_jurisdiction: str       # e.g. "Delaware LLC"
    auditor: str
    last_valuation_date: str


async def calculate_token_allocation(
    investment_usd: float,
    property: PropertyToken,
) -> dict:
    """Calculate how many tokens an investor gets for a USD investment."""
    tokens = investment_usd / property.token_price_usd
    annual_income = (investment_usd * property.annual_yield_pct) / 100
    return {
        "investment_usd": investment_usd,
        "tokens": tokens,
        "token_price_usd": property.token_price_usd,
        "ownership_pct": (tokens / property.total_tokens) * 100,
        "projected_annual_income_usd": annual_income,
        "projected_monthly_income_usd": annual_income / 12,
    }


async def distribute_rental_income(
    issuer_wallet: Wallet,
    token_code: str,
    total_rental_usd: float,
    payment_currency: str,       # e.g. "RLUSD"
    payment_issuer: str,         # RLUSD issuer
) -> list[dict]:
    """
    Distribute pro-rata rental income to all token holders.
    Fetches holder list, calculates share, sends payment.
    """
    async with AsyncJsonRpcClient(XRPL_RPC) as client:
        from xrpl.asyncio.transaction import submit_and_wait
        from xrpl.models import AccountLines

        # Get all token holders and their balances
        holders = []
        total_supply = 0.0
        marker = None
        while True:
            req = AccountLines(
                account=issuer_wallet.address,
                limit=200,
                marker=marker,
            )
            resp = await client.request(req)
            for line in resp.result.get("lines", []):
                if line["currency"] == token_code and float(line["balance"]) < 0:
                    # Negative balance on issuer side = positive holder balance
                    bal = abs(float(line["balance"]))
                    holders.append({"address": line["account"], "balance": bal})
                    total_supply += bal
            marker = resp.result.get("marker")
            if not marker:
                break

        results = []
        for holder in holders:
            share = holder["balance"] / total_supply
            income_amount = str(round(total_rental_usd * share, 6))

            tx = Payment(
                account=issuer_wallet.address,
                destination=holder["address"],
                amount={
                    "currency": payment_currency,
                    "issuer": payment_issuer,
                    "value": income_amount,
                },
                memos=[{
                    "memo": {
                        "memo_type": "72656e74616c5f696e636f6d65",  # "rental_income"
                        "memo_data": token_code.encode().hex(),
                    }
                }],
            )
            r = await submit_and_wait(tx, client, issuer_wallet)
            results.append({
                "address": holder["address"],
                "amount": income_amount,
                "tx_hash": r.result.get("hash"),
            })

        return results
```

---

## Transfer Restrictions

### On-Chain Transfer Controls

```python
from xrpl.models import Clawback


async def enforce_transfer_restriction(
    issuer_wallet: Wallet,
    from_address: str,
    to_address: str,
    token_code: str,
    amount: str,
    reason: str,
) -> dict:
    """
    Clawback tokens from a holder who violated transfer restrictions
    (e.g., transferred to a non-KYC'd address via DEX workaround).
    """
    async with AsyncJsonRpcClient(XRPL_RPC) as client:
        from xrpl.asyncio.transaction import submit_and_wait
        tx = Clawback(
            account=issuer_wallet.address,
            amount={
                "currency": token_code,
                "issuer": from_address,
                "value": amount,
            },
        )
        result = await submit_and_wait(tx, client, issuer_wallet)
        return {
            "action": "clawback",
            "holder": from_address,
            "amount": amount,
            "reason": reason,
            "tx_hash": result.result.get("hash"),
        }


async def check_transfer_eligibility(
    buyer_address: str,
    seller_address: str,
    token_code: str,
    issuer_address: str,
) -> dict:
    """
    Pre-transfer check: verify buyer is KYC'd and not sanctioned.
    Call this before facilitating any secondary market transfer.
    """
    async with AsyncJsonRpcClient(XRPL_RPC) as client:
        from xrpl.models import AccountLines

        # Check buyer trustline authorization
        buyer_lines = await client.request(
            AccountLines(account=buyer_address, peer=issuer_address)
        )
        buyer_authorized = False
        buyer_frozen = False
        for line in buyer_lines.result.get("lines", []):
            if line["currency"] == token_code:
                buyer_authorized = line.get("authorized", False)
                buyer_frozen = line.get("freeze", False)
                break

        # Check seller trustline
        seller_lines = await client.request(
            AccountLines(account=seller_address, peer=issuer_address)
        )
        seller_frozen = False
        for line in seller_lines.result.get("lines", []):
            if line["currency"] == token_code:
                seller_frozen = line.get("freeze", False)
                break

        eligible = buyer_authorized and not buyer_frozen and not seller_frozen
        return {
            "eligible": eligible,
            "buyer_authorized": buyer_authorized,
            "buyer_frozen": buyer_frozen,
            "seller_frozen": seller_frozen,
            "reason": (
                "OK" if eligible
                else "buyer not authorized" if not buyer_authorized
                else "buyer frozen" if buyer_frozen
                else "seller frozen"
            ),
        }
```

---

## Redemption Patterns

### Token Burn on Redemption

```python
async def redeem_rwa_tokens(
    investor_wallet: Wallet,
    issuer_address: str,
    token_code: str,
    amount: str,
    redemption_bank_ref: str,  # off-chain bank wire reference
) -> dict:
    """
    Investor sends tokens back to issuer to redeem for USD.
    Off-chain: issuer processes bank wire to investor.
    On-chain: tokens returned to issuer = burned from circulation.
    """
    async with AsyncJsonRpcClient(XRPL_RPC) as client:
        from xrpl.asyncio.transaction import submit_and_wait

        tx = Payment(
            account=investor_wallet.address,
            destination=issuer_address,
            amount={
                "currency": token_code,
                "issuer": issuer_address,
                "value": amount,
            },
            memos=[{
                "memo": {
                    "memo_type": "726564656d7074696f6e",  # "redemption"
                    "memo_data": redemption_bank_ref.encode().hex(),
                }
            }],
        )
        result = await submit_and_wait(tx, client, investor_wallet)
        return {
            "redeemed_tokens": amount,
            "currency": token_code,
            "redemption_ref": redemption_bank_ref,
            "tx_hash": result.result.get("hash"),
            "note": "Issuer will process USD wire within 3-5 business days",
        }
```

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

```python
import asyncio
from datetime import datetime, timedelta


async def schedule_lockup_release(
    issuer_wallet: Wallet,
    investor_address: str,
    token_code: str,
    lockup_days: int = 365,
) -> None:
    """
    Schedule a trustline unfreeze after Reg D lockup period.
    In production: use a job queue (Celery/Temporal) not asyncio.sleep.
    """
    release_date = datetime.utcnow() + timedelta(days=lockup_days)
    print(f"Lockup for {investor_address} until {release_date.isoformat()}")
    await asyncio.sleep(lockup_days * 86400)  # replace with job scheduler
    await unfreeze_individual_trustline(issuer_wallet, investor_address, token_code)
    print(f"Lockup released for {investor_address}")


async def unfreeze_individual_trustline(
    issuer_wallet: Wallet,
    investor_address: str,
    token_code: str,
) -> dict:
    async with AsyncJsonRpcClient(XRPL_RPC) as client:
        from xrpl.asyncio.transaction import submit_and_wait
        tx = TrustSet(
            account=issuer_wallet.address,
            limit_amount={
                "currency": token_code,
                "issuer": investor_address,
                "value": "0",
            },
            flags=0x00200000,  # tfClearFreeze
        )
        result = await submit_and_wait(tx, client, issuer_wallet)
        return result.result
```

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

```python
async def update_nav_on_chain(
    issuer_wallet: Wallet,
    token_code: str,
    nav_per_token_usd: float,
    total_nav_usd: float,
    valuation_date: str,        # ISO date string
    auditor_name: str,
) -> dict:
    """
    Publish NAV update to XRPL as a zero-value payment memo.
    This creates an immutable, timestamped NAV record.
    """
    import json
    nav_data = json.dumps({
        "nav_per_token": str(round(nav_per_token_usd, 6)),
        "total_nav_usd": str(round(total_nav_usd, 2)),
        "date": valuation_date,
        "auditor": auditor_name,
        "token": token_code,
    })

    async with AsyncJsonRpcClient(XRPL_RPC) as client:
        from xrpl.asyncio.transaction import submit_and_wait
        tx = Payment(
            account=issuer_wallet.address,
            destination=issuer_wallet.address,  # self-payment for memo
            amount="1",  # 1 drop minimum
            memos=[{
                "memo": {
                    "memo_type": "6e61765f757064617465",  # "nav_update"
                    "memo_data": nav_data.encode().hex(),
                }
            }],
        )
        result = await submit_and_wait(tx, client, issuer_wallet)
        return {
            "nav_per_token_usd": nav_per_token_usd,
            "total_nav_usd": total_nav_usd,
            "valuation_date": valuation_date,
            "tx_hash": result.result.get("hash"),
            "ledger_record": "immutable",
        }
```

---

## Secondary Market via XRPL DEX

```python
from xrpl.models import OfferCreate


async def list_rwa_token_for_sale(
    seller_wallet: Wallet,
    token_code: str,
    issuer_address: str,
    token_amount: str,
    price_rlusd_per_token: float,
) -> dict:
    """
    List RWA tokens for sale on the XRPL DEX.
    Price in RLUSD. Requires buyer to have authorized trustline.
    """
    rlusd_total = str(round(float(token_amount) * price_rlusd_per_token, 6))
    rlusd_issuer = "rMxCKbEDwqr76QuheSkemd63ovSYkPFBCV"

    async with AsyncJsonRpcClient(XRPL_RPC) as client:
        from xrpl.asyncio.transaction import submit_and_wait
        tx = OfferCreate(
            account=seller_wallet.address,
            taker_gets={
                "currency": token_code,
                "issuer": issuer_address,
                "value": token_amount,
            },
            taker_pays={
                "currency": "RLUSD",
                "issuer": rlusd_issuer,
                "value": rlusd_total,
            },
        )
        result = await submit_and_wait(tx, client, seller_wallet)
        return {
            "offer_sequence": result.result.get("Sequence"),
            "token_amount": token_amount,
            "price_rlusd_per_token": price_rlusd_per_token,
            "total_rlusd": rlusd_total,
            "tx_hash": result.result.get("hash"),
        }
```

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

## Cross-References

- `07-xrpl-clawback.md` — Clawback amendment technical details
- `08-xrpl-mpts.md` — Multi-Purpose Tokens for regulatory issuance
- `21-xrpl-token-model.md` — Core trustline and token model
- `24-xrpl-token-deployment.md` — Token deployment workflow
- `25-xrpl-token-security.md` — Security and audit checklist
- `52-xrpl-l1-reference.md` — Full L1 transaction reference
- `58-rlusd-operations.md` — RLUSD as payment/settlement currency for RWA income
- `47-xrpl-arweave-storage.md` — Permanent storage for audit documents
