# RLUSD Operations — Ripple USD Stablecoin on XRPL

## Overview

**RLUSD** (Ripple USD) is a USD-backed stablecoin issued by Ripple Labs on both the XRP Ledger and the Ethereum network. It is fully collateralized by U.S. dollar deposits, U.S. government bonds, and other cash equivalents, with reserves audited by an independent third party.

**Issuer address (XRPL Mainnet):** `rMxCKbEDwqr76QuheSkemd63ovSYkPFBCV`
**Currency code:** `RLUSD`
**Asset class:** Regulated USD stablecoin (NYDFS BitLicense / trust charter)
**Redeemable:** 1 RLUSD = $1.00 USD via Ripple authorized partners

RLUSD uses native XRPL features — **trustlines, Clawback, freeze, and KYC gateway hooks** — to enforce compliance at the ledger level.

---

## Architecture

### Dual-Chain Issuance

```
USD Reserves (audited)
        │
        ├──► XRPL L1 RLUSD  (rMxCKbEDwqr76QuheSkemd63ovSYkPFBCV)
        │       Trustlines, DEX, AMM, cross-border payments
        │
        └──► Ethereum ERC-20 RLUSD (0x8292...)
                DeFi protocols, USDC-compatible liquidity pools
```

### XRPL-Side Trust Chain

```
Ripple Issuer (rMxC...)
    │  DefaultRipple=true
    │  RequireAuth=true          ← only authorized trustlines accepted
    │  GlobalFreeze capability   ← emergency halt
    │  Clawback enabled          ← regulatory recovery
    │
    ├── Market Maker (authorized trustline)
    ├── Exchange Partner (authorized trustline)
    └── End User (authorized trustline via KYC gateway)
```

---

## Compliance Architecture

### 1. RequireAuth (KYC Gating)

RLUSD issuer has `RequireAuth` flag set. Users cannot hold RLUSD without the issuer first authorizing their trustline. This enforces KYC/AML at the protocol level.

```python
import asyncio
from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.models import AccountSet, AccountSetFlag, TrustSet
from xrpl.wallet import Wallet

XRPL_RPC = "https://xrplcluster.com"
RLUSD_ISSUER = "rMxCKbEDwqr76QuheSkemd63ovSYkPFBCV"
RLUSD_CODE = "RLUSD"


async def authorize_trustline(issuer_wallet: Wallet, user_address: str) -> dict:
    """Authorize a user's RLUSD trustline after KYC approval."""
    async with AsyncJsonRpcClient(XRPL_RPC) as client:
        tx = TrustSet(
            account=issuer_wallet.address,
            limit_amount={
                "currency": RLUSD_CODE,
                "issuer": user_address,   # the counterparty being authorized
                "value": "0",
            },
            flags=0x00020000,  # tfSetfAuth — authorize the trustline
        )
        from xrpl.asyncio.transaction import submit_and_wait
        result = await submit_and_wait(tx, client, issuer_wallet)
        return result.result


async def check_trustline_authorized(user_address: str) -> bool:
    """Check whether a user's RLUSD trustline is authorized."""
    async with AsyncJsonRpcClient(XRPL_RPC) as client:
        from xrpl.models import AccountLines
        req = AccountLines(account=user_address, peer=RLUSD_ISSUER)
        resp = await client.request(req)
        lines = resp.result.get("lines", [])
        for line in lines:
            if line["currency"] == RLUSD_CODE:
                return line.get("authorized", False)
        return False


async def revoke_authorization(issuer_wallet: Wallet, user_address: str) -> dict:
    """Revoke a user's RLUSD authorization (account flagged / sanctioned)."""
    async with AsyncJsonRpcClient(XRPL_RPC) as client:
        tx = TrustSet(
            account=issuer_wallet.address,
            limit_amount={
                "currency": RLUSD_CODE,
                "issuer": user_address,
                "value": "0",
            },
            flags=0x00040000,  # tfClearfAuth — de-authorize
        )
        from xrpl.asyncio.transaction import submit_and_wait
        result = await submit_and_wait(tx, client, issuer_wallet)
        return result.result
```

### 2. Freeze Controls

RLUSD supports both individual trustline freeze and global freeze.

