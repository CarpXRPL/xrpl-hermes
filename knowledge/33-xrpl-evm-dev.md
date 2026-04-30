# XRPL EVM Sidechain Development

## Overview

The XRPL EVM Sidechain is a fully EVM-compatible blockchain connected to the XRPL mainnet via a decentralized bridge. Deploy Solidity contracts, use standard Ethereum tooling, and access XRPL liquidity through the bridge. Chain ID: **1440001** (mainnet), **1440002** (testnet).

---

## 1. Network Details

### Mainnet

```
Chain ID:      1440001
RPC:           https://rpc-evm-sidechain.xrpl.org
WSS:           wss://rpc-evm-sidechain.xrpl.org
Explorer:      https://evm-sidechain.xrpl.org
Native token:  XRP (18 decimals on EVM side)
```

### Testnet

```
Chain ID:      1440002
RPC:           https://rpc-evm-sidechain.testnet.xrpl.org
Faucet:        https://bridge.testnet.xrpl.org
Explorer:      https://evm-sidechain.testnet.xrpl.org
```

---

## 2. Development Environment Setup

### Prerequisites

```bash
# Node.js + npm
node --version   # 18+
npm --version    # 8+

# Hardhat project
mkdir my-xrpl-evm-project
cd my-xrpl-evm-project
npm init -y
npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox
npm install @openzeppelin/contracts dotenv
npx hardhat init  # Select "TypeScript project"
```

### `.env`

```
PRIVATE_KEY=0x...your_private_key...
XRPL_EVM_RPC=https://rpc-evm-sidechain.xrpl.org
```

### `hardhat.config.ts`

```typescript
import { HardhatUserConfig } from "hardhat/config";
import "@nomicfoundation/hardhat-toolbox";
import * as dotenv from "dotenv";
dotenv.config();

const config: HardhatUserConfig = {
  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: { enabled: true, runs: 200 },
      viaIR: true
    }
  },
  networks: {
    xrpl_evm: {
      url: process.env.XRPL_EVM_RPC || "https://rpc-evm-sidechain.xrpl.org",
      chainId: 1440001,
      accounts: [process.env.PRIVATE_KEY!],
      gasPrice: "auto",
      gas: "auto"
    },
    xrpl_evm_testnet: {
      url: "https://rpc-evm-sidechain.testnet.xrpl.org",
      chainId: 1440002,
      accounts: [process.env.PRIVATE_KEY!]
    },
    hardhat: {
      chainId: 1440001,
      forking: {
        url: "https://rpc-evm-sidechain.xrpl.org",
        enabled: process.env.FORK === "true"
      }
    }
  },
  etherscan: {
    apiKey: {
      xrpl_evm: "placeholder"
    },
    customChains: [{
      network: "xrpl_evm",
      chainId: 1440001,
      urls: {
        apiURL: "https://evm-sidechain.xrpl.org/api",
        browserURL: "https://evm-sidechain.xrpl.org"
      }
    }]
  }
};

export default config;
```

---

## 3. Foundry Configuration

```bash
# Install Foundry
curl -L https://foundry.paradigm.xyz | bash
foundryup

forge init xrpl-evm-foundry
cd xrpl-evm-foundry
forge install OpenZeppelin/openzeppelin-contracts
```

```toml
# foundry.toml
[profile.default]
src = "src"
out = "out"
libs = ["lib"]
solc = "0.8.20"
optimizer = true
optimizer-runs = 200
remappings = [
  "@openzeppelin/=lib/openzeppelin-contracts/"
]

[rpc_endpoints]
xrpl_evm = "${XRPL_EVM_RPC}"
xrpl_evm_testnet = "https://rpc-evm-sidechain.testnet.xrpl.org"

[etherscan]
xrpl_evm = { key = "${ETHERSCAN_API_KEY}", url = "https://evm-sidechain.xrpl.org/api" }
```

```bash
# Deploy
forge create \
  --rpc-url xrpl_evm \
  --private-key $PRIVATE_KEY \
  --verify \
  src/Token.sol:XRPLToken

# Test
forge test --rpc-url xrpl_evm -vvvv

# Fork mainnet locally
anvil --fork-url https://rpc-evm-sidechain.xrpl.org --chain-id 1440001
```

---

## 4. wXRP ERC-20

wXRP is the wrapped XRP token on the EVM sidechain:

