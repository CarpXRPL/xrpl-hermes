# XRPL-Hermes Quick Start

Get from zero to your first XRPL transaction in 5 minutes. No wallet required for read-only queries.

## 1. Clone & Install

```bash
git clone https://github.com/CarpXRPL/xrpl-hermes-v1.0.git
cd xrpl-hermes-v1.0
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

Expected output:
```
Server: xrplcluster.com | Version: 2.x.x | Ledger: 93xxxxxx | Load: 1
```

## 3. Query an Account (no wallet needed)

```bash
python3 scripts/xrpl_tools.py account rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh
```

Output:
```
Account: rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh
Balance: 1,000,000,000.000000 XRP
Sequence: 1
Reserve:  10.000000 XRP base + 2.000000 XRP/object
```

## 4. Check the Latest Ledger

```bash
python3 scripts/xrpl_tools.py ledger
```

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