```python
from xrpl.models import AccountSet, AccountSetFlag, TrustSet


async def freeze_individual_trustline(
    issuer_wallet: Wallet, user_address: str
) -> dict:
    """Freeze a single user's RLUSD trustline (OFAC / court order)."""
    async with AsyncJsonRpcClient(XRPL_RPC) as client:
        tx = TrustSet(
            account=issuer_wallet.address,
            limit_amount={
                "currency": RLUSD_CODE,
                "issuer": user_address,
                "value": "0",
            },
            flags=0x00100000,  # tfSetFreeze
        )
        from xrpl.asyncio.transaction import submit_and_wait
        return (await submit_and_wait(tx, client, issuer_wallet)).result


async def unfreeze_individual_trustline(
    issuer_wallet: Wallet, user_address: str
) -> dict:
    """Unfreeze an individual trustline after clearance."""
    async with AsyncJsonRpcClient(XRPL_RPC) as client:
        tx = TrustSet(
            account=issuer_wallet.address,
            limit_amount={
                "currency": RLUSD_CODE,
                "issuer": user_address,
                "value": "0",
            },
            flags=0x00200000,  # tfClearFreeze
        )
        from xrpl.asyncio.transaction import submit_and_wait
        return (await submit_and_wait(tx, client, issuer_wallet)).result


async def activate_global_freeze(issuer_wallet: Wallet) -> dict:
    """Activate global freeze — halts ALL RLUSD transfers (emergency only)."""
    async with AsyncJsonRpcClient(XRPL_RPC) as client:
        tx = AccountSet(
            account=issuer_wallet.address,
            set_flag=AccountSetFlag.ASF_GLOBAL_FREEZE,
        )
        from xrpl.asyncio.transaction import submit_and_wait
        return (await submit_and_wait(tx, client, issuer_wallet)).result


async def deactivate_global_freeze(issuer_wallet: Wallet) -> dict:
    """Lift global freeze after emergency resolved."""
    async with AsyncJsonRpcClient(XRPL_RPC) as client:
        tx = AccountSet(
            account=issuer_wallet.address,
            clear_flag=AccountSetFlag.ASF_GLOBAL_FREEZE,
        )
        from xrpl.asyncio.transaction import submit_and_wait
        return (await submit_and_wait(tx, client, issuer_wallet)).result
```

### 3. Clawback (Regulatory Recovery)

RLUSD has **Clawback** enabled on the issuer. This allows Ripple to recover funds from a sanctioned or fraudulent account under court order.

```python
from xrpl.models import Clawback


async def clawback_rlusd(
    issuer_wallet: Wallet,
    holder_address: str,
    amount_str: str,
) -> dict:
    """
    Clawback RLUSD from a holder.

    amount_str: e.g. "500.00"
    Requires Clawback amendment enabled (live on mainnet).
    Requires issuer to have AllowTrustLineClawback flag set.
    """
    async with AsyncJsonRpcClient(XRPL_RPC) as client:
        tx = Clawback(
            account=issuer_wallet.address,
            amount={
                "currency": RLUSD_CODE,
                "issuer": holder_address,   # holder is the issuer field in clawback
                "value": amount_str,
            },
        )
        from xrpl.asyncio.transaction import submit_and_wait
        result = await submit_and_wait(tx, client, issuer_wallet)
        return result.result


async def check_clawback_enabled(issuer_address: str) -> bool:
    """Verify that Clawback is enabled on the RLUSD issuer account."""
    async with AsyncJsonRpcClient(XRPL_RPC) as client:
        from xrpl.models import AccountInfo
        req = AccountInfo(account=issuer_address, ledger_index="validated")
        resp = await client.request(req)
        flags = resp.result["account_data"].get("Flags", 0)
        # lsfAllowTrustLineClawback = 0x80000000
        return bool(flags & 0x80000000)
```

---

## KYC/AML Integration Patterns

### Architecture: Off-Chain KYC → On-Chain Authorization

```
User submits KYC docs
        │
    KYC Provider (Synaps / Jumio / Sumsub)
        │  webhook: kyc_approved(user_id, wallet_address)
        │
    Compliance Backend
        ├── Sanctions screening (OFAC / EU / UN lists)
        ├── PEP check
        ├── Risk scoring
        └── If approved → call authorize_trustline(user_wallet)
                         If denied  → log, reject, notify user
```

