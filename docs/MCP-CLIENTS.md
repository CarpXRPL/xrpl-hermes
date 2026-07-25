# MCP Client Guide — Claude Code, Cursor, Codex, Hermes, and any MCP client

`scripts/mcp_server.py` is a stdio MCP server written in stdlib-only Python (no extra dependencies beyond the repo's own requirements for the commands it runs). Point any MCP-capable client at it and the agent gets the knowledge base plus the agent-safe command subset.

## The four tools every client gets

| Tool | What it does |
|---|---|
| `xrpl_list_commands` | Lists the 67 agent-safe CLI commands exposed over MCP |
| `xrpl_run` | Runs one command with CLI-style args (e.g. `command="account"`, `args=["rADDR"]`) |
| `xrpl_knowledge_index` | Lists the 65 knowledge files, 15 reference cards, and `skills/` workflow flows with titles |
| `xrpl_knowledge` | Reads one knowledge/reference/workflow file (sandboxed to `knowledge/`, `references/`, and `skills/`) |

Design properties worth knowing before you wire it up:

- **Subprocess isolation.** Each `xrpl_run` call executes in a child process with a 90-second timeout, so a crashing or hanging command never takes down the server.
- **Default-deny custody boundary.** The server refuses `wallet-generate`, `wallet-from-seed`, `submit`, `submit-multisigned`, and `xaman-payload` before execution. Builders return signer-ready JSON for external signing.
- **Knowledge reads are sandboxed.** `xrpl_knowledge` rejects paths outside `knowledge/`, `references/`, and `skills/` (covered by tests).
- **Live-network commands need the repo's Python deps.** `xrpl_list_commands`, `xrpl_knowledge_index`, and `xrpl_knowledge` work even without `xrpl-py` installed; `xrpl_run` needs `pip install -r requirements.txt` done once in the Python that runs the server.

In all examples below, replace `/path/to/xrpl-hermes` with your actual clone path. If you installed the repo's dependencies into a virtualenv, use that venv's Python (e.g. `/path/to/xrpl-hermes/.venv/bin/python3`) as the command.

## Claude Code

```bash
claude mcp add xrpl-hermes -- python3 /path/to/xrpl-hermes/scripts/mcp_server.py
```

Verify inside a session: `/mcp` should show `xrpl-hermes` connected with the four tools. Then ask something like *"check whether the Batch amendment is enabled on XRPL mainnet"* — the agent should call `xrpl_run` with `command="amendment"`.

## Cursor

Add to `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` in your project:

```json
{
  "mcpServers": {
    "xrpl-hermes": {
      "command": "python3",
      "args": ["/path/to/xrpl-hermes/scripts/mcp_server.py"]
    }
  }
}
```

Enable the server under Cursor Settings → MCP.

## Codex CLI

Add to `~/.codex/config.toml`:

```toml
[mcp_servers.xrpl-hermes]
command = "python3"
args = ["/path/to/xrpl-hermes/scripts/mcp_server.py"]
```

## Claude Desktop

Add the same JSON block as Cursor's to `claude_desktop_config.json` (Settings → Developer → Edit Config), then restart the app.

## Hermes Agent

Hermes loads xrpl-hermes natively as a skill — the MCP server is optional there:

```bash
mkdir -p ~/.hermes/skills
cp -r xrpl-hermes ~/.hermes/skills/xrpl-hermes
```

Activate with `activate xrpl-hermes`. The skill prompt (`SKILL.md`) gives the agent the same commands via the terminal plus the knowledge-citation and freshness rules. If your Hermes setup prefers MCP, the generic stdio config below works too.

## Any other MCP client

The server speaks standard JSON-RPC 2.0 over stdio (protocol version `2025-06-18`). Generic config shape:

```json
{
  "mcpServers": {
    "xrpl-hermes": {
      "command": "python3",
      "args": ["/path/to/xrpl-hermes/scripts/mcp_server.py"]
    }
  }
}
```

No environment variables are required. Optional ones (`XRPL_PRIVATE_RPC` for your own node, `XUMM_API_KEY`/`XUMM_API_SECRET` for `xaman-payload`) can be passed through your client's `env` block.

## Smoke test without any client

You can drive the server by hand to confirm it works:

```bash
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"smoke","version":"0"}}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
  '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"xrpl_run","arguments":{"command":"ledger","args":[]}}}' \
  | python3 scripts/mcp_server.py
```

You should see three JSON-RPC responses; the third contains live validated-ledger data.

## Prompting patterns that work well

- *"Use xrpl_knowledge_index, read the AMM file, then build an AMMDeposit for …"* — knowledge first, then build; this matches how the skill is designed to be used.
- *"Check the live amendment status before using any post-2024 transaction type."* — the builders do this themselves for MPT/Credential/Oracle/Batch, but saying it keeps the agent honest for everything else.
- *"Run token-intel for CODE rISSUER and interpret the risk flags."* — one `xrpl_run` call (`command="token-intel"`, `args=["CODE","rISSUER"]`) returns the ≥5-live-datapoints, confidence-scored, missing-data-listed report; `knowledge/64` is the methodology behind it.
- *"Check the XRP AMM pool for CODE:rISSUER."* — `command="amm-info"`, `args=["XRP","CODE:rISSUER"]` returns live reserves, trading fee, and auction slot, or an honest `AMMExists: false`.

### Starter prompts by role

Copy-paste these into any connected MCP client; each resolves to live read-only calls or signer-ready JSON.

**New to XRPL**
- *"What do account reserves cost right now? Check server-info and explain base and owner reserves in plain English."*
- *"Look up account rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe and walk me through each field."*

**Developer**
- *"Check whether the MPTokensV1 amendment is enabled, then build a signer-ready MPTokenIssuanceCreate for my account rEXAMPLE… — do not submit anything."*
- *"Build a TrustSet for 1000 RLUSD from rEXAMPLE… and explain every field before I sign it in my own wallet."*

**Researcher**
- *"Run token-intel on CODE rISSUER, then pull the issuer's last 25 transactions and tell me whether the activity pattern matches the holder picture."*
- *"Compare amm-info XRP CODE:rISSUER against book-offers DEX depth for the same pair — where is the real liquidity?"*

**Bot builder**
- *"Get the XRP/USD price from flare-ftso and the validated ledger index, and shape both into one JSON object my monitor can poll."*
- *"Check bridge-status for the xrpl and xrpl-evm chains and flag anything deprecated — this runs hourly, keep the output stable."*

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `xrpl_run` returns `dispatcher unavailable: …` | The Python running the server can't import `xrpl-py`. Run `pip install -r requirements.txt` with that same Python, or point the client at your venv's `python3`. |
| Knowledge tools work but commands fail | Same as above — knowledge needs no deps, commands do. |
| `command timed out after 90s` | Public endpoint slow or unreachable; retry, or set `XRPL_PRIVATE_RPC` to your own rippled/Clio. |
| Client shows no tools | Check the path in your config is absolute and the file is executable by `python3`. Run the smoke test above outside the client. |
| `xaman-payload` returns `MissingCredentials` | Expected without `XUMM_API_KEY`/`XUMM_API_SECRET`; get free keys at apps.xumm.dev or sign the JSON manually in Xaman's Developer tab. |
