# XRPL Full Ecosystem Interoperability

## Overview

The XRPL ecosystem spans multiple chains and layers: XRPL L1 mainnet, EVM Sidechain, Xahau (Hooks), Flare, Songbird, and cross-chain protocols like Axelar. This guide covers bridging, wallet compatibility, and complete routing between all layers.

---

## 1. Ecosystem Map

```
                    ┌──────────────────┐
                    │   XRPL Mainnet   │  Chain: XRPL (not EVM)
                    │   (L1, XRP)      │  SDK: xrpl.js / xrpl-py
                    └──────┬───────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
    ┌──────▼──────┐ ┌──────▼──────┐ ┌─────▼──────┐
    │ XRPL EVM    │ │   Xahau     │ │  Flare /   │
    │ Sidechain   │ │  (Hooks)    │ │  Songbird  │
    │ Chain 1440000│ │ Chain 21337 │ │ Chain 14/19│
    └──────┬───────┘ └─────────────┘ └─────┬──────┘
           │                               │
           └──────── Axelar GMP ───────────┘
                     (50+ chains)
```

---

## 2. Layer-by-Layer Summary

### XRPL L1 Mainnet

```
Network:    XRPL (not EVM)
RPC:        wss://xrplcluster.com, https://xrplcluster.com
Explorer:   https://livenet.xrpl.org
Native:     XRP (6 decimal places)
Smart contracts: None (use Hooks on Xahau)
DEX:        Built-in order book + AMM
NFTs:       Native NFToken standard
Wallets:    Xaman, Joey, Bifrost, Crossmark
```

### XRPL EVM Sidechain

```
Network:    Ethereum-compatible EVM
Chain ID:   1440000 (mainnet), 1450024 (testnet)
RPC:        https://rpc.xrplevm.org
Explorer:   https://evm-sidechain.xrpl.org
Native:     XRP (18 decimal places on EVM)
Smart contracts: Solidity (full EVM)
DEX:        EVM DEXes (deploy your own)
NFTs:       ERC-721, ERC-1155
Wallets:    MetaMask, WalletConnect
```

### Xahau

```
Network:    XRPL fork with Hooks enabled
Chain ID:   21337
RPC:        wss://xahau.network, https://xahau.network
Testnet:    wss://hooks-testnet-v3.xrpl-labs.com
Explorer:   https://explorer.xahau.network
Native:     XAH (not XRP)
Smart contracts: C Hooks compiled to WASM
Wallets:    Joey, Xaman (partial), Crossmark
```

### Flare Network

```
Network:    EVM chain with XRPL oracle integration
Chain ID:   14
RPC:        https://flare-api.flare.network/ext/C/rpc
Explorer:   https://flare-explorer.flare.network
Native:     FLR
XRPL connection: F-Assets (XRP → FXRP)
```

### Songbird

```
Network:    Flare canary network
Chain ID:   19
RPC:        https://songbird-api.flare.network/ext/C/rpc
Explorer:   https://songbird-explorer.flare.network
Native:     SGB
XRPL connection: F-Assets (XRP → FXRP)
```

---

## 3. Bridging: XRPL L1 ↔ EVM Sidechain

```python
# XRPL → EVM: Send XRP to bridge door account
from xrpl.models.transactions import Payment
import binascii

async def xrpl_to_evm(
    xrpl_wallet,
    evm_address: str,
    xrp_amount: float,
    client
):
    BRIDGE_DOOR = "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh"  # Official bridge door
    
    tx = Payment(
        account=xrpl_wallet.address,
        destination=BRIDGE_DOOR,
        amount=str(int(xrp_amount * 1e6)),
        memos=[{
            "Memo": {
                "MemoType": binascii.hexlify(b"evmAddress").decode().upper(),
                "MemoData": binascii.hexlify(evm_address.encode()).decode().upper()
            }
        }]
    )
    
    signed = await autofill_and_sign(tx, xrpl_wallet, client)
    result = await submit_and_wait(signed, client)
    return result
```

