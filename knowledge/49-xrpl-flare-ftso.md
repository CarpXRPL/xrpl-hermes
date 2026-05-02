# Flare Network + FTSO — XRP Price Oracles and F-Assets

## Overview

Flare is an EVM-compatible Layer-1 blockchain with two uniquely valuable built-in primitives:

1. **FTSO (Flare Time Series Oracle)** — Decentralized, manipulation-resistant price feeds for crypto, FX, and commodities without relying on third-party oracle networks like Chainlink
2. **State Connector** — Trustless cross-chain state verification protocol enabling Flare contracts to prove events happened on other chains (including XRPL)
3. **F-Assets** — Trustless representations of non-smart-contract assets (XRP, BTC, DOGE) on Flare EVM, backed by over-collateralized FLR

**Key use case for XRPL:** F-XRP brings XRP into Flare DeFi, FTSO provides decentralized XRP/USD price feeds, and State Connector enables trustless XRPL transaction proofs on Flare.

**Native token:** FLR (Flare mainnet), SGB (Songbird canary network)

---

## Architecture

### FTSO Architecture

```
Data Providers (150+)
   Submit XRP/USD price every ~3.5 min
         ↓
FTSO System Contract (0x1000...0002)
   - Collects all submissions
   - Calculates weighted median
   - Distributes rewards to accurate providers
         ↓
Consumer Contracts
   - Read getCurrentPrice("XRP/USD")
   - Use for DeFi, liquidations, derivatives
```

### State Connector Architecture

```
XRPL Transaction occurs
         ↓
Attestation providers observe XRPL
         ↓
Submit attestation proofs to State Connector
         ↓
Consensus reached (voting rounds ~90s)
         ↓
Proof available on Flare
         ↓
Smart contract can verify XRPL transaction happened
```

### F-Assets Architecture

```
User locks XRP on XRPL L1
      ↓
Flare agent over-collateralizes with FLR
      ↓
F-XRP minted on Flare EVM (1:1 with locked XRP)
      ↓
F-XRP used in Flare DeFi
      ↓
Redemption: burn F-XRP → unlock XRP on XRPL
```

---

## Songbird (Canary Network)

Songbird is Flare's pre-production canary network. All major features deploy to Songbird first:
- **Native token:** SGB
- **Chain ID:** 19 (Songbird mainnet)
- **RPC:** https://songbird-api.flare.network/ext/bc/C/rpc
- Same FTSO, State Connector, and F-Asset infrastructure as Flare mainnet
- Lower TVL and value — ideal for testing

---

## Key Contracts

### Flare Mainnet (Chain ID: 14)

| Contract | Address | Description |
|----------|---------|-------------|
| FTSO Registry | `0x1000000000000000000000000000000000000003` | Lookup FTSO contracts by symbol |
| Price Submitter | `0x1000000000000000000000000000000000000003` | Submit prices (data providers) |
| State Connector | `0x1000000000000000000000000000000000000001` | Cross-chain state proofs |
| WFLR | `0x1D80c49BbBCd1C0911344458cF0eA08C4b5D1e4a` | Wrapped FLR (ERC-20) |
| FLR Delegation | `0xC18A012f137DFa44c8f62b43B05Ba3eE89e93536` | Stake FLR for FTSO rewards |

### Songbird (Chain ID: 19)

| Contract | Address | Description |
|----------|---------|-------------|
| FTSO Registry | `0x1000000000000000000000000000000000000003` | Same address as Flare |
| State Connector | `0x1000000000000000000000000000000000000001` | Same address |
| WSGB | `0x02f0826ef6aD107Cfc861152B32B52fD11BaB9ED` | Wrapped SGB |

---

## Solidity: Reading FTSO Price Feeds

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IFtsoRegistry {
    function getFtso(uint256 _ftsoIndex) external view returns (address _ftsoAddress);
    function getFtsoIndex(string memory _symbol) external view returns (uint256);
    function getCurrentPriceWithDecimals(string memory _symbol)
        external view returns (uint256 _price, uint256 _timestamp, uint256 _decimals);
}

