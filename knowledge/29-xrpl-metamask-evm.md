# XRPL EVM Sidechain: MetaMask & Solidity Development

## Overview

The XRPL EVM Sidechain is an Ethereum-compatible blockchain (Cosmos SDK chain, CometBFT consensus) connected to the XRPL via the Axelar bridge. It runs Solidity smart contracts, uses **XRP as the native gas token** (18 decimals on the EVM side), and connects to MetaMask. Chain ID: **1440000**.

---

## 1. Network Configuration

### MetaMask Manual Setup

| Parameter | Value |
|-----------|-------|
| Network Name | XRPL EVM Sidechain |
| RPC URL | `https://rpc.xrplevm.org` |
| Chain ID | `1440000` |
| Currency Symbol | `XRP` |
| Block Explorer | `https://explorer.xrplevm.org` |

```javascript
// Add network programmatically
async function addXRPLNetwork() {
  await window.ethereum.request({
    method: 'wallet_addEthereumChain',
    params: [{
      chainId: '0x15F900',  // 1440000 in hex
      chainName: 'XRPL EVM Sidechain',
      nativeCurrency: {
        name: 'XRP',
        symbol: 'XRP',
        decimals: 18
      },
      rpcUrls: ['https://rpc.xrplevm.org'],
      blockExplorerUrls: ['https://explorer.xrplevm.org']
    }]
  });
}
```

### Alternative RPC Endpoints

```
Primary:  https://rpc.xrplevm.org
Testnet:  https://rpc.testnet.xrplevm.org (Chain ID: 1449000)
```

---

## 2. XRP as Native Gas + Wrapped XRP

On the EVM sidechain, XRP **is** the native gas token (like ETH on Ethereum) — it arrives via the Axelar bridge. For DeFi protocols that need an ERC-20, a WETH-style wrapped-XRP (WXRP) contract can be used. **Verify the current WXRP contract address on the live explorer (`https://explorer.xrplevm.org`) before using one** — old devnet-era addresses circulating in tutorials are no longer valid.

```solidity
// WETH-style wrapper interface for WXRP
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
      url: 'https://rpc.xrplevm.org',
      chainId: 1440000,
      accounts: [process.env.PRIVATE_KEY],
      gasPrice: 'auto'
    },
    xrpl_evm_testnet: {
      url: 'https://rpc.testnet.xrplevm.org',
      chainId: 1449000,
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
        chainId: 1440000,
        urls: {
          apiURL: 'https://explorer.xrplevm.org/api',
          browserURL: 'https://explorer.xrplevm.org'
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
xrpl_evm = "https://rpc.xrplevm.org"
xrpl_evm_testnet = "https://rpc.testnet.xrplevm.org"

[etherscan]
xrpl_evm = { key = "placeholder", url = "https://explorer.xrplevm.org/api" }
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
  --chain-id 1440000 \
  --rpc-url https://rpc.xrplevm.org \
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

## 6. Bridge: XRPL ↔ EVM (Axelar)

XRP moves between XRPL mainnet and the EVM sidechain through the **Axelar network**. Do not hardcode old tutorial "door" accounts or placeholder bridge contracts; get the current route, gateway, and token details from the official XRPL EVM / Axelar docs and the live explorer at integration time.

- **UI route (recommended):** bridge via Squid Router — https://app.squidrouter.com — linked from https://docs.xrplevm.org.
- **Programmatic route:** Axelar Interchain Token Service / GMP. See `knowledge/46-xrpl-axelar-bridge.md` for the flow and code patterns.
- **Security rule:** never tell a user to send XRP to a bridge address you have not verified against official docs that same day.

Bridged XRP arrives on the EVM side as the **native gas token** (no wrapping step needed to pay gas).

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
  'https://rpc.xrplevm.org'
);

// Connect wallet
const wallet = new ethers.Wallet(process.env.PRIVATE_KEY, provider);
console.log('Address:', wallet.address);
console.log('Chain ID:', (await provider.getNetwork()).chainId);  // 1440000n

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

const XRPL_EVM_CHAIN_ID = 1440000;

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
        params: [{ chainId: '0x15F900' }]
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

---

## Related Files

- `knowledge/33-xrpl-evm-dev.md` — EVM sidechain development
- `knowledge/44-xrpl-evm-advanced.md` — advanced EVM ops
- `knowledge/50-xrpl-evm-sidechain.md` — EVM sidechain reference
