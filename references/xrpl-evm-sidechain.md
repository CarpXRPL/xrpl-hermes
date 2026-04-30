# XRPL EVM Sidechain — Complete Reference

## Overview
The XRPL EVM Sidechain is an Ethereum Virtual Machine (EVM) compatible sidechain to the XRP Ledger. Enables Solidity smart contracts, ERC-20/ERC-721 tokens, and full Ethereum dApp compatibility while maintaining a trustless bridge to XRPL L1.

**Status:** Mainnet live. Federated bridge between XRPL L1 and EVM sidechain.

## Architecture

```
XRPL L1  ←→  Federated Bridge  ←→  XRPL EVM Sidechain
(wXRP,           |                     (EVM, Solidity)
RLUSD)      Witness / Federator
```

### Bridge Components
- **Deposit**: Send XRP or tokens from L1 → sidechain (wrapped)
- **Withdraw**: Send from sidechain → L1 (unwrapped)
- **Federators**: Trusted parties that validate cross-chain messages
- **Witnesses**: Observe and attest to L1 transactions
- **wXRP**: Wrapped XRP on the EVM sidechain

### Bridge Transactions

**Deposit to Sidechain (L1 → EVM):**
1. User sends XRP/tokens to bridge's L1 account with destination tag
2. Witnesses observe the L1 transaction
3. After sufficient confirmations, federators sign a mint transaction on EVM sidechain
4. wXRP or wrapped tokens credited to user's EVM address

**Withdraw to L1 (EVM → L1):**
1. User burns wXRP/tokens on EVM sidechain
2. Federators observe the burn
3. After consensus, federators sign the L1 release transaction
4. XRP/tokens released to user's L1 account

### EVM Sidechain Specifics
- **Chain ID**: 1440000 (mainnet), 1450024 (testnet)
- **RPC**: Public RPC endpoints available
- **Block Time**: 3-5 seconds
- **Gas Token**: wXRP (wrapped XRP)
- **Consensus**: Authority round-robin (federators)
- **Explorer**: Block explorer at evm-sidechain-explorer.xrpl.org

### Key Contracts
- Bridge contract: Manages deposits/withdrawals between chains
- wXRP contract: ERC-20 wrapper for XRP
- Fee contract: Manages bridge fees

## Development

### Deploying a Solidity Contract
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract MyToken {
    string public name = "My Token";
    string public symbol = "MYT";
    uint8 public decimals = 18;
    uint256 public totalSupply;
    
    mapping(address => uint256) public balanceOf;
    
    constructor(uint256 _initialSupply) {
        totalSupply = _initialSupply;
        balanceOf[msg.sender] = _initialSupply;
    }
    
    function transfer(address to, uint256 amount) external returns (bool) {
        require(balanceOf[msg.sender] >= amount, "Insufficient balance");
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
        return true;
    }
}
```

### Deploy via Hardhat
```javascript
// hardhat.config.js
module.exports = {
  networks: {
    xrplEVM: {
      url: "https://rpc.xrplevm.org",
      chainId: 1440000,
      accounts: [process.env.PRIVATE_KEY]
    }
  }
};
```

### Deploy via Foundry
```bash
forge create MyToken --rpc-url https://rpc.xrplevm.org \
  --private-key $PRIVATE_KEY \
  --constructor-args 1000000000000000000000000
```

## Use Cases
- DeFi protocols (lending, borrowing, DEX)
- NFT marketplaces (ERC-721)
- Token bridges between chains
- Complex smart contract logic
- Existing Ethereum dApp porting

## Bridge Security
- Federator model (multi-sig)
- Witness attestation delay
- Fraud proofs (depending on implementation)
- Rate limits on bridge withdrawals
- Emergency pause mechanisms
