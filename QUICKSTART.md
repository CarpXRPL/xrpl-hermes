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
python3 -m scripts.xrpl_tools server-info
python3 -m scripts.xrpl_tools account rADDRESS
python3 -m scripts.xrpl_tools tx-info HASH
```

## Build unsigned intent

```bash
python3 -m scripts.xrpl_tools build-payment --from rSRC --to rDST --amount 1000000
```

Review the JSON, hand it to a compatible user-owned external signer, then verify the returned hash with `tx-info`. Hermes receives no seed/private key. Placeholder addresses above are not executable values.

New flows are Testnet-first. Mainnet requires explicit authorization, controlled value/fees and monitoring. See `SKILL.md`, `LIMITATIONS.md`, `SECURITY.md` and `docs/WORKFLOWS.md`.

## MCP

The MCP server is default-deny and exposes only the agent-safe subset. Legacy key/broadcast registrations and guarded external-side-effect commands remain denied. After installation, point your client at `.venv/bin/xrpl-hermes-mcp`; never copy credentials into chat or examples.
