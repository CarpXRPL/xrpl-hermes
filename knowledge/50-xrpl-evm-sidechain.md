# XRPL EVM Sidechain — Smart Contracts on XRPL

## Overview

The XRPL EVM Sidechain is an Ethereum Virtual Machine (EVM) compatible chain for the XRP Ledger ecosystem. It enables Solidity smart contracts, ERC-20/ERC-721 tokens, and full Ethereum toolchain compatibility (Hardhat, Foundry, ethers.js, web3.py) while connecting to XRPL L1 through Axelar bridge tooling.

**Why it matters:** XRPL L1 has no Turing-complete smart contracts (by design for speed/cost). The EVM Sidechain brings programmable DeFi to the XRPL ecosystem without changing the core ledger.

**Status:** Mainnet live. Active development by Ripple and the XRPL community.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  XRPL L1                      XRPL EVM Sidechain            │
│  (native XRP,                 (Chain ID: 1440000)            │
│   trust lines,                (Solidity + EVM)               │
│   DEX, AMM)                                                  │
│         │                           │                        │
│         └──────── Axelar bridge tooling ─────────────────────┘│
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Bridge Components (current integration model)

| Component | Role |
|-----------|------|
| Axelar validators / gateway | Observe and authorize cross-chain messages through the Axelar network |
| Squid Router UI | Recommended user-facing route linked from official XRPL EVM docs |
| EVM native XRP | XRP arrives on the EVM side as the native gas token |
| Optional WXRP wrapper | ERC-20 wrapper for DeFi integrations; verify the current contract on the live explorer before use |

### Deposit Flow (XRPL L1 → EVM)

```
1. User routes through the official XRPL EVM / Squid / Axelar flow
2. Axelar observes and authorizes the cross-chain transfer
3. XRP is delivered on the EVM side as native gas-token balance
4. Timing and gateway details are route-dependent; verify against current official docs before building production UX
```

### Withdrawal Flow (EVM → XRPL L1)

```
1. User routes through the current Axelar/Squid withdrawal path
2. Axelar validates the source-chain event and coordinates release/delivery
3. XRP arrives at the requested XRPL address if the route succeeds
4. Timing, fees, and gateway details must be read from live official docs/UI
```

---

## Network Details

| Property | Mainnet | Testnet |
|----------|---------|---------|
| Chain ID | 1440000 | 1449000 |
| RPC URL | https://rpc.xrplevm.org | https://rpc.testnet.xrplevm.org |
| Block Explorer | https://explorer.xrplevm.org | https://explorer.testnet.xrplevm.org |
| Gas Token | XRP (native, bridged via Axelar) | test XRP |
| Block Time | ~4 seconds | ~4 seconds |
| Consensus | CometBFT PoS (Cosmos SDK chain) | CometBFT PoS |

*Verified 2026-06-10 against docs.xrplevm.org and live explorer probes; mainnet launched 2025-06-30. Re-check the official docs before relying on endpoints — see `knowledge/65-agent-freshness-and-source-policy.md`.*
| EVM Version | London | London |

---

## Python: Deploy and Interact with EVM Sidechain

### Setup

```python
from web3 import Web3
from eth_account import Account
import json

# Connect to XRPL EVM Sidechain
XRPL_EVM_RPC = "https://rpc.xrplevm.org"
XRPL_EVM_CHAIN_ID = 1440000

w3 = Web3(Web3.HTTPProvider(XRPL_EVM_RPC))
print(f"Connected: {w3.is_connected()}")
print(f"Chain ID: {w3.eth.chain_id}")  # Should be 1440000
print(f"Block: {w3.eth.block_number}")
```

### Deploy ERC-20 Token

```python
# ERC-20 ABI (minimal)
ERC20_ABI = [
    {"inputs": [{"name": "_initialSupply", "type": "uint256"}], "stateMutability": "nonpayable", "type": "constructor"},
    {"inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"type": "uint256"}], "type": "function"},
    {"inputs": [{"name": "to", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "transfer", "outputs": [{"type": "bool"}], "type": "function"},
    {"inputs": [], "name": "totalSupply", "outputs": [{"type": "uint256"}], "type": "function"},
    {"inputs": [], "name": "name", "outputs": [{"type": "string"}], "type": "function"},
    {"inputs": [], "name": "symbol", "outputs": [{"type": "string"}], "type": "function"},
]

ERC20_BYTECODE = "0x..."  # Compile your Solidity contract

def deploy_erc20(private_key: str, name: str, symbol: str, initial_supply: int) -> dict:
    """Deploy an ERC-20 token on XRPL EVM Sidechain."""
    account = Account.from_key(private_key)
    nonce = w3.eth.get_transaction_count(account.address)

    # Build deployment transaction
    contract = w3.eth.contract(abi=ERC20_ABI, bytecode=ERC20_BYTECODE)
    tx = contract.constructor(initial_supply).build_transaction({
        "chainId": XRPL_EVM_CHAIN_ID,
        "from": account.address,
        "nonce": nonce,
        "gas": 2_000_000,
        "maxFeePerGas": w3.eth.gas_price,
        "maxPriorityFeePerGas": w3.to_wei(1, "gwei")
    })

    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    return {
        "contract_address": receipt["contractAddress"],
        "tx_hash": tx_hash.hex(),
        "block": receipt["blockNumber"],
        "gas_used": receipt["gasUsed"],
        "explorer": f"https://explorer.xrplevm.org/tx/{tx_hash.hex()}"
    }
```

