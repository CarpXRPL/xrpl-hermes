# MCP Client Guide — Claude Code, Cursor, Codex, Hermes, and any MCP client

`scripts/mcp_server.py` is a stdio MCP server. Point any MCP-capable client at the installed executable to expose the knowledge base and 67 read/unsigned-builder commands.

## The four tools every client gets

| Tool | What it does |
|---|---|
| `xrpl_list_commands` | Lists the 67 available CLI commands exposed over MCP |
| `xrpl_run` | Runs one command with CLI-style args (e.g. `command="account"`, `args=["rADDR"]`) |
| `xrpl_knowledge_index` | Lists the 65 knowledge files, 15 reference cards, and `skills/` workflow flows with titles |
| `xrpl_knowledge` | Reads one knowledge/reference/workflow file (sandboxed to `knowledge/`, `references/`, and `skills/`) |

Design properties worth knowing before you wire it up:

- **Subprocess isolation.** Each `xrpl_run` call executes in a child process with a 90-second timeout, so a crashing or hanging command never takes down the server.
- **Default-deny custody boundary.** Key handling, signing, and broadcasting are not implemented. `xaman-payload` is local-only because it creates a real external wallet request.
- **Knowledge reads are sandboxed.** `xrpl_knowledge` rejects paths outside `knowledge/`, `references/`, and `skills/` (covered by tests).
- **Install the project, not only requirements.** `pip install .` installs the CLI/MCP entry points and packages the complete knowledge/reference/workflow corpus.

In all examples below, replace `/path/to/xrpl-hermes` with your clone path after running `bash setup.sh`. Use `/path/to/xrpl-hermes/.venv/bin/xrpl-hermes-mcp`.

## Claude Code

```bash
claude mcp add xrpl-hermes -- /path/to/xrpl-hermes/.venv/bin/xrpl-hermes-mcp
```

Verify inside a session: `/mcp` should show `xrpl-hermes` connected with the four tools. Then ask something like *"check whether the Batch amendment is enabled on XRPL mainnet"* — the agent should call `xrpl_run` with `command="amendment"`.

## Cursor

Add to `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` in your project:

```json
{
  "mcpServers": {
    "xrpl-hermes": {
      "command": "/path/to/xrpl-hermes/.venv/bin/xrpl-hermes-mcp"
    }
  }
}
```

Enable the server under Cursor Settings → MCP.

## Codex CLI

Add to `~/.codex/config.toml`:

```toml
[mcp_servers.xrpl-hermes]
command = "/path/to/xrpl-hermes/.venv/bin/xrpl-hermes-mcp"
```

## Claude Desktop

Add the same JSON block as Cursor's to `claude_desktop_config.json` (Settings → Developer → Edit Config), then restart the app.

## Hermes Agent

Hermes loads xrpl-hermes natively as a skill — the MCP server is optional there:

```bash
mkdir -p ~/.hermes/skills/xrpl-hermes
cp -r xrpl-hermes/SKILL.md xrpl-hermes/knowledge xrpl-hermes/references xrpl-hermes/skills ~/.hermes/skills/xrpl-hermes/
hermes mcp add xrpl-hermes --command "/path/to/xrpl-hermes/.venv/bin/xrpl-hermes-mcp"
hermes mcp test xrpl-hermes
```

Launch Hermes with `hermes -s xrpl-hermes` (or load it in-session with `/skill xrpl-hermes`). The MCP runtime supplies the isolated command surface and packaged knowledge corpus.

## Any other MCP client

The server speaks standard JSON-RPC 2.0 over stdio (protocol version `2025-06-18`). Generic config shape:

```json
{
  "mcpServers": {
    "xrpl-hermes": {
      "command": "/path/to/xrpl-hermes/.venv/bin/xrpl-hermes-mcp"
    }
  }
}
```

No environment variables are required for the MCP server. `XRPL_PRIVATE_RPC` may point read-only requests at infrastructure you operate. Xaman credentials are not an MCP configuration surface because `xaman-payload` is denied before execution.

## Smoke test without any client

You can drive the server by hand to confirm it works:

```bash
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"smoke","version":"0"}}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
  '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"xrpl_run","arguments":{"command":"ledger","args":[]}}}' \
  | .venv/bin/xrpl-hermes-mcp
```

You should see three JSON-RPC responses; the third contains live validated-ledger data.

## Prompting patterns that work well

- *"Use xrpl_knowledge_index, read the AMM file, then build an AMMDeposit for …"* — knowledge first, then build; this matches how the skill is designed to be used.
- *"Check the live amendment status before using an amendment-dependent transaction type."* — builders perform live checks before producing intent.
- *"Run token-intel for CODE rISSUER and interpret the evidence gaps."* — one `xrpl_run` call returns an explicitly partial, freshness-stamped report; confidence describes data completeness only.
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
| `xrpl_run` returns `dispatcher unavailable: …` | Install the project with `pip install .`, then point the client at that environment's `xrpl-hermes-mcp` entry point. |
| Knowledge tools work but commands fail | Same as above — knowledge needs no deps, commands do. |
| `command timed out after 90s` | Public endpoint slow or unreachable; retry, or set `XRPL_PRIVATE_RPC` to your own rippled/Clio. |
| Client shows no tools | Check that the configured `.venv/bin/xrpl-hermes-mcp` path is absolute and executable. Run the smoke test above outside the client first. |
