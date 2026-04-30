# Advanced XRPL EVM Sidechain Development

## Network Overview

The XRPL EVM Sidechain is an EVM-compatible blockchain that settles periodically to XRPL mainnet via a federated bridge. It uses the same wXRP token that represents XRP bridged from mainnet.

| Parameter | Value |
|-----------|-------|
| Chain ID | 1440002 (mainnet) / 1440001 (devnet) |
| Native token | wXRP (18 decimals) |
| Block time | ~3.5 seconds |
| Consensus | IBFT 2.0 (Istanbul BFT) |
| EVM version | London |
| RPC (devnet) | `https://rpc-evm-sidechain.xrpl.org` |
| Explorer (devnet) | `https://evm-sidechain.xrpl.org` |
| Faucet | `https://bridge.devnet.xrpl.org` |

---

## MetaMask / Wallet Network Config

```javascript
// Add XRPL EVM Sidechain to MetaMask programmatically
async function addXRPLEVMNetwork() {
  await window.ethereum.request({
    method: 'wallet_addEthereumChain',
    params: [{
      chainId: '0x15F902',           // 1440002 decimal
      chainName: 'XRPL EVM Sidechain',
      nativeCurrency: {
        name: 'wXRP',
        symbol: 'wXRP',
        decimals: 18,
      },
      rpcUrls: ['https://rpc-evm-sidechain.xrpl.org/'],
      blockExplorerUrls: ['https://evm-sidechain.xrpl.org/'],
    }],
  });
}
```

---

## Hardhat Project Setup

```bash
npm init -y
npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox ethers dotenv
npx hardhat init
```

```javascript
// hardhat.config.js
require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

module.exports = {
  solidity: {
    version: "0.8.24",
    settings: {
      optimizer: { enabled: true, runs: 200 },
      evmVersion: "london",   // Required: XRPL EVM uses London
    },
  },
  networks: {
    xrpl_devnet: {
      url: "https://rpc-evm-sidechain.xrpl.org/",
      chainId: 1440002,
      accounts: [process.env.PRIVATE_KEY],
      gasPrice: 10_000_000_000,  // 10 gwei
    },
    xrpl_testnet: {
      url: "https://rpc-evm-testnet.xrpl.org/",
      chainId: 1449000,
      accounts: [process.env.PRIVATE_KEY],
    },
  },
  etherscan: {
    apiKey: {
      xrpl_devnet: "no-api-key-needed",  // Explorer doesn't require key
    },
    customChains: [{
      network: "xrpl_devnet",
      chainId: 1440002,
      urls: {
        apiURL: "https://evm-sidechain.xrpl.org/api",
        browserURL: "https://evm-sidechain.xrpl.org",
      },
    }],
  },
};
```

---

## Deploying Contracts

```bash
# Deploy
npx hardhat run scripts/deploy.js --network xrpl_devnet

# Verify contract on block explorer
npx hardhat verify --network xrpl_devnet 0xContractAddress... "Constructor Arg 1"
```

```javascript
// scripts/deploy.js
const { ethers } = require("hardhat");

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying with:", deployer.address);
  console.log("Balance:", ethers.formatEther(await ethers.provider.getBalance(deployer.address)), "wXRP");

  const Factory = await ethers.getContractFactory("MyToken");
  const contract = await Factory.deploy(
    "My Token",
    "MTK",
    ethers.parseEther("1000000"),  // 1M tokens
  );
  await contract.waitForDeployment();

  const addr = await contract.getAddress();
  console.log("Deployed to:", addr);

  // Save deployment info
  const fs = require("fs");
  fs.writeFileSync("deployments/xrpl_devnet.json", JSON.stringify({
    address: addr,
    deployer: deployer.address,
    block: await ethers.provider.getBlockNumber(),
    timestamp: new Date().toISOString(),
  }, null, 2));
}

main().catch(e => { console.error(e); process.exit(1); });
```

---

## ERC-20 Token with XRPL-Specific Features

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

/**
 * XRPL-aligned ERC-20: has freeze and clawback capability
 * mirroring XRPL IOU semantics for regulated token issuers.
 */