```python
import httpx
from typing import Optional


class RLUSDComplianceGateway:
    """Minimal KYC/AML gateway for RLUSD trustline management."""

    def __init__(self, issuer_wallet: Wallet, kyc_api_key: str):
        self.issuer = issuer_wallet
        self.kyc_api_key = kyc_api_key
        self._sanctions_cache: dict[str, bool] = {}

    async def screen_address(self, xrpl_address: str) -> dict:
        """
        Screen an XRPL address against sanctions lists.
        Uses Chainalysis / Elliptic API pattern (replace with your provider).
        """
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://api.chainalysis.com/api/risk/v2/entities/{xrpl_address}",
                headers={"Token": self.kyc_api_key},
                timeout=10.0,
            )
            data = resp.json()
            return {
                "address": xrpl_address,
                "risk": data.get("risk", "UNKNOWN"),
                "cluster": data.get("cluster", {}),
                "is_sanctioned": data.get("risk") == "SEVERE",
            }

    async def onboard_user(
        self, xrpl_address: str, kyc_session_id: str
    ) -> dict:
        """Full onboarding: KYC check → sanctions screen → authorize trustline."""
        # 1. Verify KYC session approved
        async with httpx.AsyncClient() as client:
            kyc_resp = await client.get(
                f"https://api.synaps.io/v4/session/{kyc_session_id}",
                headers={"Api-Key": self.kyc_api_key},
                timeout=10.0,
            )
            session = kyc_resp.json()

        if session.get("status") != "APPROVED":
            return {"success": False, "reason": "KYC not approved", "status": session.get("status")}

        # 2. Sanctions screen
        screen = await self.screen_address(xrpl_address)
        if screen["is_sanctioned"]:
            return {"success": False, "reason": "Sanctioned address", "risk": screen["risk"]}

        # 3. Authorize trustline
        result = await authorize_trustline(self.issuer, xrpl_address)
        return {
            "success": True,
            "address": xrpl_address,
            "tx_hash": result.get("hash"),
            "kyc_session": kyc_session_id,
        }
```

---

## Travel Rule Compliance

The **Travel Rule** (FATF Recommendation 16) requires Virtual Asset Service Providers (VASPs) to pass originator and beneficiary information for transfers ≥ $1,000 (USD equivalent). For RLUSD, this applies to institutional transfers.

### Travel Rule Pattern for RLUSD Transfers

