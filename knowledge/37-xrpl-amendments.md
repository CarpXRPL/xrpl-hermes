# XRPL Amendments Catalog

## How Amendment Voting Works

Every proposed feature on the XRPL mainnet activates through the Amendment process:

1. A rippled build adds the code behind a **feature flag** (disabled by default)
2. Validators upgrade to the new version
3. Each validator signals YES or NO via `EnableAmendment` pseudo-transactions in every ledger
4. If **80%+ of trusted validators** vote YES for **two consecutive weeks**, the amendment activates
5. Once active, it cannot be deactivated — it is permanent ledger state

**Key fact:** The two-week window resets if support drops below 80%. An amendment stuck at 79% for months will never activate.

### Monitoring Voting State

```python
import xrpl
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import ServerInfo, FeatureAll

client = JsonRpcClient("https://xrplcluster.com")

# --- Check which amendments are currently in majority (near activation) ---
info = client.request(ServerInfo())
amend_info = info.result.get("info", {}).get("amendments", {})

print("=== In Majority (will activate if sustained for 2 weeks) ===")
for m in amend_info.get("majorities", []):
    maj = m["majority"]
    print(f"  ID: {maj['amendment'][:16]}...")
    print(f"  Since ledger: {maj.get('since', 'unknown')}")

# --- Full amendment ledger (all enabled, disabled, vetoed) ---
feats = client.request(FeatureAll())
enabled = []
pending = []
vetoed_list = []

for feat_id, feat in feats.result.get("features", {}).items():
    name = feat.get("name", feat_id[:12])
    if feat.get("enabled"):
        enabled.append(name)
    elif feat.get("vetoed"):
        vetoed_list.append(name)
    else:
        pending.append(name)

print(f"\nEnabled: {len(enabled)}, Pending: {len(pending)}, Vetoed: {len(vetoed_list)}")
```

```python
# --- Check specific amendment by ID ---
from xrpl.models.requests import Feature

def check_amendment_by_id(client, amendment_id: str) -> dict:
    resp = client.request(Feature(feature=amendment_id))
    feat = resp.result.get(amendment_id, {})
    return {
        "name": feat.get("name", "unknown"),
        "enabled": feat.get("enabled", False),
        "supported": feat.get("supported", False),
        "vetoed": feat.get("vetoed", False),
    }

# Example: Check AMM amendment
AMM_ID = "8CC0774A3BF66D1D22E76BBDA8E8A232E6B6313834301B3B23E8601196AE6455"
print(check_amendment_by_id(client, AMM_ID))
```

```python
# --- Poll for amendment activation (useful for testnet deploys) ---
import time

def wait_for_amendment(client, amendment_name: str, timeout_s: int = 300) -> bool:
    start = time.time()
    while time.time() - start < timeout_s:
        feats = client.request(FeatureAll())
        for feat_id, feat in feats.result.get("features", {}).items():
            if feat.get("name") == amendment_name and feat.get("enabled"):
                print(f"{amendment_name} is now enabled!")
                return True
        print(f"Waiting for {amendment_name}...")
        time.sleep(10)
    return False
```

---

## Complete Enabled Amendments (Mainnet, Chronological)

### 2016
| Amendment | ID (first 16 chars) | Date | Purpose |
|-----------|---------------------|------|---------|
| **MultiSign** | `4C97EBA926031A7C...` | 2016-06-27 | Multi-signature via SignerListSet; up to 8 signers per list |
| **TrustSetAuth** | `6781F8368C4771B0...` | 2016-07-19 | Trust line pre-authorization (RequireAuth pattern) |

### 2017
| Amendment | Date | Purpose |
|-----------|------|---------|
| **Escrow** | 2017-03-31 | Time-locked and crypto-condition escrow (EscrowCreate/Finish/Cancel) |
| **CryptoConditions** | 2017-03-31 | RFC 3 Crypto-Conditions standard support |

### 2018
| Amendment | Date | Purpose |
|-----------|------|---------|
| **PaymentChannel** | 2018-03-23 | Off-ledger micropayments via payment channels |
| **DepositAuth** | 2018-09-28 | Accounts can require pre-authorization before receiving payments |
| **fix1543** | 2018-10-25 | Fix flag validation for SignerListSet transactions |

### 2019–2020
| Amendment | Date | Purpose |
|-----------|------|---------|
| **Flow** | 2019-03-22 | Rewrite of core payment engine (replaced CalcFlow) |
| **FlowCross** | 2019-06-20 | Improved DEX offer crossing with partial fills |
| **FlowSortStrands** | 2019-09-09 | Path-finding across multiple liquidity strands |
| **Tickets** | 2019-07-02 | Parallel tx submission (TicketCreate + ticket_sequence=N, sequence=0) |
| **fix1781** | 2019-11-11 | Fix for trust line quality calculation edge case |
| **fixQualityUpperBound** | 2021-01-22 | Fix rounding in offer quality upper bound |
| **fixRmSmallIncreasedQty** | 2020-10-27 | Remove tiny residual offers from DEX after crossing |