interface IFtso {
    function getCurrentPrice() external view returns (uint256 _price, uint256 _timestamp);
    function getCurrentPriceWithDecimals() external view returns (
        uint256 _price,
        uint256 _timestamp,
        uint256 _assetPriceUsdDecimals
    );
    function symbol() external view returns (string memory);
}

contract XRPPriceConsumer {
    address constant FTSO_REGISTRY = 0x1000000000000000000000000000000000000003;

    function getXRPUSD() external view returns (uint256 price, uint256 timestamp, uint256 decimals) {
        IFtsoRegistry registry = IFtsoRegistry(FTSO_REGISTRY);
        (price, timestamp, decimals) = registry.getCurrentPriceWithDecimals("XRP");
        // price is returned with 'decimals' decimal places
        // e.g., price=50000000, decimals=7 → $5.0000000
    }

    function getXRPUSDFloat() external view returns (uint256 priceInCents) {
        IFtsoRegistry registry = IFtsoRegistry(FTSO_REGISTRY);
        (uint256 price,, uint256 decimals) = registry.getCurrentPriceWithDecimals("XRP");
        // Convert to USD cents for integer math
        priceInCents = price * 100 / (10 ** decimals);
    }

    function getMultiplePrices(string[] memory symbols)
        external view returns (uint256[] memory prices) {
        IFtsoRegistry registry = IFtsoRegistry(FTSO_REGISTRY);
        prices = new uint256[](symbols.length);
        for (uint i = 0; i < symbols.length; i++) {
            (prices[i],,) = registry.getCurrentPriceWithDecimals(symbols[i]);
        }
    }
}
```

---

## Python: Query FTSO Prices via RPC

```python
import httpx
import asyncio
from web3 import Web3

FLARE_RPC = "https://flare-api.flare.network/ext/bc/C/rpc"
SONGBIRD_RPC = "https://songbird-api.flare.network/ext/bc/C/rpc"

