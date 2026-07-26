# XRPL L1 reference

XRPL-Hermes uses validated XRPL JSON-RPC reads and unsigned transaction builders.

## Networks

| Network | JSON-RPC | WebSocket |
|---|---|---|
| Mainnet | `https://xrplcluster.com` | `wss://xrplcluster.com` |
| Testnet | `https://s.altnet.rippletest.net:51234` | `wss://s.altnet.rippletest.net:51233` |
| Devnet | `https://s.devnet.rippletest.net:51234` | `wss://s.devnet.rippletest.net:51233` |

Set `XRPL_PRIVATE_RPC` to prefer infrastructure you operate. Public endpoints can throttle, lag, or fail.

## Core facts

- XRP amounts in transaction JSON use drops; 1 XRP is 1,000,000 drops.
- Accounts become ledger accounts only after activation with the current reserve.
- Normal transactions consume the account’s current sequence; Tickets provide reserved sequence slots.
- Fees are destroyed and must be derived from current network state.
- Base and owner reserves are network parameters, not constants.
- Validated ledgers are final under normal XRPL consensus assumptions.
- Destination tags are unsigned 32-bit routing identifiers.
- Memos are public ledger data and must not contain secrets.
- Issued currencies use currency, issuer, and decimal string value.
- Payment processors must use delivered amount metadata, especially for partial payments.
- `tec` results consume fee and sequence despite not producing the requested effect.

## Live reads

```bash
xrpl-hermes server-info
xrpl-hermes ledger
xrpl-hermes account rACCOUNT
xrpl-hermes account_objects rACCOUNT
xrpl-hermes account-tx rACCOUNT 20
xrpl-hermes trustlines rACCOUNT
xrpl-hermes tx-info TX_HASH
```

## Unsigned build lifecycle

1. Read current account, fee, reserve, amendment, and destination state.
2. Build unsigned JSON with the matching `build-*` command.
3. Inspect network, transaction type, accounts, assets, amounts, tags, memos, flags, fees, and expiry.
4. Authorize and broadcast in a user-controlled wallet.
5. Receive the transaction hash.
6. Verify `validated: true`, engine result, delivered amount, and resulting ledger objects.

XRPL-Hermes does not generate accounts, import keys, sign, or broadcast.

## Direct JSON-RPC read

```python
import httpx

response = httpx.post(
    "https://xrplcluster.com",
    json={
        "method": "account_info",
        "params": [{
            "account": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
            "ledger_index": "validated",
            "strict": True,
        }],
    },
    timeout=20,
)
response.raise_for_status()
result = response.json()["result"]
if result.get("status") != "success":
    raise RuntimeError(result)
print(result["account_data"])
```

For production reads, preserve endpoint, network, validated ledger index, fetch time, pagination markers, and explicit errors.
