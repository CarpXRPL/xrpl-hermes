# XLS Standards Deep Dive

## What XLS Means
XLS (XRPL Ledger Standards) are the formal specification process for new on-ledger features. Each standard follows the lifecycle: **Draft → Last Call → Approved → Implemented → Enabled by Amendment**. Standards are proposed as GitHub issues on the `XRPLF/XRPL-Standards` repo. An Amendment activates the standard on the live network once 80%+ of trusted validators vote YES for two consecutive weeks.

Tracking active proposals: https://github.com/XRPLF/XRPL-Standards/issues

---

## Querying Amendment / Feature Status with xrpl-py

```python
import xrpl
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import ServerInfo, FeatureAll

client = JsonRpcClient("https://xrplcluster.com")

# --- Method 1: server_info gives current amendment majority status ---
info = client.request(ServerInfo())
amendments = info.result.get("info", {}).get("amendments", {})
majorities = amendments.get("majorities", [])

print("Currently in majority (awaiting activation):")
for m in majorities:
    maj = m["majority"]
    print(f"  {maj['amendment']}: {maj.get('count', '?')} validators, since ledger {maj.get('since', '?')}")

# --- Method 2: feature endpoint lists all known amendments ---
features = client.request(FeatureAll())
for feat_id, feat_data in features.result.get("features", {}).items():
    name = feat_data.get("name", feat_id[:8])
    enabled = feat_data.get("enabled", False)
    supported = feat_data.get("supported", False)
    vetoed = feat_data.get("vetoed", False)
    print(f"  {'✅' if enabled else '⏳'} {name} — enabled={enabled}, vetoed={vetoed}")
```

```python
# Check if a specific amendment is active
def amendment_enabled(client, amendment_name: str) -> bool:
    features = client.request(FeatureAll())
    for feat_id, feat_data in features.result.get("features", {}).items():
        if feat_data.get("name") == amendment_name:
            return feat_data.get("enabled", False)
    return False

is_amm_live = amendment_enabled(client, "AMM")
is_mpt_live = amendment_enabled(client, "MPT")
print(f"AMM: {is_amm_live}, MPT: {is_mpt_live}")
```

---

## XLS-20: Non-Fungible Tokens (NFTs)

**Status:** Enabled Oct 2021  
**Amendment ID:** `BF10AB701E07E0DC6DCE4B00BA89EDE3ABD97CC9A2A62FEC89A0498D28ECC3CE`

### NFToken Flags (bitfield on NFTokenMint)
| Flag Name | Hex Value | Decimal | Meaning |
|-----------|-----------|---------|---------|
| `lsfBurnable` | `0x0001` | 1 | Issuer can burn the NFT |
| `lsfOnlyXRP` | `0x0002` | 2 | Can only be sold/bought for XRP |
| `lsfTrustLine` | `0x0004` | 4 | Automatic trustlines for non-XRP sales |
| `lsfTransferable` | `0x0008` | 8 | Can be transferred to others |

```python
from xrpl.models.transactions import NFTokenMint
import xrpl.utils

# Combine flags: Burnable + OnlyXRP + Transferable
FLAGS = 0x0001 | 0x0002 | 0x0008  # = 11

mint = NFTokenMint(
    account="rMinter...",
    nftoken_taxon=42,           # Collection taxon (32-bit)
    flags=FLAGS,
    transfer_fee=5000,          # 5000 = 5% royalty (max 50000 = 50%)
    uri=xrpl.utils.str_to_hex("ipfs://QmXyz..."),  # Max 256 bytes hex-encoded
    # NOTE: sequence=0 when using ticket_sequence
)
```

### NFToken ID Anatomy (256-bit)
```
Bit 255-240: Flags         (16 bits)
Bit 239-224: TransferFee   (16 bits, 0-50000)
Bit 223-64:  Issuer        (160 bits, account ID)
Bit 63-32:   Taxon XOR'd   (32 bits, obfuscated)
Bit 31-0:    Sequence      (32 bits, issuer's seq)
```

