# XRPL Sidechain Interop — Federated Bridge, EVM, Axelar GMP, Token Representation

This file describes practical XRPL L1 to EVM sidechain interop patterns using public endpoints.
Use `https://xrplcluster.com` for XRPL L1 JSON-RPC, `https://rpc.xrplevm.org` for EVM JSON-RPC, and `https://xahau.network` when Hook-style sidecar verification is needed.

## Interop map
- XRPL L1: native XRP, issued currencies, trust lines, DEX, AMM, fast settlement.
- XRPL EVM Sidechain: Solidity contracts, ERC-20/ERC-721, EVM tooling, gas paid in XRP representation.
- Federated bridge: watches one chain, signs mint/release or burn/release transactions on the other.
- Axelar GMP: generalized cross-chain messages for contract calls and token movement across supported chains.
- Token representation: locked L1 asset represented as wrapped EVM token or issued currency representation.

## Endpoint checks
```python
import httpx

def xrpl(method: str, params: dict | None = None) -> dict:
    response = httpx.post("https://xrplcluster.com", json={"method": method, "params": [params or {}]}, timeout=20)
    response.raise_for_status()
    return response.json()["result"]

def evm(method: str, params: list | None = None) -> str:
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []}
    response = httpx.post("https://rpc.xrplevm.org", json=payload, timeout=20)
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise RuntimeError(data["error"])
    return data["result"]

print("xrpl ledger", xrpl("ledger_current")["ledger_current_index"])
print("evm chain", int(evm("eth_chainId"), 16))
print("evm block", int(evm("eth_blockNumber"), 16))
```

## Federated bridge mechanics
- Bridge account on XRPL receives deposits and releases withdrawals.
- Bridge contract on EVM mints and burns wrapped representations.
- Witnesses observe validated ledgers and finalized EVM blocks.
- Federators sign bridge actions once quorum rules are satisfied.
- Replay protection uses transaction hash, ledger index, source chain id, destination chain id, and nonce.
- Minting should wait for validated XRPL ledgers and enough EVM confirmations per bridge policy.
- Withdrawals should burn or lock EVM tokens before XRPL release.
- Emergency pause should stop mint and release paths independently.
- Accounting must reconcile locked supply on L1 against minted supply on EVM.
- Operators should publish bridge account, contract addresses, signer set, and audit history.

## XRPL deposit transaction
A common bridge deposit sends XRP to a bridge account and includes the destination EVM address in a memo or destination tag scheme.
```python
import os
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import Payment
from xrpl.transaction import submit_and_wait
from xrpl.wallet import Wallet

client = JsonRpcClient(os.getenv("XRPL_RPC", "https://xrplcluster.com"))
wallet = Wallet.from_seed(os.environ["XRPL_SEED"])
bridge_account = os.environ["XRPL_BRIDGE_ACCOUNT"]
evm_address = os.environ["DESTINATION_EVM_ADDRESS"].lower().removeprefix("0x")

payment = Payment(
    account=wallet.classic_address,
    destination=bridge_account,
    amount="10000000",
    memos=[{
        "Memo": {
            "MemoType": "65766d5f64657374696e6174696f6e",
            "MemoFormat": "746578742f686578",
            "MemoData": evm_address
        }
    }]
)

result = submit_and_wait(payment, client, wallet)
print(result.result["hash"])
```

## Deposit event watcher
```python
import httpx

BRIDGE_ACCOUNT = "rBridgeAccountExample"

def account_tx(marker=None):
    params = {"account": BRIDGE_ACCOUNT, "ledger_index_min": -1, "ledger_index_max": -1, "limit": 20}
    if marker:
        params["marker"] = marker
    response = httpx.post("https://xrplcluster.com", json={"method": "account_tx", "params": [params]}, timeout=20)
    response.raise_for_status()
    return response.json()["result"]

for item in account_tx().get("transactions", []):
    tx = item.get("tx_json") or item.get("tx")
    meta = item.get("meta")
    if tx and tx.get("TransactionType") == "Payment" and meta.get("TransactionResult") == "tesSUCCESS":
        print(tx.get("hash"), tx.get("Amount"), tx.get("Memos"))
```

## EVM mint call shape
Bridge contracts vary. This shows the JSON-RPC transaction pattern after federator quorum signs or authorizes minting.
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "eth_sendRawTransaction",
  "params": [
    "0x02f901...signed_bridge_mint_transaction"
  ]
}
```

## EVM withdrawal submission with httpx JSON-RPC
```python
import os
from eth_account import Account
from eth_account.typed_transactions import DynamicFeeTransaction
import httpx

account = Account.from_key(os.environ["EVM_PRIVATE_KEY"])
EVM_RPC = "https://rpc.xrplevm.org"

def eth(method: str, params: list) -> str:
    response = httpx.post(EVM_RPC, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params}, timeout=20)
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise RuntimeError(data["error"])
    return data["result"]

nonce = int(eth("eth_getTransactionCount", [account.address, "pending"]), 16)
chain_id = int(eth("eth_chainId", []), 16)
gas_price = int(eth("eth_gasPrice", []), 16)