contract XRPLAlignedToken is ERC20, Ownable, Pausable {
    mapping(address => bool) public frozen;
    bool public globalFreeze;

    event AccountFrozen(address indexed account, bool frozen);
    event GlobalFreezeSet(bool frozen);
    event Clawback(address indexed from, address indexed to, uint256 amount);

    constructor(string memory name, string memory symbol, uint256 initialSupply)
        ERC20(name, symbol)
        Ownable(msg.sender)
    {
        _mint(msg.sender, initialSupply);
    }

    modifier notFrozen(address account) {
        require(!globalFreeze, "Global freeze active");
        require(!frozen[account], "Account frozen");
        _;
    }

    function _update(address from, address to, uint256 amount)
        internal override
        notFrozen(from)
        whenNotPaused
    {
        super._update(from, to, amount);
    }

    function freezeAccount(address account, bool isFrozen) external onlyOwner {
        frozen[account] = isFrozen;
        emit AccountFrozen(account, isFrozen);
    }

    function setGlobalFreeze(bool isFrozen) external onlyOwner {
        globalFreeze = isFrozen;
        emit GlobalFreezeSet(isFrozen);
    }

    function clawback(address from, uint256 amount) external onlyOwner {
        // Force-transfer tokens back to issuer (mirrors XRPL Clawback)
        _transfer(from, owner(), amount);
        emit Clawback(from, owner(), amount);
    }
}
```

---

## Bridge: XRPL Mainnet ↔ EVM Sidechain

### How the Bridge Works
1. **Lock on XRPL:** User sends XRP to the bridge door account on mainnet with a destination tag
2. **Attestation:** Bridge federators observe the XRPL tx and reach consensus
3. **Mint on EVM:** Bridge contract mints equivalent wXRP on EVM sidechain
4. **Reverse:** EVM user burns wXRP → bridge mints XRP on XRPL mainnet

### Monitoring Bridge Events (Python Relayer)

```python
import asyncio, os
from web3 import Web3
from web3.middleware import geth_poa_middleware
import xrpl
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import Payment
from xrpl.transaction import submit_and_wait
from xrpl.wallet import Wallet

BRIDGE_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "sender", "type": "address"},
            {"indexed": False, "name": "destination", "type": "string"},  # XRPL address
            {"indexed": False, "name": "amount", "type": "uint256"},
        ],
        "name": "WithdrawInitiated",
        "type": "event",
    }
]

async def watch_bridge_events():
    w3 = Web3(Web3.HTTPProvider("https://rpc-evm-sidechain.xrpl.org/"))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    bridge = w3.eth.contract(
        address="0xBridgeContractAddress...",
        abi=BRIDGE_ABI,
    )
    xrpl_client = JsonRpcClient("https://xrplcluster.com")
    bridge_wallet = Wallet.from_secret(os.environ["BRIDGE_SECRET"])

    # Listen for withdrawal events
    event_filter = bridge.events.WithdrawInitiated.create_filter(fromBlock="latest")

    while True:
        for event in event_filter.get_new_entries():
            sender = event.args.sender
            xrpl_dest = event.args.destination
            amount_wei = event.args.amount
            amount_drops = int(amount_wei / 1e12)  # 18 decimals → 6 decimals

            print(f"Bridge withdraw: {amount_wei/1e18:.6f} wXRP → {xrpl_dest}")

            # Submit XRPL payment
            tx = Payment(
                account=bridge_wallet.classic_address,
                destination=xrpl_dest,
                amount=str(amount_drops),
                # Destination tag from event if available
            )
            resp = submit_and_wait(tx, xrpl_client, bridge_wallet)
            result = resp.result['meta']['TransactionResult']
            print(f"XRPL payout: {result}")

        await asyncio.sleep(5)

asyncio.run(watch_bridge_events())
```

### Depositing from XRPL to EVM

```python
# Lock XRP on XRPL mainnet → receive wXRP on EVM
from xrpl.models.transactions import Payment

BRIDGE_DOOR = "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh"  # Mainnet bridge door

def bridge_to_evm(
    client,
    sender: Wallet,
    evm_recipient: str,   # 0x... address
    xrp_amount: float,
    dest_tag: int = 0,
):
    """Send XRP to bridge; bridge mints wXRP on EVM for evm_recipient."""
    # EVM address is encoded in Memo field
    memo_data = evm_recipient.lower().replace("0x", "").encode("utf-8").hex().upper()

    tx = Payment(
        account=sender.classic_address,
        destination=BRIDGE_DOOR,
        amount=xrpl.utils.xrp_to_drops(str(xrp_amount)),
        destination_tag=dest_tag,
        memos=[{
            "Memo": {
                "MemoData": memo_data,
                "MemoType": "4445535441444452455353",  # "DESTADDRESS"
            }
        }],
    )
    return submit_and_wait(tx, client, sender)
