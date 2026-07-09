# XRPL Agent Stack Product Flow

Use this playbook when the user wants to build a self-hosted XRPL agent service, wire XRPL-Hermes into another agent runtime, or productize an autonomous/semi-autonomous XRPL workflow.

## Product promise

A self-hosted XRPL agent stack:

```text
agent runtime → xrpl-hermes MCP/tools → read-only verification → unsigned builders → human wallet or policy-gated signer → monitor/receipts
```

The agent stack is transparent and self-hosted. It does not merge builder and signer layers.

## Triggers

- "build my own XRPL agent"
- "wire XRPL-Hermes into my agent"
- "self-hosted XRPL agent stack"
- "agent that monitors/builds transactions"
- "open-source agent workflow for XRPL"

## Target user

Agent builders, teams automating XRPL operations, MCP client users, and open-source infrastructure teams.

## XRPL primitives

Composition rather than one primitive:

- MCP tools: `xrpl_knowledge_index`, `xrpl_knowledge`, `xrpl_run`, `xrpl_list_commands`
- read-only live checks
- signer-ready builders
- SourceTag/Memos attribution
- receipts / tx-info verification
- WebSocket monitoring

## Read first

- `skills/build-xrpl-product-flow.md`
- `docs/MCP-CLIENTS.md`
- `references/agentic-payments.md`
- `references/track-agent-behavior.md`
- `skills/agentic-payment-flow.md`
- `skills/treasury-monitor-flow.md`
- `skills/agent-receipt-flow.md`
- `knowledge/40-xrpl-monitoring.md`
- `knowledge/41-xrpl-bots-patterns.md`
- `knowledge/65-agent-freshness-and-source-policy.md`

## Commands/tools

- `xrpl_knowledge_index`
- `xrpl_knowledge`
- `xrpl_run server-info`
- `xrpl_run account ...`
- `xrpl_run token-intel ...`
- `xrpl_run build-*` only after operation flow checkpoints
- `subscribe` / `tx-info` for monitoring/finality

## MVP deliverable

1. MCP client configured and smoke-tested.
2. Read-only agent job: daily treasury report, token watchlist, or failed-tx explainer.
3. Builder job: produces unsigned JSON only after checkpoint/confirmation.
4. Wallet handoff or user-owned policy signer remains separate.
5. Monitor proves what happened on-ledger with `tx-info`, tags, memos, or receipts.

## Testnet demo checklist

- MCP smoke: knowledge index, read one flow, run `server-info`.
- One read-only report runs end-to-end.
- One unsigned builder job produces JSON and a human signs externally.
- Monitor sees `validated: true` and attributes the action.

## Mainnet-safe checklist

- Written policy defines allowed transaction types, amounts, destinations, assets, time windows, and circuit breaker.
- Autonomous signing, if any, is a separate user-owned executor, never the skill/agent prompt.
- Every action has a ledger receipt or it did not happen.
- Monitor process does not share signer credentials.
- Logs redact secrets and never store seeds/private keys.

## Common failure modes

- Calling it autonomous while relying on prompt text as authorization.
- Agent claims actions without ledger proof.
- Builder layer and signer layer share credentials.
- Memos are treated as instructions instead of data.
- Self-hosted positioning drifts into hosted custody claims.