```javascript
// EVM → XRPL: Call bridge contract on EVM sidechain
const { ethers } = require('ethers');

async function evmToXRPL(xrplAddress, xrpAmount, provider, wallet) {
  const BRIDGE_ABI = ['function withdraw(string, uint32) external payable'];
  const BRIDGE_ADDR = '0x0000000000000000000000000000000000000009';
  
  const bridge = new ethers.Contract(BRIDGE_ADDR, BRIDGE_ABI, wallet);
  const tx = await bridge.withdraw(xrplAddress, 0, {
    value: ethers.parseEther(String(xrpAmount))
  });
  
  return tx.wait();
}
```

---

## 4. Bridging: XRPL L1 ↔ Flare (F-Assets)

Flare's F-Assets protocol wraps XRPL-native XRP as FXRP on Flare:

```
XRP (XRPL) → FXRP (Flare)
1. Lock XRP in Flare agent address on XRPL
2. Agent mints FXRP on Flare
3. FXRP is ERC-20, usable in DeFi

FXRP (Flare) → XRP (XRPL)  
1. Redeem FXRP on Flare
2. Agent releases XRP on XRPL
```

```javascript
// Flare: Mint FXRP by locking XRP
const FASSET_MANAGER = '0x...FAssetManager...';
const ABI = [
  'function mintFAssets(address agentVault, uint256 lots, uint256 maxMintingFeeBIPS) external payable returns (uint256 collateralReservationId)'
];

const manager = new ethers.Contract(FASSET_MANAGER, ABI, signer);
const tx = await manager.mintFAssets(agentVault, lots, maxFee);
```

---

## 5. Axelar GMP: XRPL EVM ↔ 50+ Chains

Axelar General Message Passing connects XRPL EVM to Ethereum, Polygon, Cosmos, etc.:

```solidity
// XRPL EVM → Ethereum: Send message + tokens
interface IAxelarGateway {
    function callContractWithToken(
        string calldata destinationChain,
        string calldata contractAddress,
        bytes calldata payload,
        string calldata symbol,
        uint256 amount
    ) external;
}

interface IAxelarGasService {
    function payNativeGasForContractCallWithToken(
        address sender,
        string calldata destinationChain,
        string calldata destinationAddress,
        bytes calldata payload,
        string calldata symbol,
        uint256 amount,
        address refundAddress
    ) external payable;
}

contract XRPLEVMSender {
    IAxelarGateway constant gateway = IAxelarGateway(AXELAR_GATEWAY);
    IAxelarGasService constant gasService = IAxelarGasService(AXELAR_GAS_SERVICE);
    
    function sendToEthereum(
        string calldata destinationAddress,
        bytes calldata payload,
        uint256 usdcAmount
    ) external payable {
        // Pay gas for cross-chain execution
        gasService.payNativeGasForContractCallWithToken{value: msg.value}(
            address(this),
            "Ethereum",
            destinationAddress,
            payload,
            "USDC",
            usdcAmount,
            msg.sender
        );
        
        // Send USDC + message to Ethereum
        IERC20(USDC_ADDRESS).approve(address(gateway), usdcAmount);
        gateway.callContractWithToken(
            "Ethereum",
            destinationAddress,
            payload,
            "USDC",
            usdcAmount
        );
    }
}
```

### Supported Chains via Axelar from XRPL EVM

```javascript
const AXELAR_CHAINS = [
  "Ethereum", "Polygon", "Avalanche", "Fantom",
  "Moonbeam", "BNB", "Arbitrum", "Optimism",
  "Base", "Linea", "Celo", "Kava",
  "Osmosis", "Cosmos", "Juno", "Injective",
  // ... 50+ total
];

// Axelar Gateway on XRPL EVM:
const AXELAR_GATEWAY_XRPL_EVM = "0x...";
const AXELAR_GAS_SERVICE_XRPL_EVM = "0x...";
```

---

## 6. Arweave for Permanent XRPL Data

Store XRPL transaction history, NFT metadata, and app state permanently on Arweave:

```javascript
import Arweave from 'arweave';
import { JWKInterface } from 'arweave/node/lib/wallet';

const arweave = Arweave.init({
  host: 'arweave.net',
  port: 443,
  protocol: 'https'
});

// Store XRPL transaction data permanently
async function archiveXRPLTx(txData: object, jwk: JWKInterface): Promise<string> {
  const data = JSON.stringify(txData);
  
  const tx = await arweave.createTransaction({ data });
  tx.addTag('Content-Type', 'application/json');
  tx.addTag('App', 'XRPL-Archive');
  tx.addTag('Network', 'mainnet');
  
  await arweave.transactions.sign(tx, jwk);
  await arweave.transactions.post(tx);
  
  return `https://arweave.net/${tx.id}`;
}

// Retrieve archived data
async function getArchivedTx(arweaveTxId: string) {
  const resp = await fetch(`https://arweave.net/${arweaveTxId}`);
  return resp.json();
}

// Cost estimate before upload
async function estimateCost(sizeBytes: number): Promise<string> {
  const price = await arweave.transactions.getPrice(sizeBytes);
  return arweave.ar.winstonToAr(price);  // in AR tokens
}
```

### Bundlr (now Irys) for Cheaper Arweave Uploads

```javascript
import { Uploader } from "@irys/upload";

const uploader = await Uploader.webUploader("arweave")
  .withWallet(jwk);

// Upload NFT metadata permanently
const receipt = await uploader.upload(
  JSON.stringify({ name: "NFT #001", image: "..." }),
  { tags: [{ name: "Content-Type", value: "application/json" }] }
);

const permanentUri = `https://arweave.net/${receipt.id}`;
```

---

## 7. Cross-Chain NFT Marketplace

```
XRPL NFT (NFToken) ────────────────► EVM NFT (ERC-721)
    │                                      │
    │  NFT bridge (LayerZero/Axelar)       │
    │                                      │
    ▼                                      ▼
XRPL L1 listing                  EVM marketplace listing
(NFTokenCreateOffer)              (OpenSea, LooksRare)
```

```solidity
// Represent XRPL NFT on EVM sidechain
contract XRPLNFTWrapper is ERC721 {
    mapping(bytes32 => uint256) public xrplToEvmId;
    mapping(uint256 => bytes32) public evmToXrplId;
    
    event NFTBridged(bytes32 indexed xrplNftId, uint256 indexed evmTokenId, address owner);
    
    function bridgeFromXRPL(
        bytes32 xrplNftId,
        address owner,
        string calldata tokenURI
    ) external onlyBridge {
        uint256 tokenId = uint256(xrplNftId);
        _mint(owner, tokenId);
        _setTokenURI(tokenId, tokenURI);
        xrplToEvmId[xrplNftId] = tokenId;
        evmToXrplId[tokenId] = xrplNftId;
        emit NFTBridged(xrplNftId, tokenId, owner);
    }
}
```

---

## 8. Wallet Compatibility Matrix

| Wallet | XRPL L1 | EVM Sidechain | Xahau | Flare | Hardware |
|--------|---------|---------------|-------|-------|----------|
| Xaman | ✅ | ❌ | Partial | ❌ | ❌ |
| Joey | ✅ | ❌ | ✅ | ❌ | ❌ |
| Crossmark | ✅ | ❌ | ✅ | ❌ | ❌ |
| Bifrost | ✅ | ❌ | ❌ | ❌ | ✅ |
| MetaMask | ❌ | ✅ | ❌ | ✅ | Via Ledger |
| WalletConnect | ❌ | ✅ | ❌ | ✅ | ❌ |
| Ledger | ✅ | ✅ | ❌ | ✅ | ✅ |
| Privy | XRPL SDK | ✅ | ❌ | ✅ | ❌ |

---

## 9. Complete Routing Guide

### Scenario: User has ETH on Ethereum, wants to provide liquidity on XRPL AMM

```
ETH (Ethereum)
    │
    ▼ Axelar bridge ETH → USDC on XRPL EVM
    │
USDC (XRPL EVM Sidechain)
    │
    ▼ EVM → XRPL bridge
    │
USDC/XRP trust line + AMM on XRPL L1
```

### Scenario: User wants XRP on Flare to use FLR DeFi

```
XRP (XRPL L1)
    │
    ▼ F-Asset minting
    │
FXRP (Flare)
    │
    ▼ Use in Flare DeFi: swap, lend, yield
    │
    ▼ Redeem FXRP → XRP on XRPL L1