```

---

## Precompile Contracts

The XRPL EVM includes custom precompiles that aren't in standard Ethereum:

```solidity
// Interface for XRPL mainnet account lookup precompile
interface IXRPLAccountInfo {
    function getAccountBalance(string calldata xrplAddress) external view returns (uint256 drops);
    function accountExists(string calldata xrplAddress) external view returns (bool);
}

contract XRPLPriceCheck {
    IXRPLAccountInfo constant XRPL_PRECOMPILE = IXRPLAccountInfo(0x0000000000000000000000000000000000000001);

    function checkMainnetBalance(string calldata addr) external view returns (uint256) {
        return XRPL_PRECOMPILE.getAccountBalance(addr);
    }
}
```

---

## Account Abstraction (ERC-4337) on XRPL EVM

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@account-abstraction/contracts/core/BaseAccount.sol";
import "@account-abstraction/contracts/interfaces/IEntryPoint.sol";

/**
 * Simple smart wallet supporting XRPL-style secp256k1 keys.
 * Users submit UserOperations; bundler pays gas in wXRP.
 */
contract XRPLSmartWallet is BaseAccount {
    address public owner;
    IEntryPoint private immutable _entryPoint;

    constructor(IEntryPoint entryPoint_, address owner_) {
        _entryPoint = entryPoint_;
        owner = owner_;
    }

    function entryPoint() public view override returns (IEntryPoint) {
        return _entryPoint;
    }

    function _validateSignature(
        PackedUserOperation calldata userOp,
        bytes32 userOpHash
    ) internal view override returns (uint256 validationData) {
        bytes32 ethHash = keccak256(abi.encodePacked("\x19Ethereum Signed Message:\n32", userOpHash));
        address signer = ECDSA.recover(ethHash, userOp.signature);
        return signer == owner ? 0 : SIG_VALIDATION_FAILED;
    }

    function execute(address target, uint256 value, bytes calldata data) external {
        _requireFromEntryPointOrOwner();
        (bool success, bytes memory result) = target.call{value: value}(data);
        require(success, string(result));
    }

    function _requireFromEntryPointOrOwner() internal view {
        require(msg.sender == address(_entryPoint) || msg.sender == owner, "Not authorized");
    }

    receive() external payable {}
}
```

---

## Yield Farming Pattern (Uniswap V2 Fork)

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * Single-asset staking vault — stake wXRP, earn reward tokens.
 * Simple, no complex AMM math.
 */
contract XRPStakingVault is ReentrancyGuard {
    IERC20 public immutable rewardToken;
    uint256 public rewardRate = 100;          // tokens per second per 1e18 wXRP
    uint256 public lastUpdateTime;
    uint256 public rewardPerTokenStored;

    mapping(address => uint256) public userRewardPerTokenPaid;
    mapping(address => uint256) public rewards;
    mapping(address => uint256) public balances;
    uint256 public totalSupply;

    event Staked(address indexed user, uint256 amount);
    event Withdrawn(address indexed user, uint256 amount);
    event RewardClaimed(address indexed user, uint256 amount);

    constructor(address rewardToken_) {
        rewardToken = IERC20(rewardToken_);
        lastUpdateTime = block.timestamp;
    }

    function rewardPerToken() public view returns (uint256) {
        if (totalSupply == 0) return rewardPerTokenStored;
        return rewardPerTokenStored + (
            (block.timestamp - lastUpdateTime) * rewardRate * 1e18 / totalSupply
        );
    }

    function earned(address account) public view returns (uint256) {
        return balances[account] * (rewardPerToken() - userRewardPerTokenPaid[account]) / 1e18
            + rewards[account];
    }

    modifier updateReward(address account) {
        rewardPerTokenStored = rewardPerToken();
        lastUpdateTime = block.timestamp;
        rewards[account] = earned(account);
        userRewardPerTokenPaid[account] = rewardPerTokenStored;
        _;
    }

    function stake(uint256 amount) external nonReentrant updateReward(msg.sender) {
        require(amount > 0, "Cannot stake 0");
        totalSupply += amount;
        balances[msg.sender] += amount;
        (bool success,) = address(0).call{value: amount}("");  // wXRP is native
        require(success, "Transfer failed");
        emit Staked(msg.sender, amount);
    }

    function withdraw(uint256 amount) external nonReentrant updateReward(msg.sender) {
        require(amount > 0 && balances[msg.sender] >= amount, "Invalid amount");
        totalSupply -= amount;
        balances[msg.sender] -= amount;
        payable(msg.sender).transfer(amount);
        emit Withdrawn(msg.sender, amount);
    }

    function claimReward() external nonReentrant updateReward(msg.sender) {
        uint256 reward = rewards[msg.sender];
        require(reward > 0, "Nothing to claim");
        rewards[msg.sender] = 0;
        rewardToken.transfer(msg.sender, reward);
        emit RewardClaimed(msg.sender, reward);
    }

    receive() external payable {}
}
```

---

## Web3.py Integration

```python
from web3 import Web3
from web3.middleware import geth_poa_middleware
import json, os

