# XRPL-Hermes Quick Start

Get from zero to your first XRPL transaction in 5 minutes. No wallet required for read-only queries.

## 1. Clone & Install

```bash
git clone https://github.com/CarpXRPL/xrpl-hermes.git
cd xrpl-hermes
pip install -r requirements.txt
```

Or with uv (faster):
```bash
uv pip install -r requirements.txt
```

## 2. Verify Installation

```bash
python3 scripts/xrpl_tools.py server-info
```

Expected output (JSON; numbers will vary; rippled is on the 2.x/3.x line):
```json
{
  "BuildVersion": "3.1.x",
  "Uptime": 123456,
  "CompleteLedgers": "32570-104xxxxxx",
  "ValidatedLedger": {"seq": 104125000, "reserve_base_xrp": 1, "reserve_inc_xrp": 0.2, ...},
  "ServerState": "full"
}
```

## 3. Query an Account (no wallet needed)

```bash
python3 scripts/xrpl_tools.py account rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh
```

Output (JSON):
```json
{
  "Account": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
  "BalanceDrops": "56760604151",
  "BalanceXRP": "56760.604151",
  "ReserveXRP": "1.2",
  "OwnerCount": 1,
  "SpendableXRP": "56759.404151",
  "Sequence": 44196,
  "Flags": 1703936,
  "FlagDescriptions": ["lsfDisableMasterKey", "lsfDisallowXRP", "lsfRequireDestTag"]
}
```

## 4. Check the Latest Ledger

```bash
python3 scripts/xrpl_tools.py ledger
```

## 4b. Research a Token (read-only)

```bash
# Live report: issuer flags/domain, trustline sample, DEX book vs XRP, AMM, risk flags
python3 scripts/xrpl_tools.py token-intel RLUSD rMxCKbEDwqr76QuheSUMdEGf4B9xJ8m5De
```

Anything that can't be fetched lands in `missing_data` — the report never fills gaps with made-up numbers.

## 5. Build a Payment (no wallet needed to build)

```bash
python3 scripts/xrpl_tools.py build-payment \
  --from rYOUR_ADDRESS \
  --to rDEST_ADDRESS \
  --amount 1000000
```

Output is raw TX JSON. Copy it into Xaman or Crossmark to sign and submit.

## 6. Set Up a Trust Line (build only)

```bash
python3 scripts/xrpl_tools.py build-trustset \
  --from rYOUR_ADDRESS \
  --currency USD \
  --issuer rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh \
  --value 1000000000
```

## 7. Run Example Scripts (requires XRPL_SEED)

Get a free testnet wallet:
```bash
# Faucet: https://faucet.altnet.rippletest.net/accounts
export XRPL_SEED=sEdYOUR_TESTNET_SEED_HERE
python3 examples/example-build-payment.py
```

## 8. Use It From Any MCP Client (optional)

```bash
# Claude Code / OpenClaw / Cursor — point your MCP config at the server:
claude mcp add xrpl-hermes -- python3 "$(pwd)/scripts/mcp_server.py"
```

Your agent gets `xrpl_run` (all 73 commands), `xrpl_list_commands`, and the full knowledge base via `xrpl_knowledge`.

## Next Steps

- **All tools**: see `STANDALONE.md` for the complete CLI reference
- **Deploy your own node**: see `deploy/README.md`
- **Bot examples**: `examples/example-telegram-bot.py`, `examples/example-discord-bot.py`
- **Private node**: set `XRPL_PRIVATE_RPC=http://localhost:5005` to use your own Clio/rippled

## Environment Variables

| Variable | Purpose |
|---|---|
| `XRPL_PRIVATE_RPC` | Your private rippled/Clio endpoint (takes priority) |
| `XRPL_SEED` | Wallet seed for example scripts (testnet only) |
| `XRPLSCAN_API_KEY` | XRPLScan API key for enhanced queries |