```python
def parse_nft_id(nft_id_hex: str) -> dict:
    """Decode an NFToken ID into its components."""
    nft_bytes = bytes.fromhex(nft_id_hex)
    flags = int.from_bytes(nft_bytes[0:2], 'big')
    transfer_fee = int.from_bytes(nft_bytes[2:4], 'big')
    issuer_bytes = nft_bytes[4:24]
    taxon_scrambled = int.from_bytes(nft_bytes[24:28], 'big')
    seq = int.from_bytes(nft_bytes[28:32], 'big')

    import xrpl.core.keypairs
    issuer = xrpl.core.keypairs.encode_classic_address(issuer_bytes)
    # XOR with ciphered taxon (XRPL uses XOR obfuscation)
    MAGIC = 0x96963E6F  # Scramble constant
    taxon = taxon_scrambled ^ (MAGIC * seq & 0xFFFFFFFF)

    return {
        "flags": flags,
        "transfer_fee_pct": transfer_fee / 1000,
        "issuer": issuer,
        "taxon": taxon,
        "sequence": seq,
    }
```

### NFTokenPage Storage Model
- Each account has 0 or more `NFTokenPage` ledger objects
- Each page holds 16–32 NFTs sorted by NFToken ID
- First page costs 0.2 XRP reserve; each additional page costs 0.2 XRP
- Pages merge/split automatically as NFTs are added/removed

---

## XLS-30: Automated Market Maker (AMM)

**Status:** Enabled Oct 2023  
**Amendment ID:** `8CC0774A3BF66D1D22E76BBDA8E8A232E6B6313834301B3B23E8601196AE6455`

### AMM Math
The XRPL AMM uses the **constant product formula**: `x * y = k`

Pool price: `price = pool_token_B / pool_token_A`

Trading fee is deducted from input before the swap: `effective_input = input * (1 - fee/100000)`

```python
from xrpl.models.transactions import AMMCreate, AMMDeposit, AMMWithdraw, AMMBid, AMMVote
from xrpl.models.amounts import IssuedCurrencyAmount

# Create an AMM pool: XRP/USD
create = AMMCreate(
    account="rCreator...",
    amount=xrpl.utils.xrp_to_drops("10000"),          # 10,000 XRP
    amount2=IssuedCurrencyAmount(
        currency="USD",
        issuer="rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B",    # Bitstamp
        value="5000",                                   # 5,000 USD
    ),
    trading_fee=500,   # 500 = 0.5% trading fee (max 1000 = 1%)
)
```

```python
from xrpl.models.requests import AMMInfo

# Get current AMM state
amm_info = client.request(AMMInfo(
    asset={"currency": "XRP"},
    asset2={
        "currency": "USD",
        "issuer": "rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B",
    }
))
pool = amm_info.result["amm"]
print("AMM Pool state:")
print(f"  XRP:  {int(pool['amount']) / 1e6:.2f}")
print(f"  USD:  {pool['amount2']['value']}")
print(f"  LP tokens: {pool['lp_token']['value']}")
print(f"  Fee: {pool['trading_fee'] / 10:.1f} bps")

# Calculate spot price (XRP per USD)
xrp_drops = int(pool['amount'])
usd_value = float(pool['amount2']['value'])
spot_price = (xrp_drops / 1e6) / usd_value
print(f"  Spot: {spot_price:.4f} XRP/USD")
```

### AMMBid — Auction Slot for Fee Discounts
```python
# Bid for the 24-hour auction slot (fee discount for holder)
bid = AMMBid(
    account="rBidder...",
    asset={"currency": "XRP"},
    asset2={
        "currency": "USD",
        "issuer": "rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B",
    },
    bid_min=IssuedCurrencyAmount(
        currency="03930D02208264E2E40EC1B0C09E4DB96EE197B1",  # LP token
        issuer="rAMMPool...",
        value="50",   # Minimum bid in LP tokens
    ),
)
```

