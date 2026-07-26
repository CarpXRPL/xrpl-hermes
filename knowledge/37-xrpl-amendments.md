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

## rippled 3.2.0 — release & node-operator note (live-checked 2026-06-16)

**rippled 3.2.0 is the latest release** (tagged 2026-06-15) —
`https://github.com/XRPLF/rippled/releases/tag/3.2.0`. It is largely a cleanup/modernization
release: it **retires** a large set of long-enabled legacy `fix*` amendments (their behavior is now
baked in) and includes source-level refactors. Per the release notes it also renames the C++
`ripple` namespace to `xrpl` and the `rippled` binary to `xrpld` — the rename follows **XLS-0095**,
with related file renames — so **node operators should read the release notes before upgrading**
rather than assuming a drop-in swap.

The `fixCleanup3_2_0` amendment in this line **bundles** several correctness fixes per the release
notes (e.g. precision/rounding for Single Asset Vaults and the Lending Protocol, a
`ValidPermissionedDEX` invariant fix, validation of non-canonical MPT amounts, a zero-`DomainID`
check for permissioned domains, and the new `AccountRootsDeletedClean` invariant). Like any
amendment it is inactive on mainnet until validators adopt it — see the live check below.

**GPG signing key (verbatim from the release notes):** *"Ripple has rotated the GPG key used to sign
`rippled` packages. If you have an existing installation, you should download and trust the new key to
prevent issues upgrading in the future."*

**Mainnet trails the release — verify live, don't assume.** Checked live 2026-06-16:
`python3 -m scripts.xrpl_tools server-info` returned `BuildVersion: 3.1.3` from the public cluster, and
amendments named in the 3.2.0 line (e.g. `fixCleanup3_2_0`) are **not yet on the live mainnet `feature`
table** — `amendment fixCleanup3_2_0` returns `UnknownAmendment` because mainnet nodes have not yet
upgraded. New amendments only become enabled through the usual validator-upgrade + 80%/2-week majority
process. Confirm the full new-amendment set in the official release notes; never trust a static list.

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
| **XChainBridge (XLS-38)** | Supported, not enabled on mainnet as of 2026-06-08 | Native XRPL bridge amendment; do not confuse with the XRPL EVM sidechain bridge |

### 2024–2026 live-status update

The table below is not a hand-written guess. It was refreshed from live XRPL mainnet `feature` RPC (`https://s1.ripple.com:51234`) and checked against XRPL.org Known Amendments during the 2026-06-08 release audit. Re-run `python3 scripts/xrpl_tools.py amendments` before publishing any future release.

| Amendment / Feature | Mainnet status | Feature ID | Builder impact |
|-----------|------|---------|---------|
| **AMMClawback** | Enabled | `726F944886BCDF7433203787E93DD9AA87FAB74DFE3AF4785BA03BEFC97ADA1F` | Tokens with clawback enabled can be used in AMMs; tooling may build AMM + clawback flows. |
| **fixAMMClawbackRounding** | Enabled | `5E9586DB3D765B4C5794658FB6BB385071E9838DF4016027E6E26820C8526724` | AMM/clawback accounting fixes are live. |
| **fixAMMv1_1 / v1_2 / v1_3** | Enabled | `35291ADD...`, `1E7ED950...`, `7CA70A76...` | AMM tooling should assume current mainnet behavior, not early AMM launch behavior. |
| **MPTokensV1 (XLS-33)** | Enabled | `950AE2EA4654E47F04AA8739C0B214E242097E802FD372D24047A89AB1F5EC38` | MPT builders are mainnet-relevant. Check live status before building. |
| **DID (XLS-40)** | Enabled | `DB432C3A09D9D5DFC7859F39AE5FF767ABC59AED0A9FB441E83B814D8946C109` | DIDSet/DIDDelete are mainnet concepts; add tools only after validating transaction model support. |
| **Credentials** | Enabled | `1CB67D082CF7D9102412D34258CEDB400E659352D3B207348889297A6D90F5EF` | Credential builders are mainnet-relevant and now live-gated by XRPL-Hermes. |
| **PriceOracle** | Enabled | `96FD2F293A519AE1DB6F8BED23E4AD9119342DA7CB6BAFD00953D16C54205D8B` | OracleSet builder is mainnet-relevant and live-gated. |
| **fixPriceOracleOrder** | Enabled | `FF2D1E13CF6D22427111B967BD504917F63A900CECD320D6FD3AC9FA90344631` | PriceOracle ordering fix is live. |
| **TokenEscrow** | Enabled | `138B968F25822EFBF54C00F97031221C47B1EAB8321D93C7C2AEAF85F04EC5DF` | Token escrow is live; add builder coverage before claiming full support. |
| **fixTokenEscrowV1** | Enabled | `32B8614321F7E070419115ABEAB1742EA20F3E3AF34432B5E2F474F8083260DC` | TokenEscrow fix is live. |
| **PermissionedDEX** | Enabled | `677E401A423E3708363A36BA8B3A7D019D21AC5ABD00387BDBEA6BDE4C91247E` | Permissioned DEX is live; tooling/docs need a dedicated workflow before public claims. |
| **PermissionedDomains** | Enabled | `A730EB18A9D4BB52502C898589558B4CCEB4BE10044500EE5581137A2E80E849` | Permissioned domain primitives are live. |
| **XRPFees** | Enabled | `93E516234E35E08CA689FA33A6D38E103881F8DCB53023F728C307AA89D515A7` | Fee docs should use current XRP fee behavior. |
| **Batch** | Supported, not enabled | `894646DD5284E97DECFE6674A6D6152686791C4A95F8C132CCA9BAF9E5812FB6` | Security-retired in XRPL-Hermes; `build-batch` is unregistered. |
| **PermissionDelegation** | Supported, not enabled | `AE6AB9028EEB7299EBB03C7CBCC3F2A4F5FBE00EA28B8223AA3118A0B436C1C5` | Do not document as production mainnet functionality. |
| **XChainBridge** | Supported, not enabled | `C98D98EE9616ACD36E81FDEB8D41D349BF5F1B41DD64A0ABC1FE9AA5EA267E9C` | XRPL L1 XChainBridge is not a mainnet builder path; XRPL EVM bridge docs must stay separate. |
| **DynamicMPT / LendingProtocol / SingleAssetVault** | Supported, not enabled | see live `amendments` tool | Research/devnet only unless status changes. |

