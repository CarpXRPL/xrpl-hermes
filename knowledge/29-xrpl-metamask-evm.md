# XRPL EVM Sidechain: MetaMask & Solidity Development

## Overview

The XRPL EVM Sidechain is an Ethereum-compatible blockchain connected to the XRPL via a trust-minimized bridge. It runs Solidity smart contracts, uses wXRP as native currency, and connects to MetaMask. Chain ID: **1440001**.

---

## 1. Network Configuration

### MetaMask Manual Setup

| Parameter | Value |
|-----------|-------|
| Network Name | XRPL EVM Sidechain |
| RPC URL | `https://rpc-evm-sidechain.xrpl.org` |
| Chain ID | `1440001` |
| Currency Symbol | `XRP` |
| Block Explorer | `https://evm-sidechain.xrpl.org` |

```javascript
// Add network programmatically
async function addXRPLNetwork() {
  await window.ethereum.request({
    method: 'wallet_addEthereumChain',
    params: [{
      chainId: '0x15F902',  // 1440001 in hex
      chainName: 'XRPL EVM Sidechain',
      nativeCurrency: {
        name: 'XRP',
        symbol: 'XRP',
        decimals: 18
      },
      rpcUrls: ['https://rpc-evm-sidechain.xrpl.org'],
      blockExplorerUrls: ['https://evm-sidechain.xrpl.org']
    }]
  });
}
```

### Alternative RPC Endpoints

```
Primary:  https://rpc-evm-sidechain.xrpl.org
Testnet:  https://rpc-evm-sidechain.testnet.xrpl.org (Chain ID: 1440002)
```

---

## 2. wXRP Currency

On the EVM sidechain, XRP is represented as the native gas token (like ETH on Ethereum). Wrapped XRP (wXRP) is an ERC-20 version:

```
wXRP Contract: 0xCCccCCCc00000001000000000000000000000000
               (canonical wrapped XRP address)
```

```solidity
// IERC20 interface for wXRP
interface IWXRP {
    function deposit() external payable;
    function withdraw(uint256 amount) external;
    function balanceOf(address account) external view returns (uint256);
    function transfer(address to, uint256 amount) external returns (bool);
    function approve(address spender, uint256 amount) external returns (bool);
}
```

XRP has 6 decimal places on XRPL, but 18 on EVM sidechain:
```javascript
// XRP amount conversion
const XRP_DECIMALS = 18;  // on EVM sidechain
const xrpToWei = (xrp) => ethers.parseEther(String(xrp));
const weiToXrp = (wei) => ethers.formatEther(wei);
```

---

## 3. Hardhat Configuration

```bash
npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox
npx hardhat init
```

```javascript
// hardhat.config.js
require('@nomicfoundation/hardhat-toolbox');
require('dotenv').config();

module.exports = {
  solidity: {
    version: '0.8.20',
    settings: {
      optimizer: {
        enabled: true,
        runs: 200
      }
    }
  },
  networks: {
    xrpl_evm: {
      url: 'https://rpc-evm-sidechain.xrpl.org',
      chainId: 1440001,
      accounts: [process.env.PRIVATE_KEY],
      gasPrice: 'auto'
    },
    xrpl_evm_testnet: {
      url: 'https://rpc-evm-sidechain.testnet.xrpl.org',
      chainId: 1440002,
      accounts: [process.env.PRIVATE_KEY],
    }
  },
  etherscan: {
    apiKey: {
      xrpl_evm: 'no-api-key-needed'
    },
    customChains: [
      {
        network: 'xrpl_evm',
        chainId: 1440001,
        urls: {
          apiURL: 'https://evm-sidechain.xrpl.org/api',
          browserURL: 'https://evm-sidechain.xrpl.org'
        }
      }
    ]
  }
};
```

---

## 4. Foundry Configuration

```bash
# Install Foundry
curl -L https://foundry.paradigm.xyz | bash
foundryup

# Initialize project
forge init my-xrpl-contract
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

[rpc_endpoints]
xrpl_evm = "https://rpc-evm-sidechain.xrpl.org"
xrpl_evm_testnet = "https://rpc-evm-sidechain.testnet.xrpl.org"

[etherscan]
xrpl_evm = { key = "placeholder", url = "https://evm-sidechain.xrpl.org/api" }
```

```bash
# Deploy with Foundry
forge create \
  --rpc-url xrpl_evm \
  --private-key $PRIVATE_KEY \
  src/MyContract.sol:MyContract \
  --constructor-args "arg1" "arg2"

# Verify contract
forge verify-contract \
  --chain-id 1440001 \
  --rpc-url https://rpc-evm-sidechain.xrpl.org \
  0xCONTRACT_ADDRESS \
  src/MyContract.sol:MyContract
```

---

## 5. Deploying with Hardhat

```javascript
// scripts/deploy.js
const { ethers } = require('hardhat');

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log('Deploying with:', deployer.address);
  console.log('Balance:', ethers.formatEther(await deployer.provider.getBalance(deployer.address)), 'XRP');

  const MyContract = await ethers.getContractFactory('MyContract');
  const contract = await MyContract.deploy(/* constructor args */);
  await contract.waitForDeployment();

  console.log('Contract deployed to:', await contract.getAddress());
}

main().catch((e) => { console.error(e); process.exit(1); });
```

```bash
npx hardhat run scripts/deploy.js --network xrpl_evm
```

---