### Interact with Deployed Contract

```python
def get_erc20_balance(contract_address: str, holder_address: str) -> dict:
    """Get ERC-20 token balance on XRPL EVM Sidechain."""
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(contract_address),
        abi=ERC20_ABI
    )
    balance = contract.functions.balanceOf(
        Web3.to_checksum_address(holder_address)
    ).call()
    name = contract.functions.name().call()
    symbol = contract.functions.symbol().call()
    total_supply = contract.functions.totalSupply().call()

    return {
        "holder": holder_address,
        "token": f"{name} ({symbol})",
        "balance": balance,
        "balance_normalized": balance / 10**18,
        "total_supply": total_supply / 10**18
    }

def transfer_erc20(
    private_key: str,
    contract_address: str,
    to_address: str,
    amount: int
) -> str:
    """Transfer ERC-20 tokens."""
    account = Account.from_key(private_key)
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(contract_address),
        abi=ERC20_ABI
    )

    tx = contract.functions.transfer(
        Web3.to_checksum_address(to_address),
        amount
    ).build_transaction({
        "chainId": XRPL_EVM_CHAIN_ID,
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": 100_000,
        "maxFeePerGas": w3.eth.gas_price,
        "maxPriorityFeePerGas": w3.to_wei(1, "gwei")
    })

    signed = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_hash.hex()
```

---

## Python: Bridge XRP from XRPL L1 to EVM Sidechain

Do **not** build bridge payments from a hardcoded door account or copied tutorial address. The current production path is Axelar/Squid; gateway addresses, contract addresses, route fees, and memo/tag formats are live integration details.

Safe automation pattern:

```python
import os
from web3 import Web3

XRPL_EVM_RPC = "https://rpc.xrplevm.org"
w3 = Web3(Web3.HTTPProvider(XRPL_EVM_RPC))


def bridge_integration_preflight() -> dict:
    """Collect values your app must verify from official docs/UI before enabling bridge actions."""
    return {
        "official_docs": "https://docs.xrplevm.org",
        "recommended_ui": "https://app.squidrouter.com",
        "mainnet_explorer": "https://explorer.xrplevm.org",
        "chain_id": w3.eth.chain_id,  # should be 1440000
        "gateway_from_env": os.environ.get("AXELAR_XRPL_GATEWAY", "unset"),
        "security_rule": "Do not submit a live bridge transaction unless the gateway/route was verified from official sources today.",
    }


def check_native_xrp_balance(evm_address: str) -> dict:
    """Native XRP balance on the EVM sidechain, denominated with 18 decimals."""
    balance_wei = w3.eth.get_balance(Web3.to_checksum_address(evm_address))
    return {
        "address": evm_address,
        "xrp_balance": balance_wei / 10**18,
        "wei": balance_wei,
    }
```

For ERC-20 wrapped XRP integrations, verify the current wrapper contract on `https://explorer.xrplevm.org` and treat it as application configuration, not a constant baked into docs.

---

## Solidity: EVM Sidechain Smart Contracts

### ERC-20 Token

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract XRPLToken is ERC20, Ownable {
    constructor(
        string memory name,
        string memory symbol,
        uint256 initialSupply
    ) ERC20(name, symbol) Ownable(msg.sender) {
        _mint(msg.sender, initialSupply * 10**decimals());
    }

    function mint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount);
    }
}
```

### Simple DEX

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract SimpleDEX {
    mapping(address => mapping(address => uint256)) public liquidity;

    function addLiquidity(
        address tokenA,
        address tokenB,
        uint256 amountA,
        uint256 amountB
    ) external {
        IERC20(tokenA).transferFrom(msg.sender, address(this), amountA);
        IERC20(tokenB).transferFrom(msg.sender, address(this), amountB);
        liquidity[tokenA][tokenB] += amountA;
        liquidity[tokenB][tokenA] += amountB;
    }

    function swap(
        address tokenIn,
        address tokenOut,
        uint256 amountIn
    ) external returns (uint256 amountOut) {
        uint256 reserveIn = IERC20(tokenIn).balanceOf(address(this));
        uint256 reserveOut = IERC20(tokenOut).balanceOf(address(this));

        // Constant product formula: x * y = k (0.3% fee)
        uint256 amountInWithFee = amountIn * 997;
        amountOut = (amountInWithFee * reserveOut) /
                    (reserveIn * 1000 + amountInWithFee);

        IERC20(tokenIn).transferFrom(msg.sender, address(this), amountIn);
        IERC20(tokenOut).transfer(msg.sender, amountOut);
    }
}
```