---

## Pending / Not Mainnet-Enabled

| Feature | Stage from live mainnet check | Purpose |
|-----------|-------|---------|
| **Hooks on XRPL L1** | Not an enabled XRPL mainnet amendment | WebAssembly smart hooks are live on Xahau, not XRPL L1 mainnet. Keep Xahau workflows separate. |
| **Batch** | Supported by servers, not enabled | Grouping concept only; XRPL-Hermes security-retired and unregistered its builder. |
| **PermissionDelegation** | Supported by servers, not enabled | Delegated account permissions; do not use for production mainnet claims yet. |
| **XChainBridge** | Supported by servers, not enabled | Native XRPL bridge amendment is not mainnet-enabled. Do not confuse with XRPL EVM sidechain bridge tooling. |
| **DynamicMPT / LendingProtocol / SingleAssetVault** | Supported by servers, not enabled | Treat as research/devnet until enabled. |

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

## Tracking Current Status

- Use Hermes `amendments` / `amendment NAME` against a current validated XRPL node.
- Cross-check [XRPL.org Known Amendments](https://xrpl.org/known-amendments.html) and current XRPLF/rippled release material.
- Third-party explorer amendment pages are uncertified external context.

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
    "MultiSign":       "4C97EBA926031A7CF7D7B36FDE3ED66DDA5421192D63DE53FFB46E43B9DC8373",
    "Escrow":          "07D43DCE529B15A10827E5E04943B496762F9A88E3268269D69C44BE49E21104",
    "PayChan":         "08DE7D96082187F6E6578530258C77FAABABE4C20474BDB82F04B021F1A68647",
    "TicketBatch":     "955DF3FA5891195A9DAEFA1DDC6BB244B545DDE1BAA84CBB25D5F12A8DA68A0C",
    "Flow":            "740352F2412A9909880C23A559FCECEDA3BE2126FED62FC7660D628A06927F11",
    "FlowCross":       "3012E8230864E95A58C60FD61430D7E1B4D3353195F2981DC12B0C7C0950FFAC",
    "NonFungibleTokensV1_1 (XLS-20)": "32A122F1352A4C7B3A6D790362CC34749C5E57FCE896377BFDC6CCD14F6CD627",
    "Clawback":        "56B241D7A43D40354D02A9DC4C8DF5C7A1F930D92A9035C4E12291B3CA3E1C2B",
    "AMM (XLS-30)":    "8CC0774A3BF66D1D22E76BBDA8E8A232E6B6313834301B3B23E8601196AE6455",
    "MPTokensV1 (XLS-33)": "950AE2EA4654E47F04AA8739C0B214E242097E802FD372D24047A89AB1F5EC38",
    "DID (XLS-40)":    "DB432C3A09D9D5DFC7859F39AE5FF767ABC59AED0A9FB441E83B814D8946C109",
    "DepositAuth":     "F64E1EABBE79D55B3BB82020516CEC2C582A98A6BFE20FBE9BB6A0D233418064",
    "DisallowIncoming":"47C3002ABA31628447E8E9A8B315FAA935CE30183F9A9B86845E469CA2CDC3DF",
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
