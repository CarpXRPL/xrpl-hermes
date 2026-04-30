# XRPL Wallets & Auth — Complete Reference

## Xaman Wallet
Formerly XUMM. Most popular XRPL mobile wallet.

### Key Features
- Non-custodial (keys stored on device only)
- XRPL L1 native
- Deep-link signing (Pay URL scheme: https://xumm.app/detect/...)
- Push notifications for transactions
- NFT viewer and management
- Multi-account support
- In-app DEX and AMM access

### Deep Link Format
xumm://sign - Full signing request
https://xumm.app/detect/ - Browser detection with auto-app-open
Payload: JSON transaction object. Xaman parses, validates, signs, returns tx_blob.

### Signing Flow
1. App creates signing payload (JSON tx)
2. Generates a sign-in URL / QR code
3. User opens in Xaman on phone
4. Xaman validates, user reviews and signs
5. Xaman returns signed tx_blob
6. App submits blob to XRPL network via xrpl-py

### API
- Xaman API: (requires API key) for advanced features
- Subscription: real-time tx status via WebSocket

## Joey Wallet
Lightweight XRPL web wallet by XRPL Labs.

### Key Features
- Browser-based (no install required)
- XRPL L1 and Hooks support
- Trust line management
- Transaction signing via browser extension
- Xahau Hooks compatible

### Use Cases
- Quick web dApp authentication
- Hooks testing and deployment
- Development and testing

## Privy Auth
Web3 authentication SDK. No seed phrases, no browser extensions.

### Features
- Email/social login + embedded wallet creation
- Supports XRPL keys (Ed25519)
- Wallet abstraction (user doesn't see keys)
- Pre-built React components
- Multi-chain support (ETH, SOL, XRPL)

### Integration
```javascript
import { PrivyProvider, usePrivy } from '@privy-io/react-auth';
usePrivy().login(); // Email, Google, Twitter, Discord
usePrivy().getEthereumWallet(); // Ethers provider
// XRPL signing via custom integration
```

## MetaMask (EVM Sidechain)
### Setup
1. Add XRPL EVM Sidechain RPC
2. Network Name: XRPL EVM Sidechain
3. RPC URL: https://rpc.xrplevm.org
4. Chain ID: 1440000
5. Currency: wXRP

### Usage
- Deploy and interact with Solidity contracts
- Bridge XRP/RLUSD via sidechain bridge UI
- Sign transactions for EVM dApps
- WalletConnect for mobile

## Comparison

| Wallet | Type | Best For |
|--------|------|----------|
| Xaman | Mobile app | Daily XRPL use, payments, tokens, NFTs |
| Joey | Browser plugin | Hooks dev, web dApps, fast auth |
| Privy | SDK | Embedded wallets, social login, no seed phrase UX |
| MetaMask | Browser plugin | EVM sidechain, Solidity dev, DeFi |