### LP Token Formula
```
LP_minted = LP_total * sqrt(deposit_A/pool_A * deposit_B/pool_B)
```
For single-asset deposits, the formula adds a swap component automatically.

---

## XLS-39: Clawback

**Status:** Enabled Oct 2022  
**Amendment ID:** `56B241D7A43D40354D02A9DC4C8DF5C7A1F930D92A9035C4E12291B3CA3E1C2B`

### Setup & Use
```python
from xrpl.models.transactions import AccountSet, Clawback
from xrpl.models.transactions.account_set import AccountSetFlag
from xrpl.models.amounts import IssuedCurrencyAmount

# Step 1: Enable clawback on account (one-time, irreversible)
# Once set, DefaultRipple CANNOT be enabled on this account
enable_clawback = AccountSet(
    account="rIssuer...",
    set_flag=AccountSetFlag.ASF_ALLOW_TRUSTLINE_CLAWBACK,
)

# Step 2: Claw back tokens from a holder
claw = Clawback(
    account="rIssuer...",
    amount=IssuedCurrencyAmount(
        currency="TOKEN",
        issuer="rHolder...",   # NOTE: issuer field = the HOLDER for clawback
        value="1000",          # Amount to claw back
    ),
)
```

### Clawback Constraints
- Cannot clawback if the trust line is frozen globally by issuer
- Cannot clawback more than the holder has
- `lsfAllowTrustLineClawback` flag is irreversible — once set, cannot be unset
- Setting this flag means you can NEVER enable `DefaultRipple` on the account
- Cannot clawback XRP (only IOU/token trust lines)

---

## XLS-33: Multi-Purpose Tokens (MPTs)

**Status:** Enabled Dec 2024  
**Amendment ID:** `67E4BD1C87F5FE4D32D15C0A98C01B22ABABDE3A1C37D9A7CEA0EF3D4A99D2E5`

### Why MPTs Over Trust Lines
| Feature | Trust Lines | MPTs |
|---------|------------|------|
| Reserve cost | 5 XRP per trustline | ~0.1 XRP per MPT issuance |
| Precision | Float (15 sig digits) | Fixed-point uint64 |
| Authorization | Manual TrustSet | MPTokenAuthorize |
| Ledger footprint | Large | Compact |
| Issuer control | Via flags | Via MPTokenIssuanceSet |

```python
from xrpl.models.transactions import (
    MPTokenIssuanceCreate, MPTokenIssuanceSet,
    MPTokenAuthorize, MPTokenIssuanceDestroy
)

# Create an MPT issuance
create_mpt = MPTokenIssuanceCreate(
    account="rIssuer...",
    maximum_amount="1000000000",     # Max supply (raw integer units)
    asset_scale=6,                   # 6 decimal places → divide by 1M for human value
    transfer_fee=200,                # 0.2% transfer fee (0-50000)
    flags=0x0002,                    # lsfMPTRequireAuth: holders must be authorized
    metadata="4D59544F4B454E",       # Hex-encoded metadata
)

# Authorize a holder to receive MPTs
authorize = MPTokenAuthorize(
    account="rHolder...",
    mpt_issuance_id="00000001...",   # From MPTokenIssuanceCreate result
)

# OR: Issuer authorizes (if MPTRequireAuth is set)
issuer_auth = MPTokenAuthorize(
    account="rIssuer...",
    mpt_issuance_id="00000001...",
    holder="rHolder...",
)
```

### MPT Issuance ID Structure
```
4 bytes: Sequence number (big-endian)
20 bytes: Issuer account ID
= 24 bytes total (48 hex characters)
```

---

## XLS-38: Federated Bridge (Cross-Chain)