---

## Hardhat Configuration

```javascript
// hardhat.config.js
require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

module.exports = {
  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: { enabled: true, runs: 200 }
    }
  },
  networks: {
    xrplEVM: {
      url: "https://rpc.xrplevm.org",
      chainId: 1440000,
      accounts: [process.env.PRIVATE_KEY],
      timeout: 60000
    },
    xrplEVMTestnet: {
      url: "https://rpc.testnet.xrplevm.org",
      chainId: 1449000,
      accounts: [process.env.PRIVATE_KEY]
    }
  },
  etherscan: {
    apiKey: {
      xrplEVM: "no-api-key-needed"
    },
    customChains: [
      {
        network: "xrplEVM",
        chainId: 1440000,
        urls: {
          apiURL: "https://explorer.xrplevm.org/api",
          browserURL: "https://explorer.xrplevm.org"
        }
      }
    ]
  }
};
```

```javascript
// scripts/deploy.js
const { ethers } = require("hardhat");

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying from:", deployer.address);
  console.log("Balance:", ethers.formatEther(await ethers.provider.getBalance(deployer.address)), "wXRP");

  const Token = await ethers.getContractFactory("XRPLToken");
  const token = await Token.deploy("My Token", "MYT", 1_000_000);
  await token.waitForDeployment();

  console.log("Token deployed to:", await token.getAddress());
}

main().catch(console.error);
```

## Foundry Configuration

```bash
# foundry.toml
[profile.default]
src = "src"
out = "out"
libs = ["lib"]

[rpc_endpoints]
xrpl_evm = "https://rpc.xrplevm.org"
xrpl_evm_testnet = "https://rpc.testnet.xrplevm.org"
```

```bash
# Deploy
forge create src/Token.sol:XRPLToken \
  --rpc-url https://rpc.xrplevm.org \
  --private-key $PRIVATE_KEY \
  --constructor-args "My Token" "MYT" 1000000

# Verify
forge verify-contract \
  --chain-id 1440000 \
  --rpc-url https://rpc.xrplevm.org \
  --constructor-args $(cast abi-encode "constructor(string,string,uint256)" "My Token" "MYT" 1000000) \
  $CONTRACT_ADDRESS \
  src/Token.sol:XRPLToken
```

---

## JSON: Bridge Transaction Examples

### Deposit XRP from L1 to EVM Sidechain

```json
{
  "TransactionType": "Payment",
  "Account": "rSenderXRPLAddress",
  "Destination": "rBridgeGatewayAccount",
  "Amount": "10000000",
  "DestinationTag": 2345678901,
  "Fee": "12",
  "Sequence": 123456,
  "Memos": [
    {
      "Memo": {
        "MemoType": "6272696467655F61646472657373",
        "MemoData": "307861626364656637383930616263646566373839306162636465663738393031"
      }
    }
  ]
}
```

### EVM Withdrawal to XRPL L1 (Solidity call)

```json
{
  "function": "withdraw(address,uint256)",
  "parameters": {
    "xrplAddress": "rDestinationXRPLAddress",
    "amountDrops": "10000000"
  },
  "contract": "0xBridgeContractAddress",
  "chain_id": 1440000
}
```

---

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `https://rpc.xrplevm.org` | JSON-RPC endpoint (ETH compatible) |
| `https://explorer.xrplevm.org` | Block explorer UI |
| `https://explorer.xrplevm.org/api` | Explorer REST API |
| `wss://rpc.xrplevm.org/ws/ws` | WebSocket endpoint |

```python
import httpx

async def get_evm_sidechain_info() -> dict:
    """Get EVM sidechain network info."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://rpc.xrplevm.org",
            json={"jsonrpc": "2.0", "method": "eth_chainId", "params": [], "id": 1}
        )
        chain_id = int(response.json()["result"], 16)

        block_resp = await client.post(
            "https://rpc.xrplevm.org",
            json={"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 2}
        )
        block = int(block_resp.json()["result"], 16)

        gas_resp = await client.post(
            "https://rpc.xrplevm.org",
            json={"jsonrpc": "2.0", "method": "eth_gasPrice", "params": [], "id": 3}
        )
        gas_price_wei = int(gas_resp.json()["result"], 16)

    return {
        "chain_id": chain_id,
        "latest_block": block,
        "gas_price_gwei": gas_price_wei / 10**9,
        "explorer": "https://explorer.xrplevm.org"
    }

async def get_account_balance_evm(address: str) -> dict:
    """Get wXRP (native gas) balance on EVM Sidechain."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://rpc.xrplevm.org",
            json={
                "jsonrpc": "2.0",
                "method": "eth_getBalance",
                "params": [address, "latest"],
                "id": 1
            }
        )
        balance_wei = int(response.json()["result"], 16)

    return {
        "address": address,
        "wxrp_balance": balance_wei / 10**18,
        "wei": balance_wei
    }
```

