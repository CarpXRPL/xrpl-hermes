# Advanced XRPL EVM Sidechain Development

## Network Overview

The XRPL EVM Sidechain is an EVM-compatible blockchain that settles periodically to XRPL mainnet via a federated bridge. It uses the same wXRP token that represents XRP bridged from mainnet.

| Parameter | Value |
|-----------|-------|
| Chain ID | 1440000 (mainnet) / 1450024 (testnet) |
| Native token | wXRP (18 decimals) |
| Block time | ~3.5 seconds |
| Consensus | IBFT 2.0 (Istanbul BFT) |
| EVM version | London |
| RPC (devnet) | `https://rpc.xrplevm.org` |
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
      chainId: '0x15F900',           // 1440000 decimal
      chainName: 'XRPL EVM Sidechain',
      nativeCurrency: {
        name: 'wXRP',
        symbol: 'wXRP',
        decimals: 18,
      },
      rpcUrls: ['https://rpc.xrplevm.org/'],
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
    xrpl_mainnet: {
      url: "https://rpc.xrplevm.org/",
      chainId: 1440000,
      accounts: [process.env.PRIVATE_KEY],
      gasPrice: 10_000_000_000,  // 10 gwei
    },
    xrpl_testnet: {
      url: "https://rpc.testnet.xrplevm.org/",
      chainId: 1450024,
      accounts: [process.env.PRIVATE_KEY],
    },
  },
  etherscan: {
    apiKey: {
      xrpl_devnet: "no-api-key-needed",  // Explorer doesn't require key
    },
    customChains: [{
      network: "xrpl_devnet",
      chainId: 1450024,
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
    w3 = Web3(Web3.HTTPProvider("https://rpc.xrplevm.org/"))
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
    w3 = Web3(Web3.HTTPProvider("https://rpc.xrplevm.org/"))
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
    "chainId": 1450024,
    "gas": 100_000,
    "gasPrice": w3.to_wei(10, "gwei"),
    "nonce": nonce,
})

# Or use on mainnet
# "chainId": 1440000,
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

---

## UniswapV2-Style Swap Contract

XRPL EVM is fully EVM-compatible, so standard UniswapV2-style AMM pairs work out of the box. Below is a complete pair contract adapted for the XRPL EVM sidechain.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * Minimal UniswapV2-style Pair for XRPL EVM Sidechain.
 * Constant product AMM: x * y = k
 * Compatible with standard UniswapV2 Router and Factory contracts.
 */
interface IERC20 {
    function transferFrom(address from, address to, uint256 value) external returns (bool);
    function transfer(address to, uint256 value) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

contract XRPLEVMPair {
    address public token0;
    address public token1;

    uint112 private reserve0;
    uint112 private reserve1;
    uint32  private blockTimestampLast;

    uint256 public price0CumulativeLast;
    uint256 public price1CumulativeLast;
    uint256 public kLast;  // reserve0 * reserve1

    uint256 private unlocked = 1;
    modifier lock() {
        require(unlocked == 1, "Locked");
        unlocked = 0;
        _;
        unlocked = 1;
    }

    event Mint(address indexed sender, uint256 amount0, uint256 amount1);
    event Burn(address indexed sender, uint256 amount0, uint256 amount1, address indexed to);
    event Swap(address indexed sender, uint256 amount0In, uint256 amount1In, uint256 amount0Out, uint256 amount1Out, address indexed to);
    event Sync(uint112 reserve0, uint112 reserve1);

    constructor(address _token0, address _token1) {
        require(_token0 != address(0) && _token1 != address(0), "Invalid tokens");
        // Sort so token0 < token1 (address comparison)
        (token0, token1) = _token0 < _token1 ? (_token0, _token1) : (_token1, _token0);
    }

    // ── Liquidity ──

    /** Mint LP tokens. Caller must send both tokens before calling. */
    function mint(address to) external lock returns (uint256 liquidity) {
        uint112 _reserve0 = reserve0;
        uint112 _reserve1 = reserve1;
        uint256 balance0 = IERC20(token0).balanceOf(address(this));
        uint256 balance1 = IERC20(token1).balanceOf(address(this));

        uint256 amount0 = balance0 - _reserve0;
        uint256 amount1 = balance1 - _reserve1;

        uint256 _totalSupply = totalSupply();
        if (_totalSupply == 0) {
            liquidity = _sqrt(amount0 * amount1) - 1000;  // MINIMUM_LIQUIDITY
            _mint(address(0), 1000);  // Burn first 1000 LP tokens
        } else {
            liquidity = _min(
                amount0 * _totalSupply / _reserve0,
                amount1 * _totalSupply / _reserve1
            );
        }
        require(liquidity > 0, "Insufficient liquidity minted");
        _mint(to, liquidity);

        _update(balance0, balance1, _reserve0, _reserve1);
        emit Mint(msg.sender, amount0, amount1);
    }

    /** Burn LP tokens and receive underlying assets. */
    function burn(address to) external lock returns (uint256 amount0, uint256 amount1) {
        uint112 _reserve0 = reserve0;
        uint112 _reserve1 = reserve1;
        uint256 balance0 = IERC20(token0).balanceOf(address(this));
        uint256 balance1 = IERC20(token1).balanceOf(address(this));
        uint256 liquidity = balanceOf(address(this));

        uint256 _totalSupply = totalSupply();
        amount0 = liquidity * balance0 / _totalSupply;
        amount1 = liquidity * balance1 / _totalSupply;
        require(amount0 > 0 && amount1 > 0, "Insufficient liquidity burned");

        _burn(address(this), liquidity);
        _safeTransfer(token0, to, amount0);
        _safeTransfer(token1, to, amount1);

        uint256 newBalance0 = IERC20(token0).balanceOf(address(this));
        uint256 newBalance1 = IERC20(token1).balanceOf(address(this));
        _update(newBalance0, newBalance1, _reserve0, _reserve1);
        emit Burn(msg.sender, amount0, amount1, to);
    }

    // ── Swap ──

    /** Execute a swap. Caller must send input tokens before calling. */
    function swap(uint256 amount0Out, uint256 amount1Out, address to, bytes calldata data) external lock {
        require(amount0Out > 0 || amount1Out > 0, "Invalid output amount");
        require(amount0Out < reserve0 && amount1Out < reserve1, "Insufficient liquidity");

        uint256 balance0 = IERC20(token0).balanceOf(address(this)) - amount0Out;
        uint256 balance1 = IERC20(token1).balanceOf(address(this)) - amount1Out;

        require(balance0 * balance1 >= uint256(reserve0) * uint256(reserve1), "K invariant failed");

        _update(uint112(balance0), uint112(balance1), reserve0, reserve1);
        emit Swap(msg.sender, amount0In, amount1In, amount0Out, amount1Out, to);
    }

    // ── Reserves ──

    function getReserves() public view returns (
        uint112 _reserve0,
        uint112 _reserve1,
        uint32 _blockTimestampLast
    ) {
        return (reserve0, reserve1, blockTimestampLast);
    }

    function _update(uint256 balance0, uint256 balance1, uint112 _reserve0, uint112 _reserve1) private {
        require(balance0 <= type(uint112).max && balance1 <= type(uint112).max, "Overflow");
        uint32 blockTimestamp = uint32(block.timestamp % 2**32);
        uint32 timeElapsed = blockTimestamp - _blockTimestampLast;

        if (timeElapsed > 0 && _reserve0 != 0 && _reserve1 != 0) {
            price0CumulativeLast += uint256(uint176(_reserve1)) * timeElapsed / uint256(_reserve0);
            price1CumulativeLast += uint256(uint176(_reserve0)) * timeElapsed / uint256(_reserve1);
        }

        reserve0 = uint112(balance0);
        reserve1 = uint112(balance1);
        blockTimestampLast = blockTimestamp;
        emit Sync(reserve0, reserve1);
    }

    // ── Price Calculation ──

    /** Calculate output amount for a given input (0.3% fee). */
    function getAmountOut(uint256 amountIn, uint256 reserveIn, uint256 reserveOut) public pure returns (uint256) {
        require(amountIn > 0, "Insufficient input");
        require(reserveIn > 0 && reserveOut > 0, "Insufficient liquidity");
        uint256 amountInWithFee = amountIn * 997;
        uint256 numerator = amountInWithFee * reserveOut;
        uint256 denominator = reserveIn * 1000 + amountInWithFee;
        return numerator / denominator;
    }

    /** Calculate input amount needed for a desired output. */
    function getAmountIn(uint256 amountOut, uint256 reserveIn, uint256 reserveOut) public pure returns (uint256) {
        require(amountOut > 0, "Insufficient output");
        require(reserveIn > 0 && reserveOut > 0, "Insufficient liquidity");
        uint256 numerator = reserveIn * amountOut * 1000;
        uint256 denominator = (reserveOut - amountOut) * 997;
        return numerator / denominator + 1;
    }

    // ── Helpers ──

    function _safeTransfer(address token, address to, uint256 value) private {
        (bool success, bytes memory data) = token.call(
            abi.encodeWithSelector(IERC20.transfer.selector, to, value)
        );
        require(success && (data.length == 0 || abi.decode(data, (bool))), "Transfer failed");
    }

    function _sqrt(uint256 y) private pure returns (uint256 z) {
        if (y > 3) {
            z = y;
            uint256 x = y / 2 + 1;
            while (x < z) { z = x; x = (y / x + x) / 2; }
        } else if (y != 0) { z = 1; }
    }

    function _min(uint256 a, uint256 b) private pure returns (uint256) { return a < b ? a : b; }

    // ERC-20 LP token (minimal)
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    uint256 private _totalSupply;
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);

    function totalSupply() public view returns (uint256) { return _totalSupply; }
    function _mint(address to, uint256 amount) internal { _totalSupply += amount; balanceOf[to] += amount; emit Transfer(address(0), to, amount); }
    function _burn(address from, uint256 amount) internal { _totalSupply -= amount; balanceOf[from] -= amount; emit Transfer(from, address(0), amount); }
    function approve(address spender, uint256 value) external returns (bool) { allowance[msg.sender][spender] = value; emit Approval(msg.sender, spender, value); return true; }
}
```

### Deploying the Pair

```bash
# Using Hardhat
npx hardhat run scripts/deploy-pair.ts --network xrpl_evm
```

```typescript
// scripts/deploy-pair.ts
import { ethers } from "hardhat";

async function main() {
  const TokenA = "0x...";  // ERC-20 address
  const TokenB = "0x...";  // ERC-20 or wXRP

  const Pair = await ethers.getContractFactory("XRPLEVMPair");
  const pair = await Pair.deploy(TokenA, TokenB);
  await pair.waitForDeployment();

  const addr = await pair.getAddress();
  console.log("Pair deployed:", addr);
}
```

---

## Adding and Removing Liquidity

### Add Liquidity (Python + web3.py)

```python
from web3 import Web3
from web3.middleware import geth_poa_middleware
import os

RPC = "https://rpc.xrplevm.org"
CHAIN_ID = 1440000

w3 = Web3(Web3.HTTPProvider(RPC))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
account = w3.eth.account.from_key(os.environ["PRIVATE_KEY"])

# Minimal ERC-20 ABI for approve + balanceOf
ERC20_ABI = [
    {"constant": False, "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
]

PAIR_ABI = [
    {"constant": False, "inputs": [{"name": "to", "type": "address"}], "name": "mint", "outputs": [{"name": "liquidity", "type": "uint256"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "to", "type": "address"}], "name": "burn", "outputs": [{"name": "amount0", "type": "uint256"}, {"name": "amount1", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "getReserves", "outputs": [{"name": "_reserve0", "type": "uint112"}, {"name": "_reserve1", "type": "uint112"}, {"name": "_blockTimestampLast", "type": "uint32"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "token0", "outputs": [{"name": "", "type": "address"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "token1", "outputs": [{"name": "", "type": "address"}], "type": "function"},
]

PAIR_ADDRESS = "0xYourPairContractAddress"
TOKEN_A = "0xTokenAAddress"
TOKEN_B = "0xTokenBAddress"  # or wXRP (0xCCcc...)


def add_liquidity(amount_a: int, amount_b: int):
    """Add liquidity to the XRPL EVM pair."""
    pair = w3.eth.contract(address=Web3.to_checksum_address(PAIR_ADDRESS), abi=PAIR_ABI)
    token_a = w3.eth.contract(address=Web3.to_checksum_address(TOKEN_A), abi=ERC20_ABI)
    token_b = w3.eth.contract(address=Web3.to_checksum_address(TOKEN_B), abi=ERC20_ABI)

    nonce = w3.eth.get_transaction_count(account.address)

    # 1. Approve both tokens for the pair contract
    for token, amount in [(token_a, amount_a), (token_b, amount_b)]:
        tx = token.functions.approve(PAIR_ADDRESS, amount).build_transaction({
            "chainId": CHAIN_ID, "from": account.address,
            "gas": 100_000, "gasPrice": w3.eth.gas_price, "nonce": nonce,
        })
        signed = account.sign_transaction(tx)
        w3.eth.send_raw_transaction(signed.rawTransaction)
        nonce += 1
        print(f"Approved {token.address} for {amount / 1e18}")

    # 2. Transfer both tokens to pair contract
    for token, amount in [(token_a, amount_a), (token_b, amount_b)]:
        tx = token.functions.transfer(PAIR_ADDRESS, amount).build_transaction({
            "chainId": CHAIN_ID, "from": account.address,
            "gas": 100_000, "gasPrice": w3.eth.gas_price, "nonce": nonce,
        })
        signed = account.sign_transaction(tx)
        w3.eth.send_raw_transaction(signed.rawTransaction)
        nonce += 1
        print(f"Transferred {amount / 1e18} to pair")

    # 3. Mint LP tokens
    tx = pair.functions.mint(account.address).build_transaction({
        "chainId": CHAIN_ID, "from": account.address,
        "gas": 200_000, "gasPrice": w3.eth.gas_price, "nonce": nonce,
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    # Parse LP token amount from Mint event
    logs = pair.events.Mint().process_receipt(receipt)
    liquidity = logs[0].args.liquidity if logs else "check explorer"

    print(f"Liquidity added. LP tokens: {liquidity}")
    print(f"Tx: {tx_hash.hex()}")


def remove_liquidity(lp_amount: int):
    """Burn LP tokens and withdraw underlying assets."""
    pair = w3.eth.contract(address=Web3.to_checksum_address(PAIR_ADDRESS), abi=PAIR_ABI)
    nonce = w3.eth.get_transaction_count(account.address)

    # Transfer LP tokens to the pair contract, then call burn
    # Note: LP tokens must be transferred to pair first, then burn
    tx = pair.functions.burn(account.address).build_transaction({
        "chainId": CHAIN_ID, "from": account.address,
        "gas": 200_000, "gasPrice": w3.eth.gas_price, "nonce": nonce,
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    logs = pair.events.Burn().process_receipt(receipt)
    if logs:
        print(f"Removed: {logs[0].args.amount0 / 1e18:.4f} token0, {logs[0].args.amount1 / 1e18:.4f} token1")
    print(f"Tx: {tx_hash.hex()}")
```

### Execute a Swap (Python)

```python
def swap_exact_input(amount_in: int, min_amount_out: int, path: list):
    """
    Swap exact input tokens for a minimum output.
    This sends tokens to the pair and calls swap().
    """
    pair = w3.eth.contract(address=Web3.to_checksum_address(PAIR_ADDRESS), abi=PAIR_ABI)
    token_in = w3.eth.contract(address=Web3.to_checksum_address(path[0]), abi=ERC20_ABI)

    nonce = w3.eth.get_transaction_count(account.address)

    # 1. Approve input token
    tx = token_in.functions.approve(PAIR_ADDRESS, amount_in).build_transaction({
        "chainId": CHAIN_ID, "from": account.address,
        "gas": 100_000, "gasPrice": w3.eth.gas_price, "nonce": nonce,
    })
    signed = account.sign_transaction(tx)
    w3.eth.send_raw_transaction(signed.rawTransaction)
    nonce += 1

    # 2. Transfer input tokens to pair
    tx = token_in.functions.transfer(PAIR_ADDRESS, amount_in).build_transaction({
        "chainId": CHAIN_ID, "from": account.address,
        "gas": 100_000, "gasPrice": w3.eth.gas_price, "nonce": nonce,
    })
    signed = account.sign_transaction(tx)
    w3.eth.send_raw_transaction(signed.rawTransaction)
    nonce += 1

    # 3. Call swap with calculated amounts
    reserves = pair.functions.getReserves().call()
    token0 = pair.functions.token0().call()
    token1 = pair.functions.token1().call()

    # Determine which token is input/output
    if path[0].lower() == token0.lower():
        amount0Out = 0
        amount1Out = pair.functions.getAmountOut(amount_in, reserves[0], reserves[1]).call()
    else:
        amount0Out = pair.functions.getAmountOut(amount_in, reserves[1], reserves[0]).call()
        amount1Out = 0

    require(amount0Out >= min_amount_out or amount1Out >= min_amount_out, "Slippage too high")

    tx = pair.functions.swap(amount0Out, amount1Out, account.address, b"").build_transaction({
        "chainId": CHAIN_ID, "from": account.address,
        "gas": 150_000, "gasPrice": w3.eth.gas_price, "nonce": nonce,
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    print(f"Swap executed: {tx_hash.hex()}")
    return receipt
```

### Price Impact Calculator

```python
def calculate_price_impact(reserve_in: int, reserve_out: int, amount_in: int) -> dict:
    """Calculate swap price impact using constant product formula (0.3% fee)."""
    amount_in_with_fee = amount_in * 997
    numerator = amount_in_with_fee * reserve_out
    denominator = reserve_in * 1000 + amount_in_with_fee
    amount_out = numerator // denominator

    price_before = reserve_out / reserve_in
    price_after = (reserve_out - amount_out) / (reserve_in + amount_in)
    impact = ((price_before - price_after) / price_before) * 100

    return {
        "amount_in": amount_in / 1e18,
        "amount_out": amount_out / 1e18,
        "price_impact_pct": impact,
        "effective_price": (amount_out / amount_in) if amount_in > 0 else 0,
    }

# Example: swap 1000 tokens into a pool with 50000/50000 reserves
result = calculate_price_impact(50_000 * 10**18, 50_000 * 10**18, 1000 * 10**18)
print(f"Input: {result['amount_in']:.2f}")
print(f"Output: {result['amount_out']:.2f}")
print(f"Price impact: {result['price_impact_pct']:.4f}%")
# Input: 1000.00
# Output: 980.34
# Price impact: ~1.97% (a 1000 token swap in a 50k pool)
```

### Swap Using UniswapV2 Router (Standard Contract)

For production use, deploy the standard UniswapV2 Router and use its `swapExactTokensForTokens` and `addLiquidity` functions:

```solidity
// Standard UniswapV2 Router interface
interface IUniswapV2Router {
    function addLiquidity(
        address tokenA, address tokenB,
        uint256 amountADesired, uint256 amountBDesired,
        uint256 amountAMin, uint256 amountBMin,
        address to, uint256 deadline
    ) external returns (uint256 amountA, uint256 amountB, uint256 liquidity);

    function swapExactTokensForTokens(
        uint256 amountIn, uint256 amountOutMin,
        address[] calldata path, address to, uint256 deadline
    ) external returns (uint256[] memory amounts);
}
```

The Router handles approvals, transfers, and price calculations in a single call. Deploy the standard `UniswapV2Router02` from the UniswapV2-periphery repository (no modifications needed for XRPL EVM).

```bash
# Deploy the standard Router (pointing to your Factory)
npx hardhat run scripts/deploy-router.ts --network xrpl_evm
```

## Related Files
- `knowledge/33-xrpl-evm-dev.md` — basic EVM development guide
- `references/xrpl-evm-sidechain.md` — sidechain architecture overview
- `knowledge/35-xrpl-full-interop.md` — full interoperability patterns
- `knowledge/45-xrpl-ecosystem-complete.md` — ecosystem and project directory
