# Beginner guide

XRPL-Hermes separates reading/building from authorization:

1. **Read** current validated XRPL state.
2. **Build** unsigned transaction JSON.
3. **Review** network, accounts, tags, asset/issuer, amount, flags, fees/limits and irreversible effects.
4. **Sign externally** in a compatible user-owned wallet. Hermes receives no seed/private key.
5. **Verify** the returned hash with `tx-info`; require `validated: true` and the expected final result.

Start with read-only commands:

```bash
python3 -m scripts.xrpl_tools  # prints CLI usage and commands
python3 -m scripts.xrpl_tools server-info
python3 -m scripts.xrpl_tools account rADDRESS
```

Then use a `build-*` command on Testnet. Never paste wallet recovery material into chat, scripts or environment owned by the agent. Mainnet requires explicit approval and monitored limits.

Read `QUICKSTART.md`, `SKILL.md`, `SECURITY.md` and `LIMITATIONS.md` before any value-bearing workflow.