**Status:** Last Call / Pending  
Enables native cross-chain assets between XRPL mainnet and sidechains (e.g., EVM sidechain) via a multi-sig federation. Key transaction types: `XChainCreateBridge`, `XChainCommit`, `XChainClaim`, `XChainAccountCreateCommit`.

```python
# Lock XRP on mainnet to bridge to EVM sidechain
from xrpl.models.transactions import XChainCommit

commit = XChainCommit(
    account="rSender...",
    xchain_bridge={
        "LockingChainDoor": "rHb9...",   # Mainnet door account
        "LockingChainIssue": {"currency": "XRP"},
        "IssuingChainDoor": "rBridge...",  # Sidechain door
        "IssuingChainIssue": {"currency": "XRP"},
    },
    xchain_sequence_num=1,
    amount=xrpl.utils.xrp_to_drops("100"),
    other_chain_destination="0xEVM_ADDRESS...",  # EVM recipient
)
```

---

## XLS-40: Hooks (Smart Contracts)

**Status:** Draft — live on Xahau network, pending for XRPL mainnet  
Hooks are small WebAssembly programs that execute on transaction acceptance. See `knowledge/43-xrpl-hooks-advanced.md` for full detail.

---

## XLS-60: Decentralized Identifiers (DID)

**Status:** Enabled 2025

```python
from xrpl.models.transactions import DIDSet, DIDDelete

# Create/update a DID document on XRPL
did_set = DIDSet(
    account="rOwner...",
    did_document="7B2240636F6E74657874...",  # Hex: {"@context": "https://www.w3.org/ns/did/v1"...}
    uri="https://did.example.com/rOwner",
    data="6578616D706C65",  # Arbitrary hex-encoded data
)

# The DID for this account is: did:xrpl:1:rOwner...
```

---

## Amendment Voting Mechanics (Deep)

```python
from xrpl.models.requests import Feature

def get_amendment_status(client, amendment_name: str) -> dict:
    """Full status report for one amendment."""
    features = client.request(FeatureAll())
    info = client.request(ServerInfo())

    # Find by name in features
    target = None
    for feat_id, feat in features.result.get("features", {}).items():
        if feat.get("name") == amendment_name:
            target = {"id": feat_id, **feat}
            break

    if not target:
        return {"error": f"Amendment '{amendment_name}' not found"}

    # Check if it has a current majority
    majorities = (
        info.result.get("info", {})
        .get("amendments", {})
        .get("majorities", [])
    )
    in_majority = any(
        m["majority"]["amendment"] == target["id"]
        for m in majorities
    )

    return {
        "name": amendment_name,
        "id": target["id"],
        "enabled": target.get("enabled", False),
        "supported": target.get("supported", False),
        "vetoed": target.get("vetoed", False),
        "in_majority": in_majority,
        "threshold_needed": "80% of trusted validators for 2 weeks",
    }

# Example
status = get_amendment_status(client, "AMM")
print(status)
```

### Vote Timeline
1. Validators signal intent via `EnableAmendment` pseudo-transaction
2. If 80%+ support → **majority** tracked in ledger state
3. If majority holds for **2 weeks** (≈ 336,000 ledgers) → amendment activates on next close
4. If majority drops below 80% → clock resets

### Vetoing an Amendment (Validator Operators)
Validator operators configure their node to vote NO on specific amendments:
```cfg
# /etc/rippled/rippled.cfg
[veto_amendments]
3012E8230864E95A58C60FD61430D7E1B4D3353195F2981DC12B0C7C0950FFAC  # ExpandedSignerList
```

---

## Related Files
- `knowledge/05-xrpl-amm.md` — AMM mechanics in detail
- `knowledge/06-xrpl-nfts.md` — NFT fundamentals
- `knowledge/07-xrpl-clawback.md` — clawback use cases
- `knowledge/08-xrpl-mpts.md` — MPT guide
- `knowledge/37-xrpl-amendments.md` — full amendment catalog
- `knowledge/43-xrpl-hooks-advanced.md` — Hooks / Xahau