def connect_xrpl_evm() -> Web3:
    w3 = Web3(Web3.HTTPProvider("https://rpc-evm-sidechain.xrpl.org/"))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    assert w3.is_connected(), "Failed to connect to XRPL EVM"
    print(f"Connected. Chain ID: {w3.eth.chain_id}, Block: {w3.eth.block_number}")
    return w3

w3 = connect_xrpl_evm()
account = w3.eth.account.from_key(os.environ["PRIVATE_KEY"])

# Load contract
with open("artifacts/contracts/MyToken.sol/MyToken.json") as f:
    artifact = json.load(f)

contract = w3.eth.contract(
    address="0xDeployedAddress...",
    abi=artifact["abi"],
)

# Call view function
name = contract.functions.name().call()
balance = contract.functions.balanceOf(account.address).call()
print(f"Token: {name}, Balance: {w3.from_wei(balance, 'ether')}")

# Send transaction
nonce = w3.eth.get_transaction_count(account.address)
tx = contract.functions.transfer(
    "0xRecipient...",
    w3.to_wei(100, "ether"),
).build_transaction({
    "chainId": 1440002,
    "gas": 100_000,
    "gasPrice": w3.to_wei(10, "gwei"),
    "nonce": nonce,
})
signed = account.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print(f"Tx {tx_hash.hex()}: {'success' if receipt.status == 1 else 'failed'}")
```

---

## Oracle Integration (Flare FTSO)

XRPL EVM can use Flare's FTSO for XRP/USD price feeds via cross-chain messaging:

```solidity
// Interface to Flare FTSO price provider (deployed on Flare, accessible via Axelar GMP)
interface IFtsoRegistry {
    function getCurrentPriceWithDecimals(string calldata symbol)
        external view returns (uint256 price, uint256 timestamp, uint256 decimals);
}

contract XRPPriceFeed {
    IFtsoRegistry public immutable ftso;

    constructor(address ftsoAddress) {
        ftso = IFtsoRegistry(ftsoAddress);
    }

    function getXRPUSD() external view returns (uint256 price, uint256 decimals) {
        (uint256 p, , uint256 d) = ftso.getCurrentPriceWithDecimals("XRP");
        return (p, d);
    }

    // Human-readable: price / 10^decimals = USD value
    function getXRPUSDHuman() external view returns (string memory) {
        (uint256 p, , uint256 d) = ftso.getCurrentPriceWithDecimals("XRP");
        // Format: p / 10^d
        return string(abi.encodePacked(
            _uint2str(p / (10**d)),
            ".",
            _uint2str((p % (10**d)) * 100 / (10**d))  // 2 decimal places
        ));
    }
}
```

---

## Gas Estimation and Cost

```python
# Typical gas costs on XRPL EVM
GAS_COSTS = {
    "transfer_wXRP":   21_000,
    "erc20_transfer":  65_000,
    "erc20_approve":   46_000,
    "uniswap_swap":   150_000,
    "deploy_erc20":   800_000,
    "deploy_staking": 1_200_000,
}

GAS_PRICE_GWEI = 10  # Current default

def estimate_cost_wXRP(gas_units: int, gas_price_gwei: int = GAS_PRICE_GWEI) -> float:
    wei = gas_units * gas_price_gwei * 1e9
    return wei / 1e18

for op, gas in GAS_COSTS.items():
    cost = estimate_cost_wXRP(gas)
    print(f"{op:25s}: {cost:.8f} wXRP (≈ ${cost * 0.5:.6f} at $0.50/XRP)")
```

---

## Related Files
- `knowledge/33-xrpl-evm-dev.md` — basic EVM development guide
- `references/xrpl-evm-sidechain.md` — sidechain architecture overview
- `knowledge/35-xrpl-full-interop.md` — full interoperability patterns
- `knowledge/45-xrpl-ecosystem-complete.md` — ecosystem and project directory