### 2021
| Amendment | Date | Purpose |
|-----------|------|---------|
| **CheckCashMakesTrustLine** | 2020-11-23 | Check cashing creates trust line automatically |
| **XLS-20 (NFTs)** | 2021-10-31 | NFToken: mint, trade, burn, royalties on-chain |
| **fixRemoveNFTokenAutoTrustLine** | 2022-01-25 | Remove auto-trust-line creation bug in NFT trading |
| **NonFungibleTokensV1_1** | 2022-06-01 | NFT v1.1 fixes: offer cancel, burn, page management |

### 2022
| Amendment | Date | Purpose |
|-----------|------|---------|
| **DisallowIncoming** | 2022-12-13 | Accounts can block incoming payments, NFTs, checks |
| **Clawback (XLS-39)** | 2022-10-31 | Issuers can claw back tokens from trust lines |
| **fixNFTokenNegOffer** | 2022-09-01 | Fix negative-amount NFT offer edge case |
| **fixUniversalAMM** | 2023-04 | AMM infrastructure preparation patch |

### 2023
| Amendment | Date | Purpose |
|-----------|------|---------|
| **AMM (XLS-30)** | 2023-10-24 | Automated Market Maker pools (constant product formula) |
| **fixAMMOverflowOffer** | 2023-12 | Fix overflow in AMM offer crossing math |
| **XChainBridge (XLS-38)** | 2024-Q1 | Cross-chain bridge for XRP and IOU assets |

### 2024–2025
| Amendment | Date | Purpose |
|-----------|------|---------|
| **fixAMMv1_1** | 2024-Q2 | Fix AMM trading fee precision, LP token math |
| **MPT (XLS-33)** | 2024-12 | Multi-Purpose Tokens: compact on-ledger fungible tokens |
| **fixAMMv1_2** | 2025-Q1 | Additional AMM edge case corrections |
| **DID (XLS-40)** | 2025-Q1 | W3C Decentralized Identifiers on XRPL (DIDSet/DIDDelete) |
| **ExpandedSignerList** | 2025-Q2 | Increase max signers in SignerList from 8 to 32 |
| **Credentials (XLS-70)** | 2025-Q2 | On-chain verifiable credentials for DepositPreauth |

---

## Pending / In-Development

| Amendment | Stage | Purpose |
|-----------|-------|---------|
| **Hooks** | Draft | WebAssembly smart hooks (live on Xahau, pending mainnet) |
| **XLS-56 (Batch)** | Draft | Group up to 8 transactions into a single submission |
| **Remit** | In Voting | Combined payment + memo + destination tag in one tx |
| **PriceOracle** | In Voting | Native on-ledger price oracle aggregation |
| **fixEmptyDID** | Patch | Prevent empty DID documents from being stored |

---

## Amendment Activation on Devnet / Testnet

You can force-enable amendments on a private rippled instance for testing:

```cfg
# /etc/rippled/rippled.cfg
[amendment_majority_time]
# Reduce from 2-week default to 5 minutes for testing
5m

[features]
# Force-enable specific amendments on startup
AMM
MPT
DID
```

Or via RPC on a test node (only works on private networks with admin access):
```python
# Submit a "majority" vote for testing only — works on private networks
# where you control >80% of validators
from xrpl.models.requests import Submit

enable_request = {
    "method": "feature",
    "params": [{"feature": "AMM", "vetoed": False}]
}
# This RPC is admin-only and not available on public nodes
```

---

## Detecting Amendment-Dependent Code Paths

```python
# Pattern: gate features behind amendment check
from functools import lru_cache

@lru_cache(maxsize=1)
def get_enabled_amendments(client) -> set:
    feats = client.request(FeatureAll())
    return {
        feat.get("name")
        for feat in feats.result.get("features", {}).values()
        if feat.get("enabled")
    }

def can_use_amm(client) -> bool:
    return "AMM" in get_enabled_amendments(client)

def can_use_mpt(client) -> bool:
    return "MPT" in get_enabled_amendments(client)

# In code:
if can_use_amm(client):
    # Use AMMDeposit for liquidity
    pass
else:
    # Fall back to DEX offer placement
    pass
```

---

## Amendment Vetoing (Validator Operators)

Validator operators can configure their node to permanently vote NO:

```cfg
# /etc/rippled/rippled.cfg
[veto_amendments]
# One amendment ID per line
3012E8230864E95A58C60FD61430D7E1B4D3353195F2981DC12B0C7C0950FFAC
```

Vetoing means the node will never vote YES even if the operator upgrades the software. To unvote:
1. Remove the line from config
2. Restart rippled
3. Node will start voting YES automatically

---

## Tracking Real-Time

- **XRPSCAN Amendments:** https://xrpscan.com/amendments (shows vote counts + majority timers)
- **XRPl.org Amendments:** https://xrpl.org/known-amendments.html
- **GitHub Tracking Issues:** https://github.com/XRPLF/rippled/issues?q=label%3Aamendment

---

## Amendment Impact on Application Code