```python
import json
from dataclasses import dataclass
from xrpl.models import Payment
from xrpl.utils import xrp_to_drops


@dataclass
class TravelRulePayload:
    """IVMS101-compatible Travel Rule data payload."""
    originator_name: str
    originator_address: str          # XRPL address
    originator_vasp_did: str         # DID of sending VASP
    originator_account_number: str   # internal account ID

    beneficiary_name: str
    beneficiary_address: str         # XRPL destination address
    beneficiary_vasp_did: str        # DID of receiving VASP

    amount_usd: float
    currency: str = "RLUSD"
    transfer_ref: str = ""           # internal reference ID


async def build_travel_rule_payment(
    sender_wallet: Wallet,
    destination: str,
    amount_rlusd: str,
    travel_payload: TravelRulePayload,
    destination_tag: Optional[int] = None,
) -> dict:
    """
    Build a RLUSD payment with Travel Rule data.

    Travel Rule data is sent out-of-band to the receiving VASP
    before or alongside the on-chain transaction.
    The on-chain tx uses the Memo field for the transfer reference only
    (NEVER include PII in Memo — it is public on-chain data).
    """
    # 1. Send IVMS101 payload to receiving VASP (off-chain)
    travel_rule_ref = await _send_ivms101_to_vasp(travel_payload)

    # 2. Build on-chain payment with reference only
    memo_data = json.dumps({"tr_ref": travel_rule_ref}).encode().hex()

    async with AsyncJsonRpcClient(XRPL_RPC) as client:
        tx = Payment(
            account=sender_wallet.address,
            destination=destination,
            amount={
                "currency": RLUSD_CODE,
                "issuer": RLUSD_ISSUER,
                "value": amount_rlusd,
            },
            destination_tag=destination_tag,
            memos=[{
                "memo": {
                    "memo_type": "747261766c5f72756c65",  # "travel_rule" hex
                    "memo_data": memo_data,
                }
            }],
        )
        from xrpl.asyncio.transaction import submit_and_wait
        result = await submit_and_wait(tx, client, sender_wallet)
        return {
            "tx_hash": result.result.get("hash"),
            "travel_rule_ref": travel_rule_ref,
            "amount": amount_rlusd,
            "destination": destination,
        }


async def _send_ivms101_to_vasp(payload: TravelRulePayload) -> str:
    """
    Send IVMS101 Travel Rule payload to receiving VASP.
    Uses Notabene / Sygna Bridge / VerifyVASP pattern.
    Returns: transfer_reference_id from receiving VASP.
    """
    ivms101 = {
        "originatorVasp": {"vasp": {"name": payload.originator_vasp_did}},
        "originator": {
            "originatorPersons": [{
                "naturalPerson": {
                    "name": [{"nameIdentifier": [{"primaryIdentifier": payload.originator_name}]}]
                }
            }],
            "accountNumber": [payload.originator_address],
        },
        "beneficiaryVasp": {"vasp": {"name": payload.beneficiary_vasp_did}},
        "beneficiary": {
            "beneficiaryPersons": [{
                "naturalPerson": {
                    "name": [{"nameIdentifier": [{"primaryIdentifier": payload.beneficiary_name}]}]
                }
            }],
            "accountNumber": [payload.beneficiary_address],
        },
        "transfer": {
            "virtualAsset": payload.currency,
            "transactionAmount": str(int(payload.amount_usd * 100)),
        },
    }
    # POST to your Travel Rule compliance provider
    # async with httpx.AsyncClient() as client:
    #     resp = await client.post("https://api.notabene.id/tf/simple/transfers", json=ivms101)
    #     return resp.json()["id"]
    return f"TR-{payload.transfer_ref or 'REF'}"
```

---

## Monitoring RLUSD Supply and Circulation

### Fetch Total RLUSD Supply

```python
async def get_rlusd_supply() -> dict:
    """
    Get total RLUSD in circulation on XRPL.
    XRPL tracks this via gateway_balances on the issuer account.
    """
    async with AsyncJsonRpcClient(XRPL_RPC) as client:
        from xrpl.models import GatewayBalances
        req = GatewayBalances(
            account=RLUSD_ISSUER,
            ledger_index="validated",
        )
        resp = await client.request(req)
        obligations = resp.result.get("obligations", {})
        rlusd_supply = obligations.get("RLUSD", "0")
        return {
            "issuer": RLUSD_ISSUER,
            "total_supply_rlusd": rlusd_supply,
            "all_obligations": obligations,
        }


async def get_rlusd_holders(limit: int = 200) -> list[dict]:
    """Paginate through all RLUSD trustline holders."""
    async with AsyncJsonRpcClient(XRPL_RPC) as client:
        from xrpl.models import AccountLines
        holders = []
        marker = None

        while True:
            req = AccountLines(
                account=RLUSD_ISSUER,
                limit=200,
                marker=marker,
            )
            resp = await client.request(req)
            lines = resp.result.get("lines", [])
            for line in lines:
                if line["currency"] == RLUSD_CODE and float(line["balance"]) != 0:
                    holders.append({
                        "address": line["account"],
                        "balance": line["balance"],
                        "authorized": line.get("authorized", False),
                        "frozen": line.get("freeze", False),
                    })
            marker = resp.result.get("marker")
            if not marker or len(holders) >= limit:
                break

        holders.sort(key=lambda h: float(h["balance"]), reverse=True)
        return holders


async def monitor_large_rlusd_transfers(threshold_rlusd: float = 10000.0) -> None:
    """
    Stream ledger transactions and alert on large RLUSD transfers.
    Useful for compliance monitoring and AML pattern detection.
    """
    from xrpl.asyncio.clients import AsyncWebsocketClient
    import json

    ws_url = "wss://xrplcluster.com"
    async with AsyncWebsocketClient(ws_url) as client:
        await client.send({
            "command": "subscribe",
            "streams": ["transactions"],
        })
        print(f"Monitoring RLUSD transfers ≥ {threshold_rlusd:,.2f}")

        async for msg in client:
            data = json.loads(msg) if isinstance(msg, str) else msg
            tx = data.get("transaction", {})

            if tx.get("TransactionType") != "Payment":
                continue

            amt = tx.get("Amount", {})
            if not isinstance(amt, dict):
                continue
            if amt.get("currency") != RLUSD_CODE:
                continue

            amount_rlusd = float(amt.get("value", 0))
            if amount_rlusd < threshold_rlusd:
                continue

            print(
                f"[ALERT] Large RLUSD transfer: "
                f"{amount_rlusd:,.2f} RLUSD | "
                f"{tx['Account']} → {tx.get('Destination', '?')} | "
                f"Hash: {data.get('transaction', {}).get('hash', '?')}"
            )
```