---

## Error Handling Patterns

```python
from web3.exceptions import ContractLogicError, TransactionNotFound

class EVMSidechainError(Exception):
    pass

class BridgeError(EVMSidechainError):
    pass

class InsufficientGasError(EVMSidechainError):
    pass

def safe_send_evm_transaction(
    private_key: str,
    to: str,
    data: bytes,
    value: int = 0,
    gas_limit: int = 200_000
) -> str:
    """Send EVM transaction with error handling and gas estimation."""
    account = Account.from_key(private_key)

    try:
        # Estimate gas first
        estimated_gas = w3.eth.estimate_gas({
            "from": account.address,
            "to": Web3.to_checksum_address(to),
            "data": data,
            "value": value
        })
        gas = int(estimated_gas * 1.2)  # 20% buffer
    except ContractLogicError as e:
        raise EVMSidechainError(f"Transaction would revert: {e}")
    except Exception as e:
        gas = gas_limit  # Fall back to provided limit
        print(f"Gas estimation failed, using {gas}: {e}")

    # Check balance
    balance = w3.eth.get_balance(account.address)
    gas_price = w3.eth.gas_price
    required = gas * gas_price + value

    if balance < required:
        raise InsufficientGasError(
            f"Need {required / 10**18:.6f} wXRP, have {balance / 10**18:.6f}"
        )

    nonce = w3.eth.get_transaction_count(account.address)
    tx = {
        "chainId": XRPL_EVM_CHAIN_ID,
        "from": account.address,
        "to": Web3.to_checksum_address(to),
        "data": data,
        "value": value,
        "nonce": nonce,
        "gas": gas,
        "maxFeePerGas": gas_price,
        "maxPriorityFeePerGas": w3.to_wei(1, "gwei")
    }

    signed = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)

    try:
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        if receipt["status"] == 0:
            raise EVMSidechainError(f"Transaction reverted: {tx_hash.hex()}")
        return tx_hash.hex()
    except TransactionNotFound:
        raise EVMSidechainError(f"Transaction not found after timeout: {tx_hash.hex()}")
```

---

## Bridge Security Model

| Property | Detail |
|----------|--------|
| Trust model | Federated (semi-trusted federators) |
| Federator count | Small fixed set (Ripple-operated initially) |
| Signing requirement | Multi-sig threshold |
| Fraud detection | Monitoring + emergency pause |
| Rate limits | Bridge withdrawal limits enforced |
| Slashing | None (not permissionless validator set) |
| Risk | Federator compromise or collusion |

The federated model differs from Axelar (permissionless validator set). This is a known tradeoff for the current XRPL EVM Sidechain — more centralized than Axelar but simpler and faster.

---

## Use Cases

| Use Case | Implementation |
|----------|---------------|
| DeFi lending | Aave/Compound fork on EVM sidechain |
| DEX | Uniswap v2/v3 fork with wXRP pairs |
| NFT marketplace | OpenSea-style ERC-721 marketplace |
| Stablecoin protocols | RLUSD on EVM, collateralized by wXRP |
| Token launchpad | Fairlaunch contracts for new tokens |
| Bridges | Connect EVM sidechain to Ethereum/Polygon |
| Options/derivatives | Put/call options on wXRP |

---

## Resources

- XRPL EVM Sidechain docs: https://docs.xrplevm.org
- Block explorer: https://explorer.xrplevm.org
- RPC endpoint: https://rpc.xrplevm.org
- Bridge UI: https://bridge.xrpl.org
- Testnet faucet: https://faucet.xrplevm.org (XRPL EVM Sidechain testnet; may rate-limit)
- GitHub: https://github.com/xrplf/xbridge-cli

---

## Related Files

- `52-xrpl-l1-reference.md` — XRPL L1 for originating the bridge deposit
- `53-xrpl-wallets-auth.md` — MetaMask setup for EVM Sidechain
- `55-xrpl-sidechain-interop.md` — Full interoperability patterns between L1 and EVM
- `46-xrpl-axelar-bridge.md` — Axelar: alternative bridge to external EVM chains
- `49-xrpl-flare-ftso.md` — Flare as alternative EVM environment for XRPL assets