## 6. Bridge: XRPL ↔ EVM

The bridge allows moving XRP between the XRPL mainnet and the EVM sidechain.

### Bridge Addresses

```
XRPL Mainnet locking account: rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh  (door account)
EVM Sidechain bridge contract: 0x... (deployed on EVM sidechain)
```

### Deposit (XRPL → EVM)

```python
# Send XRP from XRPL to bridge door account
# with your EVM address as a memo

from xrpl.models.transactions import Payment
import binascii

evm_address = "0xYOUR_EVM_ADDRESS"

tx = Payment(
    account=xrpl_wallet.address,
    destination="rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",  # bridge door
    amount="10000000",  # 10 XRP
    memos=[{
        "Memo": {
            "MemoData": binascii.hexlify(evm_address.encode()).decode().upper(),
            "MemoType": binascii.hexlify(b"destination").decode().upper()
        }
    }]
)
```

### Withdrawal (EVM → XRPL)

```solidity
// Call bridge contract on EVM sidechain
interface IBridge {
    function crossChainTransfer(
        string calldata xrplDestination,
        uint256 amount,
        uint32 destinationTag
    ) external payable;
}

// Usage
IBridge bridge = IBridge(BRIDGE_CONTRACT_ADDRESS);
bridge.crossChainTransfer{value: 10 ether}(
    "rXRPL_ADDRESS...",
    10 ether,
    0  // destination tag
);
```

---

## 7. Sample Solidity Contract

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract XRPLToken is ERC20, Ownable {
    uint256 public constant MAX_SUPPLY = 1_000_000_000 * 10**18;
    
    constructor(address initialOwner) 
        ERC20("XRPL Token", "XTKN") 
        Ownable(initialOwner) 
    {
        _mint(msg.sender, 100_000_000 * 10**18);  // 100M initial
    }
    
    function mint(address to, uint256 amount) external onlyOwner {
        require(totalSupply() + amount <= MAX_SUPPLY, "Exceeds max supply");
        _mint(to, amount);
    }
    
    // Accept XRP deposits
    receive() external payable {}
    
    function getXRPBalance() external view returns (uint256) {
        return address(this).balance;
    }
}
```

---

## 8. ethers.js Integration

```javascript
const { ethers } = require('ethers');

// Connect to XRPL EVM
const provider = new ethers.JsonRpcProvider(
  'https://rpc-evm-sidechain.xrpl.org'
);

// Connect wallet
const wallet = new ethers.Wallet(process.env.PRIVATE_KEY, provider);
console.log('Address:', wallet.address);
console.log('Chain ID:', (await provider.getNetwork()).chainId);  // 1440001n

// Send XRP (native token)
async function sendXRP(to, xrpAmount) {
  const tx = await wallet.sendTransaction({
    to,
    value: ethers.parseEther(String(xrpAmount))
  });
  return tx.wait();
}

// Interact with contract
const abi = [...]; // your contract ABI
const contract = new ethers.Contract(CONTRACT_ADDRESS, abi, wallet);
const result = await contract.someFunction(arg1, arg2);
```

---

## 9. MetaMask React Integration

```jsx
import { useState } from 'react';
import { ethers } from 'ethers';

const XRPL_EVM_CHAIN_ID = 1440001;

function XRPLEVMWallet() {
  const [account, setAccount] = useState(null);
  const [provider, setProvider] = useState(null);

  const connect = async () => {
    if (!window.ethereum) {
      alert('Install MetaMask');
      return;
    }

    // Add/switch to XRPL EVM network
    try {
      await window.ethereum.request({
        method: 'wallet_switchEthereumChain',
        params: [{ chainId: '0x15F902' }]
      });
    } catch (e) {
      if (e.code === 4902) {
        await addXRPLNetwork();
      }
    }

    const accounts = await window.ethereum.request({
      method: 'eth_requestAccounts'
    });
    setAccount(accounts[0]);

    const p = new ethers.BrowserProvider(window.ethereum);
    setProvider(p);
  };

  const sendXRP = async (to, amount) => {
    const signer = await provider.getSigner();
    const tx = await signer.sendTransaction({
      to,
      value: ethers.parseEther(String(amount))
    });
    return tx.wait();
  };

  return (
    <div>
      {account ? (
        <div>
          <p>Connected: {account}</p>
          <button onClick={() => sendXRP('0xDEST...', 1)}>Send 1 XRP</button>
        </div>
      ) : (
        <button onClick={connect}>Connect MetaMask</button>
      )}
    </div>
  );
}
```

---

## 10. Cross-Chain Messaging

Using the XRPL EVM bridge for automated cross-chain operations:

```javascript
// Monitor XRPL for events → trigger EVM contract
const xrpl = require('xrpl');

const xrplClient = new xrpl.Client('wss://xrplcluster.com');
await xrplClient.connect();

xrplClient.on('transaction', async (tx) => {
  if (tx.transaction.Destination === BRIDGE_DOOR_ACCOUNT) {
    // XRP is moving to EVM sidechain
    const evmAddress = extractEVMAddressFromMemo(tx.transaction.Memos);
    const amount = tx.meta.delivered_amount;
    
    console.log(`Bridge: ${amount} drops → ${evmAddress} on EVM`);
    // EVM side handles the rest automatically
  }
});

await xrplClient.request({
  command: 'subscribe',
  accounts: [BRIDGE_DOOR_ACCOUNT]
});
```