```solidity
// wXRP interface
interface IWXRP {
    event Deposit(address indexed dst, uint256 wad);
    event Withdrawal(address indexed src, uint256 wad);
    
    function deposit() external payable;
    function withdraw(uint256 wad) external;
    function totalSupply() external view returns (uint256);
    function balanceOf(address guy) external view returns (uint256);
    function transfer(address dst, uint256 wad) external returns (bool);
    function approve(address guy, uint256 wad) external returns (bool);
    function transferFrom(address src, address dst, uint256 wad) external returns (bool);
    function allowance(address src, address guy) external view returns (uint256);
}

address constant WXRP = 0xCCccCCCc00000001000000000000000000000000;
```

Using wXRP in contracts:
```solidity
// Wrap XRP → wXRP
function wrapXRP() external payable {
    IWXRP(WXRP).deposit{value: msg.value}();
}

// Unwrap wXRP → XRP
function unwrapXRP(uint256 amount) external {
    IWXRP(WXRP).withdraw(amount);
    payable(msg.sender).transfer(amount);
}
```

---

## 5. Sample ERC-20 Token

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Permit.sol";

contract XRPLEVMToken is ERC20, ERC20Burnable, Ownable, ERC20Permit {
    uint256 public constant MAX_SUPPLY = 1_000_000_000 * 10**18;
    
    constructor(address initialOwner)
        ERC20("XRPL EVM Token", "XEVM")
        Ownable(initialOwner)
        ERC20Permit("XRPL EVM Token")
    {
        _mint(msg.sender, 100_000_000 * 10**18);
    }
    
    function mint(address to, uint256 amount) external onlyOwner {
        require(totalSupply() + amount <= MAX_SUPPLY, "Exceeds max");
        _mint(to, amount);
    }
}
```

---

## 6. Deployment Scripts

### Hardhat

```typescript
// scripts/deploy.ts
import { ethers } from "hardhat";

async function main() {
  const [deployer] = await ethers.getSigners();
  
  const balance = await deployer.provider.getBalance(deployer.address);
  console.log(`Deployer: ${deployer.address}`);
  console.log(`Balance: ${ethers.formatEther(balance)} XRP`);
  
  const Token = await ethers.getContractFactory("XRPLEVMToken");
  const token = await Token.deploy(deployer.address);
  await token.waitForDeployment();
  
  const address = await token.getAddress();
  console.log(`Token deployed: ${address}`);
  console.log(`Explorer: https://evm-sidechain.xrpl.org/address/${address}`);
  
  return address;
}

main().catch((e) => { console.error(e); process.exit(1); });
```

```bash
npx hardhat run scripts/deploy.ts --network xrpl_evm
```

---

## 7. Bridge Deposits (XRPL → EVM)

```python
# Python: Send XRP from XRPL mainnet to EVM sidechain
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import Payment
from xrpl.transaction import autofill_and_sign, submit_and_wait
import binascii

BRIDGE_DOOR = "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh"  # example door account

client = JsonRpcClient("https://xrplcluster.com")
wallet = Wallet.from_seed("sn...")
evm_address = "0xYOUR_EVM_ADDRESS"

tx = Payment(
    account=wallet.address,
    destination=BRIDGE_DOOR,
    amount="10000000",  # 10 XRP
    memos=[{
        "Memo": {
            "MemoType": binascii.hexlify(b"evmAddress").decode().upper(),
            "MemoData": binascii.hexlify(evm_address.encode()).decode().upper()
        }
    }]
)

signed = autofill_and_sign(tx, wallet, client)
result = submit_and_wait(signed, client)
print(f"Bridge deposit: {result.result['meta']['TransactionResult']}")
# EVM sidechain will credit your EVM address within ~15s
```

---

## 8. Bridge Withdrawals (EVM → XRPL)

```solidity
// Call from your contract or directly
interface IXRPLBridge {
    event WithdrawalRequest(
        address indexed from,
        string xrplDestination,
        uint256 amount,
        uint32 destinationTag
    );
    
    function withdraw(
        string calldata xrplAddress,
        uint32 destinationTag
    ) external payable;
}

// EVM sidechain bridge address (check official docs for current address)
address constant BRIDGE = 0x0000000000000000000000000000000000000009;

// Usage
IXRPLBridge(BRIDGE).withdraw{value: 10 ether}(
    "rXRPLDESTINATION...",
    0
);
```

### JavaScript

```javascript
const { ethers } = require('ethers');