---

## RLUSD AMM Liquidity

RLUSD is available on XRPL's native AMM (XLS-30). Liquidity providers can deposit RLUSD/XRP or RLUSD/other-token pairs.

```python
from xrpl.models import AMMDeposit, AMMDepositFlag, AMMInfo


async def get_rlusd_xrp_amm_info() -> dict:
    """Get the RLUSD/XRP AMM pool info."""
    async with AsyncJsonRpcClient(XRPL_RPC) as client:
        req = AMMInfo(
            asset={"currency": "XRP"},
            asset2={
                "currency": RLUSD_CODE,
                "issuer": RLUSD_ISSUER,
            },
        )
        resp = await client.request(req)
        amm = resp.result.get("amm", {})
        return {
            "amm_account": amm.get("account"),
            "xrp_amount": amm.get("amount"),
            "rlusd_amount": amm.get("amount2", {}).get("value"),
            "lp_token": amm.get("lp_token"),
            "trading_fee": amm.get("trading_fee"),
        }


async def deposit_rlusd_xrp_amm(
    lp_wallet: Wallet,
    rlusd_amount: str,
    xrp_drops: str,
) -> dict:
    """
    Provide liquidity to the RLUSD/XRP AMM pool.
    Uses tfTwoAsset — deposit both sides proportionally.
    """
    async with AsyncJsonRpcClient(XRPL_RPC) as client:
        tx = AMMDeposit(
            account=lp_wallet.address,
            asset={"currency": "XRP"},
            asset2={
                "currency": RLUSD_CODE,
                "issuer": RLUSD_ISSUER,
            },
            amount=xrp_drops,
            amount2={
                "currency": RLUSD_CODE,
                "issuer": RLUSD_ISSUER,
                "value": rlusd_amount,
            },
            flags=AMMDepositFlag.TF_TWO_ASSET,
        )
        from xrpl.asyncio.transaction import submit_and_wait
        result = await submit_and_wait(tx, client, lp_wallet)
        return result.result
```

---

## Cross-Border Payment Pattern

RLUSD is designed as a bridge currency for institutional cross-border payments.

```python
async def build_cross_border_rlusd_payment(
    sender_wallet: Wallet,
    destination_address: str,
    destination_currency: str,
    destination_issuer: str,
    destination_amount: str,
    max_rlusd_spend: str,
) -> dict:
    """
    Send a cross-border payment using RLUSD as the bridge currency.
    Source → RLUSD → destination_currency (via XRPL path-finding).
    """
    async with AsyncJsonRpcClient(XRPL_RPC) as client:
        # 1. Find the best path
        from xrpl.models import RipplePathFind
        path_req = RipplePathFind(
            source_account=sender_wallet.address,
            source_currencies=[{
                "currency": RLUSD_CODE,
                "issuer": RLUSD_ISSUER,
            }],
            destination_account=destination_address,
            destination_amount={
                "currency": destination_currency,
                "issuer": destination_issuer,
                "value": destination_amount,
            },
        )
        path_resp = await client.request(path_req)
        alternatives = path_resp.result.get("alternatives", [])
        if not alternatives:
            return {"error": "No path found"}

        best_path = alternatives[0]

        # 2. Build cross-currency payment
        tx = Payment(
            account=sender_wallet.address,
            destination=destination_address,
            amount={
                "currency": destination_currency,
                "issuer": destination_issuer,
                "value": destination_amount,
            },
            send_max={
                "currency": RLUSD_CODE,
                "issuer": RLUSD_ISSUER,
                "value": max_rlusd_spend,
            },
            paths=best_path.get("paths_computed", []),
        )
        from xrpl.asyncio.transaction import submit_and_wait
        result = await submit_and_wait(tx, client, sender_wallet)
        return result.result
```