# Replace data with ABI-encoded withdrawToXrpl(xrplAddress, amount) calldata from your bridge ABI.
tx = DynamicFeeTransaction.from_dict({
    "chainId": chain_id,
    "nonce": nonce,
    "to": os.environ["EVM_BRIDGE_CONTRACT"],
    "value": 0,
    "gas": 150000,
    "maxFeePerGas": gas_price,
    "maxPriorityFeePerGas": 0,
    "data": os.environ["WITHDRAW_CALLDATA"],
})
signed = Account.sign_transaction(tx.as_dict(), os.environ["EVM_PRIVATE_KEY"])
print(eth("eth_sendRawTransaction", [signed.raw_transaction.hex()]))
```

## Axelar GMP conceptual flow
- Source contract calls Axelar Gateway with destination chain, destination contract, and payload.
- Gas service receives native gas payment for relayer execution.
- Axelar validators observe and approve the command.
- Destination gateway marks the command executable.
- Destination contract executes payload through `execute` or token-aware handlers.
- Application stores command id and source transaction hash for idempotency.
- Refund handling returns unused gas to the configured refund address.
- Payloads should include app nonce, source account, destination account, token id, amount, and deadline.

## Axelar GMP payload JSON
```json
{
  "source_chain": "xrpl-evm",
  "destination_chain": "ethereum",
  "source_address": "0xSourceContract",
  "destination_address": "0xDestinationContract",
  "payload": {
    "action": "creditDeposit",
    "xrpl_tx_hash": "ABCDEF0123456789",
    "xrpl_account": "rUserClassicAddress",
    "evm_recipient": "0xRecipient",
    "asset": "XRP",
    "amount": "10000000",
    "nonce": "deposit-000001"
  }
}
```

## Token representation patterns
- **Lock and mint**: XRP locked on XRPL bridge account; ERC-20 wrapped XRP minted on EVM.
- **Burn and release**: Wrapped token burned on EVM; XRP released from XRPL bridge account.
- **Issuer mirror**: XRPL issued currency represented by ERC-20 with issuer metadata and redemption policy.
- **Canonical sidechain token**: Token originates on EVM and is represented on XRPL as issued currency.
- **Synthetic token**: No direct redeemability; price exposure maintained by collateral or oracle policy.
- **Pool share representation**: XRPL AMM LP exposure represented as EVM receipt token for strategy contracts.
- **NFT mirror**: XRPL NFT represented by ERC-721 with escrow or burn/mint policy.
- **Message-only bridge**: No asset movement; XRPL payment event triggers EVM contract action.

## Bridge reconciliation
```python
from decimal import Decimal

locked_xrp_drops = Decimal("100000000000")
wrapped_supply_wei = Decimal("100000000000000000000000")
wrapped_supply_drops = wrapped_supply_wei / Decimal(10) ** 12

if locked_xrp_drops < wrapped_supply_drops:
    raise RuntimeError("wrapped supply exceeds locked XRP")
print("bridge solvent")
```

## Security checklist
- Publish bridge account and verify all deposits target that exact account.
- Require validated XRPL ledgers before minting.
- Require finalized or policy-confirmed EVM blocks before XRPL release.
- Deduplicate by source chain, source transaction hash, log index, and nonce.
- Use threshold signatures or multisig for federator actions.
- Rotate federator keys through a timelocked governance process.
- Pause deposits and withdrawals separately.
- Rate-limit large withdrawals and add manual review thresholds.
- Keep a public supply dashboard comparing locked and minted balances.
- Write integration tests for replay, wrong destination, wrong amount, and stale nonce cases.

## Practical Interop Notes

### Withdrawal (EVM → XRPL)
- Wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Include the EVM burn tx hash in the XRPL Payment memo for the bridge to validate against its event log.
- Use a unique nonce per withdrawal to prevent replay if EVM → Axelar → bridge fails and must be retried.

### Federated Bridge Operations
- Sign exactly one command for each source event and store signer receipts for audit.
- Federators should run on separate infrastructure; use threshold signatures (M-of-N) so no single federator controls funds.
- Rotate federator keys through a timelocked governance process.
- Publish the bridge account, contract addresses, signer set, and current supply reconciliation publicly.
- Rehearse the emergency pause flow at least quarterly — pause deposits only, confirm no pending tx stuck mid-flight.

### Axelar GMP Hygiene
- Include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- The destination contract must be idempotent: same commandId + txHash should be a no-op.
- Gas should be estimated conservatively — Axelar's gas service refunds unused native gas but short gas stalls the transfer.

### Token Representation
- Document whether the token is redeemable (1:1 backed), synthetic (price exposure only), issuer-backed (gateway custodied), or message-only (no asset movement).
- For lock-and-mint bridges: monitor the locked balance on L1 against minted supply on EVM; any divergence is a critical incident.
- For NFT mirrors: prefer burn/mint over escrow — escrowed NFTs complicate concurrent sell offer lifecycle.

### Deposit (XRPL → EVM)
- Parse XRPL memos as hex; validate the EVM address length (42 chars, 0x prefix); reject malformed payloads before minting.
- Multi-page deposits (large NFT metadata bundles): use a separate memo per page, keyed by sequence number.
- Edge case: the same user sends a deposit and a withdrawal for the same asset in the same ledger — buffer both and process deposit first.