const BRIDGE_ABI = [
  'function withdraw(string calldata xrplAddress, uint32 destinationTag) external payable'
];

const provider = new ethers.JsonRpcProvider('https://rpc-evm-sidechain.xrpl.org');
const wallet = new ethers.Wallet(process.env.PRIVATE_KEY, provider);
const bridge = new ethers.Contract(BRIDGE_ADDRESS, BRIDGE_ABI, wallet);

const tx = await bridge.withdraw(
  'rXRPL_DESTINATION...',
  0,  // destination tag
  { value: ethers.parseEther('10') }
);
await tx.wait();
console.log('Bridge withdrawal initiated:', tx.hash);
```

---

## 9. Cross-Chain Messaging (Axelar)

```solidity
// XRPL EVM supports Axelar for GMP (General Message Passing)
interface IAxelarGateway {
    function callContract(
        string calldata destinationChain,
        string calldata contractAddress,
        bytes calldata payload
    ) external;
    
    function callContractWithToken(
        string calldata destinationChain,
        string calldata contractAddress,
        bytes calldata payload,
        string calldata symbol,
        uint256 amount
    ) external;
}

contract CrossChainMessenger {
    IAxelarGateway immutable gateway;
    
    constructor(address _gateway) {
        gateway = IAxelarGateway(_gateway);
    }
    
    function sendMessage(
        string calldata destinationChain,
        string calldata destinationAddress,
        string calldata message
    ) external {
        bytes memory payload = abi.encode(message);
        gateway.callContract(destinationChain, destinationAddress, payload);
    }
}
```

---

## 10. Testing Locally with Anvil Fork

```bash
# Fork XRPL EVM mainnet
anvil \
  --fork-url https://rpc-evm-sidechain.xrpl.org \
  --chain-id 1440001 \
  --block-time 1 \
  --port 8545

# In your test, use:
# provider = new ethers.JsonRpcProvider('http://localhost:8545')
```

```typescript
// hardhat test with fork
import { expect } from "chai";
import { ethers } from "hardhat";
import { loadFixture } from "@nomicfoundation/hardhat-toolbox/network-helpers";

describe("XRPLEVMToken", function() {
  async function deployFixture() {
    const [owner, user] = await ethers.getSigners();
    const Token = await ethers.getContractFactory("XRPLEVMToken");
    const token = await Token.deploy(owner.address);
    return { token, owner, user };
  }
  
  it("should mint initial supply to owner", async () => {
    const { token, owner } = await loadFixture(deployFixture);
    const balance = await token.balanceOf(owner.address);
    expect(balance).to.equal(ethers.parseEther("100000000"));
  });
  
  it("should transfer tokens", async () => {
    const { token, owner, user } = await loadFixture(deployFixture);
    await token.transfer(user.address, ethers.parseEther("1000"));
    expect(await token.balanceOf(user.address)).to.equal(ethers.parseEther("1000"));
  });
});
```

---

## 11. Gas & Fees

```javascript
// Estimate gas
const gasEstimate = await contract.estimateGas.mint(to, amount);
const gasPrice = await provider.getFeeData();

console.log(`Gas estimate: ${gasEstimate.toString()}`);
console.log(`Gas price: ${ethers.formatUnits(gasPrice.gasPrice, 'gwei')} gwei`);
console.log(`Estimated cost: ${ethers.formatEther(gasEstimate * gasPrice.gasPrice)} XRP`);

// Send with explicit gas
const tx = await contract.mint(to, amount, {
  gasLimit: gasEstimate * 120n / 100n,  // 20% buffer
  maxFeePerGas: gasPrice.maxFeePerGas,
  maxPriorityFeePerGas: gasPrice.maxPriorityFeePerGas
});
```

---

## 12. Key Differences from Ethereum

| Feature | Ethereum | XRPL EVM |
|---------|----------|----------|
| Native token | ETH (18 dec) | XRP (18 dec on EVM) |
| Block time | ~12s | ~3-5s |
| Consensus | PoS | Federated UNL |
| Chain ID | 1 | 1440001 |
| wETH equivalent | 0xC02a... | wXRP 0xCCcc...0001 |
| Bridge | Separate L2s | Native XRPL bridge |
| DEX | Uniswap etc | AMM on XRPL L1 |
| Smart contracts | Full EVM | Full EVM |