Each amendment can change transaction behavior or add new fields. Always gate code on amendment status:

```python
from functools import lru_cache
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import FeatureAll

@lru_cache(maxsize=1)
def enabled_amendments(client_url: str) -> frozenset:
    """Cache amendment set — refresh on new deployments."""
    client = JsonRpcClient(client_url)
    feats = client.request(FeatureAll())
    return frozenset(
        feat.get("name")
        for feat in feats.result.get("features", {}).values()
        if feat.get("enabled")
    )

def has_amendment(name: str, client_url: str = "https://xrplcluster.com") -> bool:
    return name in enabled_amendments(client_url)

# Usage in feature-gated code paths
if has_amendment("MPT"):
    # Use MPTokenIssuanceCreate for compact token issuance
    from xrpl.models.transactions import MPTokenIssuanceCreate
    # ...
else:
    # Fall back to IOU trust line model
    from xrpl.models.transactions import TrustSet
    # ...

if has_amendment("DID"):
    # Issue W3C DIDs on-ledger
    from xrpl.models.transactions import DIDSet
    # ...

if has_amendment("Credentials"):
    # Use DepositPreauth with credential filter
    # ...
    pass
```

---

## Critical Amendment IDs (For Direct Feature Lookup)

```python
# Known amendment IDs for direct lookup via Feature RPC
AMENDMENT_IDS = {
    "MultiSign":       "4C97EBA926031A7CF7D7B36FBF07DB2CAFF30FA2F86FBD3F7E83DDF17F51AA0",
    "Escrow":          "07D43DCE529B15A10827E5E04943B496762F9A88E3268269D69C44BE49E21104",
    "PaymentChannel":  "08DE7D96082187F6E6578530258C77FAABABE4C20474BDB82F04B021F1A68647",
    "Tickets":         "955DF3FA5891195A9DAEFA1DDC6BB244B545DDE1BAA84CBB25D5F12A8DA68A0C",
    "Flow":            "740352F2412A9909880C23A559FCECEDA3BE2126FED62FC7660D628A06927F11",
    "FlowCross":       "3012E8230864E95A58C60FD61430D7E1B4D3353195F2981DC12B0C7C0950FFAC",
    "NFT (XLS-20)":    "BF10AB701E07E0DC6DCE4B00BA89EDE3ABD97CC9A2A62FEC89A0498D28ECC3CE",
    "Clawback":        "56B241D7A43D40354D02A9DC4C8DF5C7A1F930D92A9035C4E12291B3CA3E1C2B",
    "AMM (XLS-30)":    "8CC0774A3BF66D1D22E76BBDA8E8A232E6B6313834301B3B23E8601196AE6455",
    "MPT (XLS-33)":    "67E4BD1C87F5FE4D32D15C0A98C01B22ABABDE3A1C37D9A7CEA0EF3D4A99D2E5",
    "DID (XLS-40)":    "C4483A1896579A7E1AFF0F7D22F3C023EE5B13A4F1E6B7E8DBB57F4A1FBD26F",
    "DepositAuth":     "F64E1EABBE79D55B3BB82020516CEC2C582A98A6B300094AB71B60D2DCA2FB8F",
    "DisallowIncoming":"878A53F7BD9E5D63AEC7F5D1B1ECB1C7DB37DFE5E0F44B4F84A71A65B8DF8B5",
}

def get_amendment_by_name(client, name: str) -> dict:
    """Look up an amendment by its well-known name."""
    amendment_id = AMENDMENT_IDS.get(name)
    if not amendment_id:
        return {"error": f"Unknown amendment name: {name}"}

    from xrpl.models.requests import Feature
    resp = client.request(Feature(feature=amendment_id))
    feat = resp.result.get(amendment_id, {})
    return {
        "name": name,
        "id": amendment_id,
        "enabled": feat.get("enabled", False),
        "supported": feat.get("supported", False),
        "vetoed": feat.get("vetoed", False),
    }
```

---

## Amendment Governance Notes

- **No on-chain governance voting by token holders** — only validator operators vote
- **Validators = infrastructure operators**, not economic stakeholders
- Ripple operates some validators but does not have majority control
- The **Unique Node List (UNL)** — the set of trusted validators — is maintained by the XRPL Foundation
- Any validator can veto any amendment indefinitely, but doing so may result in being removed from the UNL
- Fork risk: if a contentious amendment splits the validator set, the minority chain stops closing ledgers

### Proposing a New Amendment
1. Create GitHub issue on `XRPLF/XRPL-Standards` with XLS-N specification
2. Write rippled implementation + tests (open PR to `XRPLF/rippled`)
3. Get review from core developers and validators
4. Merge behind a feature flag
5. Get validators to upgrade their nodes
6. Monitor voting until 80% threshold + 2-week window achieved

---

## Related Files
- `knowledge/14-xrpl-consensus.md` — consensus protocol detail
- `knowledge/36-xrpl-xls-standards.md` — individual XLS specs
- `knowledge/43-xrpl-hooks-advanced.md` — Hooks/Xahau details
