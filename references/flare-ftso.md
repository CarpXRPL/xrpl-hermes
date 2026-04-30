# Flare FTSO + Songbird — Complete Reference

## Flare Network
Flare is an EVM-compatible blockchain with built-in oracles (FTSO) and cross-chain interoperability. Native token: FLR.

### FTSO (Flare Time Series Oracle)
- Decentralized price feeds for crypto, FX, commodities
- Data providers stake FLR to submit prices
- Median of submitted prices used as reference
- Rewards distributed to accurate providers
- Key feeds: XRP/USD, BTC/USD, ETH/USD, FLR/USD, SGB/USD
- Update frequency: ~3 minutes

### State Connector
- Trustless verification of state from other chains
- Proves existence of transactions, blocks, or events
- Two-phase attestation protocol
- Used for cross-chain asset movement

### F-Assets
- Trustless representation of non-smart contract assets
- XRP, BTC, DOGE as F-XRP, F-BTC, F-DOGE on Flare
- Over-collateralized by FLR
- Agents mint F-Assets by locking collateral

## Songbird (Canary Network)
- Flare's canary network (pre-production)
- Native token: SGB
- Test FTSO, State Connector, F-Assets first
- Same architecture as Flare, lower value
- All dApps deploy here before Flare mainnet

## Key Contracts (Flare)
- FTSO system: 0x1000000000000000000000000000000000000002
- State Connector: 0x1000000000000000000000000000000000000003
- WFLR: 0x1D80c49BbBCd1C0911344458cF0eA08C4b5D1e4a

## Key Contracts (Songbird)
- FTSO system: 0x1000000000000000000000000000000000000002
- State Connector: 0x1000000000000000000000000000000000000003
- WSGB: 0x02f0826ef6aD107Cfc861152B32B52fD11BaB9ED

## Development Example
```solidity
contract XRPPriceConsumer {
    function getXRPUSD() external view returns (uint256) {
        (uint256 price,,) = IFlarePriceOracle(FTSO_ADDR).getCurrentPrice("XRP/USD");
        return price;
    }
}
```

## LayerCake Bridge
- Bridge between Flare and other chains
- Uses State Connector for trustless verification
- Supports FLR, SGB, F-Asset transfers

## Resources
- Flare docs: docs.flare.network
- FTSO dashboard: ftso.flare.network
