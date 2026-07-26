# xrpl-py with XRPL-Hermes

`xrpl-py` is the Python engine used by the CLI. Applications can also consume XRPL-Hermes as a subprocess or use xrpl-py directly for reads and unsigned transaction models.

## Read validated account state

```python
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountInfo

client = JsonRpcClient("https://xrplcluster.com")
response = client.request(AccountInfo(
    account="rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
    ledger_index="validated",
))
print(response.result["account_data"])
```

## Build unsigned JSON through XRPL-Hermes

```python
import json
import subprocess

result = subprocess.run(
    [
        "xrpl-hermes", "build-payment",
        "--from", "rSOURCE",
        "--to", "rDESTINATION",
        "--amount", "1000000",
    ],
    check=True,
    text=True,
    capture_output=True,
)

payload = json.loads("\n".join(
    line for line in result.stdout.splitlines() if not line.startswith("#")
))
print(payload)
```

The payload is unsigned. Pass it to a user-controlled wallet using that wallet’s current SDK or handoff mechanism, then verify the returned hash:

```bash
xrpl-hermes tx-info TX_HASH
```

## Amounts

```python
from xrpl.utils import xrp_to_drops, drops_to_xrp

assert xrp_to_drops("1.5") == "1500000"
assert drops_to_xrp("1500000") == "1.5"
```

Issued-currency amounts use `{currency, issuer, value}` objects. Do not use floating-point arithmetic for financial values.

## Compatibility

The package test suite runs against xrpl-py 4.2 and 5.x. For models outside the shipped builders, verify the installed SDK and current XRPL documentation rather than inferring support from a protocol amendment.

XRPL-Hermes does not expose xrpl-py wallet generation, seed import, signing, or submit helpers.
