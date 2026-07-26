# XRPL-Hermes quick start

## Install

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
xrpl-hermes validate-address rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe
```

## Read live state

```bash
xrpl-hermes server-info
xrpl-hermes account rADDRESS
xrpl-hermes tx-info TRANSACTION_HASH
```

## Build unsigned intent

```bash
xrpl-hermes build-payment --from rSOURCE --to rDESTINATION --amount 1000000
```

Review the JSON, authorize it in a compatible user-controlled wallet, then verify the returned hash with `tx-info`. XRPL-Hermes does not accept keys, sign, or broadcast.

New value-moving flows are Testnet-first. Mainnet requires explicit authorization, controlled value and fees, and monitoring.

## MCP

Point your MCP client at the installed executable:

```text
/path/to/xrpl-hermes/.venv/bin/xrpl-hermes-mcp
```

MCP exposes all 67 read/unsigned-builder commands. See [`docs/MCP-CLIENTS.md`](docs/MCP-CLIENTS.md).

## Xaman Payment handoff

Xaman is available through the local CLI, not MCP, because creating a request is a real external side effect.

```bash
export XUMM_API_KEY='...'
export XUMM_API_SECRET='...'
xrpl-hermes xaman-payload '{"TransactionType":"Payment","Account":"rSOURCE","Destination":"rDESTINATION","Amount":"1000000"}'
```

Keep credentials local and verify the final transaction independently.