```

### Scenario: Deploy smart contract that reacts to XRPL payments

```
User sends XRP on XRPL
    │
    ▼ Hook on Xahau catches payment (if using Xahau)
    │  OR
    ▼ Bridge to EVM sidechain
    │
Solidity contract executes
    │
    ▼ Results bridge back to XRPL
```

---

## 10. Multi-Chain SDK Architecture

```python
class XRPLEcosystemClient:
    """Unified client for all XRPL ecosystem chains."""
    
    def __init__(self):
        # XRPL L1
        from xrpl.clients import JsonRpcClient
        self.xrpl = JsonRpcClient("https://xrplcluster.com")
        
        # EVM Sidechain
        from web3 import Web3
        self.evm = Web3(Web3.HTTPProvider("https://rpc.xrplevm.org"))
        
        # Xahau
        self.xahau = JsonRpcClient("https://xahau.network")
        
        # Flare (EVM)
        self.flare = Web3(Web3.HTTPProvider("https://flare-api.flare.network/ext/C/rpc"))
    
    def xrpl_balance(self, address: str) -> float:
        from xrpl.models.requests import AccountInfo
        resp = self.xrpl.request(AccountInfo(account=address))
        return int(resp.result["account_data"]["Balance"]) / 1e6
    
    def evm_balance(self, address: str) -> float:
        from web3 import Web3
        balance_wei = self.evm.eth.get_balance(address)
        return float(self.evm.from_wei(balance_wei, 'ether'))
    
    def flare_balance(self, address: str) -> float:
        balance_wei = self.flare.eth.get_balance(address)
        return float(self.flare.from_wei(balance_wei, 'ether'))
    
    def total_xrp_across_chains(self, xrpl_addr: str, evm_addr: str) -> dict:
        return {
            "xrpl_l1": self.xrpl_balance(xrpl_addr),
            "evm_sidechain": self.evm_balance(evm_addr),
            "xahau": self.xrpl_balance(xrpl_addr),  # different network
        }
```

---

## 11. Permanent Storage Architecture for XRPL Apps

```
Application Data Flow:
                    
User Action
    │
    ▼
Frontend (Vercel/Netlify/Arweave)
    │
    ▼
Backend API (VPS or serverless)
    │
    ├──► XRPL L1 (transactions, tokens, NFTs)
    │
    ├──► EVM Sidechain (smart contracts, DeFi)
    │
    ├──► Arweave (permanent metadata, archives)
    │         Content-addressed, permanent
    │
    ├──► IPFS (NFT images, metadata)
    │         Pinned via Pinata/NFT.storage
    │
    └──► PostgreSQL/Redis (app state, caching)

Recommended Stack:
  Frontend:  Next.js on Vercel
  Backend:   FastAPI on Hetzner CX32
  XRPL:      xrpl-py or xrpl.js
  EVM:       ethers.js or web3.py
  Storage:   Arweave (permanent) + Redis (cache)
  Auth:      Xaman (crypto-native) or Privy (mainstream)
  Monitor:   Uptime Kuma + Cloudflare
```

---

## 12. Chain ID Reference

| Network | Chain ID | Type |
|---------|----------|------|
| XRPL Mainnet | N/A (not EVM) | XRPL |
| XRPL Testnet | N/A | XRPL |
| XRPL EVM Sidechain | 1440000 | EVM |
| XRPL EVM Testnet | 1450024 | EVM |
| Xahau Mainnet | 21337 | XRPL fork |
| Xahau Testnet | 21338 | XRPL fork |
| Flare | 14 | EVM |
| Songbird | 19 | EVM |
| Ethereum | 1 | EVM |
| Polygon | 137 | EVM |
| Arbitrum One | 42161 | EVM L2 |
| Base | 8453 | EVM L2 |

---

## Related Files

- `knowledge/33-xrpl-evm-dev.md` — EVM development
- `knowledge/44-xrpl-evm-advanced.md` — advanced cross-VM patterns
- `knowledge/46-xrpl-axelar-bridge.md` — Axelar GMP bridges
- `knowledge/50-xrpl-evm-sidechain.md` — XRPL EVM sidechain
- `knowledge/55-xrpl-sidechain-interop.md` — sidechain interop patterns
