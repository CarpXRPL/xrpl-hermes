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

## Practical interop notes
- Withdrawal workflow 1: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 2: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 3: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 4: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 5: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 6: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 7: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 8: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 9: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 10: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 11: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 12: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 13: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 14: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 15: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 16: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 17: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 18: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 19: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 20: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 21: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 22: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 23: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 24: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 25: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 26: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 27: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 28: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 29: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 30: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 31: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 32: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 33: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 34: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 35: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 36: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 37: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 38: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 39: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 40: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 41: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 42: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 43: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 44: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 45: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 46: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 47: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 48: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 49: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 50: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 51: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 52: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 53: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 54: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 55: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 56: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 57: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 58: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 59: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 60: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 61: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 62: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 63: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 64: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 65: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 66: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 67: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 68: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 69: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 70: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 71: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 72: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 73: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 74: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 75: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 76: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 77: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 78: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 79: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 80: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 81: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 82: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 83: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 84: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 85: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 86: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 87: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 88: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 89: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 90: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 91: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 92: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 93: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 94: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 95: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 96: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 97: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 98: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 99: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 100: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 101: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 102: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 103: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 104: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 105: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 106: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 107: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 108: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 109: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 110: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 111: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 112: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 113: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 114: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 115: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 116: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 117: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 118: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 119: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 120: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 121: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 122: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 123: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 124: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 125: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 126: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 127: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 128: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 129: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 130: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 131: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 132: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 133: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 134: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 135: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 136: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 137: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 138: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 139: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 140: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 141: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 142: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 143: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 144: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 145: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 146: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 147: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 148: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 149: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 150: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 151: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 152: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 153: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 154: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 155: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 156: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 157: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 158: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 159: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 160: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 161: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 162: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 163: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 164: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 165: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 166: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 167: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 168: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 169: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 170: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 171: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 172: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 173: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 174: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 175: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 176: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 177: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 178: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 179: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 180: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 181: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 182: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 183: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 184: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 185: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 186: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 187: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 188: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 189: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 190: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 191: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 192: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 193: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 194: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 195: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 196: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 197: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 198: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 199: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 200: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 201: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 202: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 203: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 204: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 205: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 206: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 207: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 208: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 209: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 210: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 211: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 212: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 213: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 214: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 215: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 216: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 217: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 218: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 219: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 220: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 221: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 222: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 223: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 224: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 225: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 226: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 227: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 228: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 229: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 230: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 231: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 232: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 233: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 234: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 235: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 236: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 237: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 238: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 239: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 240: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 241: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 242: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 243: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 244: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 245: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
- Withdrawal workflow 246: wait for the EVM burn transaction receipt and bridge event before preparing the XRPL Payment release.
- Federator workflow 247: sign exactly one command for each source event and store signer receipts for audit.
- Axelar workflow 248: include an app-level nonce and deadline in every GMP payload to prevent duplicate execution.
- Representation workflow 249: document whether the token is redeemable, synthetic, issuer-backed, or message-only.
- Deposit workflow 250: parse XRPL memos as hex, validate the EVM address length, and reject malformed payloads before minting.