# FTSO Registry ABI (simplified)
FTSO_REGISTRY_ABI = [
    {
        "inputs": [{"name": "_symbol", "type": "string"}],
        "name": "getCurrentPriceWithDecimals",
        "outputs": [
            {"name": "_price", "type": "uint256"},
            {"name": "_timestamp", "type": "uint256"},
            {"name": "_decimals", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

FTSO_REGISTRY_ADDRESS = "0x1000000000000000000000000000000000000003"

def get_ftso_price(symbol: str, network: str = "flare") -> dict:
    """
    Get current FTSO price for a symbol.
    Supported symbols: XRP, BTC, ETH, FLR, SGB, LTC, XLM, ADA, ALGO, etc.
    """
    rpc = FLARE_RPC if network == "flare" else SONGBIRD_RPC
    w3 = Web3(Web3.HTTPProvider(rpc))

    registry = w3.eth.contract(
        address=Web3.to_checksum_address(FTSO_REGISTRY_ADDRESS),
        abi=FTSO_REGISTRY_ABI
    )

    price, timestamp, decimals = registry.functions.getCurrentPriceWithDecimals(symbol).call()

    # Convert to human-readable float
    price_float = price / (10 ** decimals)

    return {
        "symbol": symbol,
        "price_usd": price_float,
        "raw_price": price,
        "decimals": decimals,
        "timestamp": timestamp,
        "network": network
    }

def get_xrp_price() -> dict:
    """Convenience function for XRP/USD price."""
    return get_ftso_price("XRP", "flare")

def get_multiple_ftso_prices(symbols: list, network: str = "flare") -> dict:
    """Get FTSO prices for multiple symbols efficiently."""
    rpc = FLARE_RPC if network == "flare" else SONGBIRD_RPC
    w3 = Web3(Web3.HTTPProvider(rpc))
    registry = w3.eth.contract(
        address=Web3.to_checksum_address(FTSO_REGISTRY_ADDRESS),
        abi=FTSO_REGISTRY_ABI
    )

    results = {}
    for symbol in symbols:
        try:
            price, timestamp, decimals = registry.functions.getCurrentPriceWithDecimals(symbol).call()
            results[symbol] = {
                "price_usd": price / (10 ** decimals),
                "timestamp": timestamp
            }
        except Exception as e:
            results[symbol] = {"error": str(e)}

    return results

# Get XRP and BTC prices
prices = get_multiple_ftso_prices(["XRP", "BTC", "ETH", "FLR"])
print(f"XRP/USD: ${prices['XRP']['price_usd']:.4f}")
print(f"BTC/USD: ${prices['BTC']['price_usd']:,.2f}")
```

---

## Python: Monitor FTSO Price Feeds

```python
import asyncio
import httpx
from web3 import Web3
from datetime import datetime

async def monitor_xrp_price_changes(
    alert_threshold_pct: float = 5.0,
    poll_interval_seconds: int = 210  # ~3.5 min FTSO epoch
) -> None:
    """Monitor XRP/USD price via FTSO and alert on large moves."""
    last_price = None
    w3 = Web3(Web3.HTTPProvider(FLARE_RPC))
    registry = w3.eth.contract(
        address=Web3.to_checksum_address(FTSO_REGISTRY_ADDRESS),
        abi=FTSO_REGISTRY_ABI
    )

    while True:
        try:
            price, _, decimals = registry.functions.getCurrentPriceWithDecimals("XRP").call()
            current_price = price / (10 ** decimals)
            now = datetime.utcnow().isoformat()

            if last_price is not None:
                change_pct = abs(current_price - last_price) / last_price * 100
                direction = "↑" if current_price > last_price else "↓"

                if change_pct >= alert_threshold_pct:
                    print(f"[ALERT] {now} XRP {direction} {change_pct:.2f}%: ${last_price:.4f} → ${current_price:.4f}")
                else:
                    print(f"[{now}] XRP/USD: ${current_price:.4f} ({direction}{change_pct:.2f}%)")
            else:
                print(f"[{now}] XRP/USD: ${current_price:.4f} (initial)")

            last_price = current_price

        except Exception as e:
            print(f"Error reading FTSO: {e}")

        await asyncio.sleep(poll_interval_seconds)

async def get_ftso_price_history(
    symbol: str = "XRP",
    epochs: int = 10
) -> list:
    """
    Fetch historical FTSO price data via Flare explorer API.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://flare-explorer.flare.network/api",
            params={
                "module": "stats",
                "action": "ftso_prices",
                "symbol": symbol,
                "limit": epochs
            }
        )
        return response.json().get("result", [])
```

---

## Python: State Connector (XRPL Transaction Proof)

```python
from web3 import Web3

STATE_CONNECTOR_ABI = [
    {
        "inputs": [
            {"name": "_attestationType", "type": "bytes32"},
            {"name": "_sourceId", "type": "bytes32"},
            {"name": "_requestBody", "type": "bytes"}
        ],
        "name": "requestAttestations",
        "outputs": [],
        "type": "function"
    },
    {
        "inputs": [{"name": "_merkleProof", "type": "bytes32[]"}, {"name": "_data", "type": "tuple"}],
        "name": "verifyPayment",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    }
]

STATE_CONNECTOR_ADDRESS = "0x1000000000000000000000000000000000000001"

def request_xrpl_payment_attestation(
    w3: Web3,
    sender_account,
    xrpl_tx_hash: str
) -> dict:
    """
    Request State Connector attestation for an XRPL payment.
    This proves to Flare contracts that an XRPL payment occurred.
    """
    state_connector = w3.eth.contract(
        address=Web3.to_checksum_address(STATE_CONNECTOR_ADDRESS),
        abi=STATE_CONNECTOR_ABI
    )

    # Attestation type for XRPL payment
    PAYMENT_ATTESTATION_TYPE = Web3.keccak(text="Payment")[:32]
    XRPL_SOURCE_ID = Web3.keccak(text="XRPL")[:32]

    # Encode the XRPL tx hash as request body
    request_body = bytes.fromhex(xrpl_tx_hash.replace("0x", ""))

    tx = state_connector.functions.requestAttestations(
        PAYMENT_ATTESTATION_TYPE,
        XRPL_SOURCE_ID,
        request_body
    ).build_transaction({
        "from": sender_account.address,
        "gas": 200000,
        "nonce": w3.eth.get_transaction_count(sender_account.address)
    })

    signed = w3.eth.account.sign_transaction(tx, sender_account.key)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    return {
        "attestation_request_tx": tx_hash.hex(),
        "xrpl_tx_hash": xrpl_tx_hash,
        "status": "pending",
        "note": "Wait ~90 seconds for attestation round to complete"
    }
```

---

## Python: F-Assets (F-XRP)

```python
import httpx

FASSETS_API = "https://fassets.flare.network/api"

async def get_fxrp_status() -> dict:
    """Get current F-XRP system status."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{FASSETS_API}/fasset/FXRP/status")
        return response.json()

async def get_fxrp_agents() -> list:
    """List active F-XRP minting agents."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{FASSETS_API}/fasset/FXRP/agents")
        return response.json().get("agents", [])

async def get_fxrp_collateral_ratio() -> dict:
    """Get current collateralization ratio for F-XRP."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{FASSETS_API}/fasset/FXRP/collateral")
        data = response.json()

    return {
        "total_minted": data.get("totalMinted"),
        "total_collateral_flr": data.get("totalCollateralFLR"),
        "collateral_ratio": data.get("collateralRatio"),
        "min_collateral_ratio": data.get("minCollateralRatio"),
        "liquidation_ratio": data.get("liquidationRatio")
    }

async def request_fxrp_minting(
    lots: int,
    agent_address: str,
    xrpl_address: str
) -> dict:
    """
    Request F-XRP minting. User will need to send XRP to the agent's XRPL address.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{FASSETS_API}/fasset/FXRP/mint",
            json={
                "lots": lots,
                "agentAddress": agent_address,
                "userXrplAddress": xrpl_address
            }
        )
        return response.json()
```

---

## JSON: FTSO Price Response Structure

```json
{
  "symbol": "XRP",
  "price": 50000000,
  "decimals": 7,
  "timestamp": 1714348800,
  "epoch": 4829,
  "price_usd": 5.0,
  "providers_count": 87,
  "median_price": 50000000,
  "low_price": 49800000,
  "high_price": 50200000
}
```

---

## FTSO Available Price Feeds

| Symbol | Asset | Update Freq |
|--------|-------|-------------|
| XRP | XRP/USD | ~3.5 min |
| BTC | Bitcoin/USD | ~3.5 min |
| ETH | Ethereum/USD | ~3.5 min |
| FLR | Flare/USD | ~3.5 min |
| SGB | Songbird/USD | ~3.5 min |
| LTC | Litecoin/USD | ~3.5 min |
| XLM | Stellar/USD | ~3.5 min |
| ADA | Cardano/USD | ~3.5 min |
| ALGO | Algorand/USD | ~3.5 min |
| DOGE | Dogecoin/USD | ~3.5 min |

Check https://ftso.flare.network for the full current list. New feeds added periodically.

---

## LayerCake Bridge

LayerCake enables trustless FLR/SGB transfers between Flare and other chains:

```python
async def get_layercake_bridge_info() -> dict:
    """
    Get LayerCake bridge configuration.
    Bridge uses State Connector for trustless verification.
    """
    async with httpx.AsyncClient() as client:
        # Check Flare docs for actual LayerCake API
        response = await client.get("https://layercake.flare.network/api/v1/info")
        return response.json()
```

---

## Error Handling Patterns

```python
from web3.exceptions import ContractLogicError
from web3 import Web3

class FTSOError(Exception):
    pass

class FTSOPriceStaleError(FTSOError):
    pass

class FTSOSymbolNotFoundError(FTSOError):
    pass

def safe_get_ftso_price(symbol: str, max_age_seconds: int = 600) -> dict:
    """
    Get FTSO price with staleness check.
    FTSO updates every ~3.5 min; prices older than 10 min may be stale.
    """
    import time

    try:
        result = get_ftso_price(symbol)
    except ContractLogicError as e:
        if "symbol not found" in str(e).lower():
            raise FTSOSymbolNotFoundError(f"Symbol {symbol} not in FTSO")
        raise FTSOError(f"FTSO contract error: {e}")
    except Exception as e:
        raise FTSOError(f"Failed to read FTSO price: {e}")

    # Check price freshness
    age_seconds = time.time() - result["timestamp"]
    if age_seconds > max_age_seconds:
        raise FTSOPriceStaleError(
            f"FTSO {symbol} price is {age_seconds:.0f}s old (max {max_age_seconds}s)"
        )

    return result

def get_xrp_price_with_fallback() -> float:
    """Get XRP price, falling back to Songbird FTSO if Flare fails."""
    for network in ["flare", "songbird"]:
        try:
            result = get_ftso_price("XRP", network)
            return result["price_usd"]
        except FTSOError:
            continue

    raise FTSOError("Could not get XRP price from any FTSO network")
```

---

## Practical Workflow: Use FTSO in XRPL Price Bot

```python
import asyncio
from web3 import Web3

async def xrpl_price_monitoring_bot():
    """
    Monitor XRP price from Flare FTSO and trigger XRPL actions on large moves.
    """
    w3 = Web3(Web3.HTTPProvider(FLARE_RPC))
    registry = w3.eth.contract(
        address=Web3.to_checksum_address(FTSO_REGISTRY_ADDRESS),
        abi=FTSO_REGISTRY_ABI
    )

    price_history = []
    ALERT_THRESHOLD = 10.0  # alert if > 10% move in 30 minutes

    while True:
        try:
            price, timestamp, decimals = registry.functions.getCurrentPriceWithDecimals("XRP").call()
            xrp_usd = price / (10 ** decimals)

            price_history.append({"price": xrp_usd, "timestamp": timestamp})
            # Keep last 10 epochs (~35 minutes)
            price_history = price_history[-10:]

            if len(price_history) >= 2:
                oldest = price_history[0]["price"]
                pct_change = (xrp_usd - oldest) / oldest * 100

                print(f"XRP/USD: ${xrp_usd:.4f} | 30m change: {pct_change:+.2f}%")

                if abs(pct_change) >= ALERT_THRESHOLD:
                    direction = "SURGE" if pct_change > 0 else "DROP"
                    print(f"⚠️  XRP {direction}: {pct_change:+.2f}% in last 30 minutes!")
                    # Trigger XRPL action here (e.g., adjust offers, send alert)

        except Exception as e:
            print(f"Error: {e}")

        await asyncio.sleep(210)  # FTSO epoch ~3.5 minutes
```

---

## Network Configuration

### Flare Mainnet
- Chain ID: 14
- RPC: https://flare-api.flare.network/ext/bc/C/rpc
- Explorer: https://flare-explorer.flare.network
- Currency: FLR

### Songbird (Canary)
- Chain ID: 19
- RPC: https://songbird-api.flare.network/ext/bc/C/rpc
- Explorer: https://songbird-explorer.flare.network
- Currency: SGB

### MetaMask Setup

```javascript
// Add Flare to MetaMask
{
  chainId: "0xE",        // 14 in hex
  chainName: "Flare Mainnet",
  rpcUrls: ["https://flare-api.flare.network/ext/bc/C/rpc"],
  nativeCurrency: { name: "FLR", symbol: "FLR", decimals: 18 },
  blockExplorerUrls: ["https://flare-explorer.flare.network"]
}
```

---

## Resources

- Flare documentation: https://docs.flare.network
- FTSO dashboard: https://ftso.flare.network
- F-Assets documentation: https://docs.flare.network/tech/fassets
- State Connector docs: https://docs.flare.network/tech/state-connector
- Flare explorer: https://flare-explorer.flare.network
- Songbird explorer: https://songbird-explorer.flare.network

---

## Related Files

- `50-xrpl-evm-sidechain.md` — XRPL EVM Sidechain (alternative smart contract platform)
- `46-xrpl-axelar-bridge.md` — Axelar cross-chain bridge vs Flare's approach
- `52-xrpl-l1-reference.md` — XRPL L1 where XRP originates for F-XRP
- `55-xrpl-sidechain-interop.md` — Cross-chain interoperability patterns