---

## Regulatory Compliance Checklist

### For RLUSD Issuers / VASPs

| Requirement | XRPL Mechanism | Status |
|---|---|---|
| KYC before holding | `RequireAuth` + trustline authorization | ✅ Native |
| AML screening | Off-chain (Chainalysis/Elliptic) + webhook | ✅ Pattern above |
| Sanction freeze | `TrustSet tfSetFreeze` | ✅ Native |
| Emergency halt | `AccountSet ASF_GLOBAL_FREEZE` | ✅ Native |
| Regulatory clawback | `Clawback` amendment | ✅ Live on mainnet |
| Travel Rule (FATF R16) | IVMS101 + Memo reference | ✅ Pattern above |
| Audit trail | XRPL immutable ledger | ✅ Native |
| Reserve attestation | Off-chain (third-party auditor) | External |

### For Exchanges Listing RLUSD

1. Obtain authorization from Ripple (commercial agreement)
2. Implement KYC/AML matching Ripple's compliance standards
3. Set up Travel Rule messaging with Notabene, Sygna, or VerifyVASP
4. Monitor for frozen trustlines before processing withdrawals
5. Subscribe to RLUSD issuer account for freeze/unfreeze events

---

## Useful Queries

```python
async def rlusd_full_status_report(user_address: str) -> dict:
    """Full compliance status for a user's RLUSD position."""
    async with AsyncJsonRpcClient(XRPL_RPC) as client:
        from xrpl.models import AccountLines, AccountInfo
        lines_req = AccountLines(account=user_address, peer=RLUSD_ISSUER)
        info_req = AccountInfo(account=user_address, ledger_index="validated")

        lines_resp = await client.request(lines_req)
        info_resp = await client.request(info_req)

        rlusd_line = None
        for line in lines_resp.result.get("lines", []):
            if line["currency"] == RLUSD_CODE:
                rlusd_line = line
                break

        return {
            "address": user_address,
            "has_trustline": rlusd_line is not None,
            "balance": rlusd_line["balance"] if rlusd_line else "0",
            "limit": rlusd_line["limit"] if rlusd_line else "0",
            "authorized": rlusd_line.get("authorized", False) if rlusd_line else False,
            "frozen_by_issuer": rlusd_line.get("freeze", False) if rlusd_line else False,
            "frozen_by_self": rlusd_line.get("freeze_peer", False) if rlusd_line else False,
            "xrp_balance": info_resp.result["account_data"]["Balance"],
        }
```

---

## Resources

- Ripple RLUSD page: https://ripple.com/rlusd
- RLUSD on XRPL explorer: https://livenet.xrpl.org/accounts/rMxCKbEDwqr76QuheSkemd63ovSYkPFBCV
- XRPL Clawback amendment: https://xrpl.org/clawback.html
- XRPL Freeze: https://xrpl.org/freezes.html
- XRPL RequireAuth: https://xrpl.org/authorized-trust-lines.html
- FATF Travel Rule: https://www.fatf-gafi.org/en/topics/virtual-assets.html
- IVMS101 standard: https://intervasp.org/
- Notabene Travel Rule: https://notabene.id
- Sygna Bridge: https://www.sygna.io

---

## Cross-References

- `02-xrpl-payments.md` — Payment transaction format and fields
- `05-xrpl-amm.md` — AMM deposit/withdraw for RLUSD liquidity
- `07-xrpl-clawback.md` — Clawback amendment details
- `21-xrpl-token-model.md` — Trustline model and token issuance
- `52-xrpl-l1-reference.md` — Full L1 transaction reference
- `59-rwa-tokenization.md` — Real-world asset tokenization (complementary compliance patterns)
