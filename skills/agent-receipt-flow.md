# Agent Receipt Flow

Record **what an agent did** — a completed run, an audit, or a skill that improved (v1 → v2) — as
an on-chain receipt, the signer-separated way: Hermes builds an **unsigned** `NFTokenMint`; the
user's wallet/signing layer decides whether to sign it. **There is no autonomous minting here.**
**Testnet-first; keys stay with the user.** Safety = the **Safety rules** block in `SKILL.md`.

This is the safe shape of the popular "an agent mints its own NFT to prove it learned something"
demo. The good part — provenance you don't own — is kept; the unsafe part — a seed in the agent
that signs and submits on its own — is removed.

## Why on-chain?

A self-improving agent needs an audit trail it doesn't control. Recording a receipt on XRPL gives:

- **Timestamp** — ordered by ledger index; the ledger is the authoritative clock, not the agent.
- **Provenance** — the minting account is the on-record author.
- **Tamper-evidence** — the summary is bound to the NFT's URI; it can't be quietly edited.
- **Public verifiability** — anyone can fetch the NFT and decode the URI (`nft-info <NFTokenID>`).

## Architecture

```
agent finishes work / a skill evolves
  └── summarize it as a compact receipt (≤256-byte URI, or a pointer to an off-ledger record)
        └── Hermes build-nft-mint ──► unsigned NFTokenMint JSON  (no keys, no signing)
              └── human preview + approval (account, taxon, flags, decoded URI)
                    └── compatible external authorization/broadcast layer
                          └── returned hash/id ──► nft-info <NFTokenID> after validated finality
```

---

## Step 1 — Summarize the run / skill evolution

The XRPL `NFTokenMint` `URI` holds at most **256 bytes**. Keep the on-ledger record a compact
summary; put anything large off-ledger and point at it.

**Inline (self-contained, must fit 256 bytes)** — a `data:` URI carrying a small JSON summary:

```json
{"t":"skill-evolution","skill":"xrpl_send_payment","v":"v1->v2","agent":"hermes","net":"testnet","ts":"2026-06-16"}
```

**Pointer (for large records)** — keep the full metadata on IPFS / your API and set the URI to the
link (`ipfs://…` or `https://…/receipt.json`). The NFT anchors a verifiable pointer; the canonical
record lives off-ledger.

Build the inline `data:` URI in either stack:

```bash
# JavaScript / Node
node -e 'const j=JSON.stringify({t:"skill-evolution",skill:"xrpl_send_payment",v:"v1->v2",agent:"hermes",net:"testnet",ts:"2026-06-16"});
process.stdout.write("data:application/json;base64,"+Buffer.from(j).toString("base64"))'
```

```python
# Python
import base64, json
r = {"t":"skill-evolution","skill":"xrpl_send_payment","v":"v1->v2","agent":"hermes","net":"testnet","ts":"2026-06-16"}
print("data:application/json;base64," + base64.b64encode(json.dumps(r).encode()).decode())
```

---

## Step 2 — Build the unsigned receipt (NFTokenMint)

`build-nft-mint` hex-encodes the URI for you and emits signer-ready JSON (`SigningPubKey:""`). It
never signs. If the URI exceeds 256 bytes (512 hex chars) the builder refuses it — shorten the
summary or switch to pointer mode.

```bash
python3 scripts/xrpl_tools.py build-nft-mint \
  --from rMINTER --taxon 1 \
  --uri "data:application/json;base64,eyJ0Ijoic2tpbGwtZXZvbHV0aW9uIiwuLi59"
```

- `--taxon` groups a "collection" — use one dedicated value to group all your agent receipts.
- Flags default to `8` (tfTransferable) so others can hold/verify the receipt; pass a different
  value for a non-transferable (soulbound) receipt bound to the minting account.

**Runnable build-only twins (same unsigned JSON, no seed/signing/node):** Python
[`examples/example-agent-receipt.py`](../examples/example-agent-receipt.py) and xrpl.js
[`examples/js/agent-receipt-nft.js`](../examples/js/agent-receipt-nft.js) — each builds the compact
`data:` URI, enforces the 256-byte limit *after* encoding, and prints the unsigned `NFTokenMint`.

---

## Step 3 — Preview and confirm (before any signing)

Show the human the exact mint and get approval (Safety rule 4). Decode the URI back so the summary
is readable, never a raw hex blob:

```
Network:   testnet
Account:   rMINTER           Taxon: 1     Flags: 8 (transferable)
URI:       data:application/json;base64,…  →  {"t":"skill-evolution","skill":"xrpl_send_payment","v":"v1->v2",…}
```

Mainnet recording requires **explicit human approval** (Safety rule 5). A receipt is cheap but it
is still a permanent, public ledger write — record it deliberately.

---

## Step 4 — Hand off to the wallet/signing layer (testnet)

Signing stays with the user — **never put a seed in chat/logs.** Use a compatible user-owned external
wallet/HSM/KMS that never exposes its key to Hermes. Compare the
authorized fields with reviewed intent, then return a hash for validated-result verification. The
pattern is identical to the authorization boundary in `skills/agentic-payment-flow.md`.

---

## Step 5 — Read the receipt back from the ledger

```bash
python3 scripts/xrpl_tools.py nft-info <NFTokenID>   # confirm the URI on-ledger
```

Decode the returned `URI` (hex → text) to recover the summary, or follow the pointer to the
off-ledger record. Anyone can do this — that is the point of putting it on-chain.

---

## Common mistakes

| Mistake | Fix |
|---|---|
| Agent signs + submits the mint itself from a stored seed | Builder emits **unsigned** JSON; a human-held wallet signs (no autonomous minting) |
| Stuffing a full report into the URI | 256-byte limit — inline a compact summary, or use pointer mode (IPFS/API) |
| Checking the size before encoding | base64+hex inflates the payload; check the **final** hex length (≤512) |
| Calling it "proof the agent got smarter" | A receipt records a *claim* with provenance — describe what changed, don't overclaim |
| Recording on mainnet without approval | Explicit human sign-off; it is a permanent public write (Safety rule 5) |
| Seed/key requested by agent code | Stop; use a user-owned external signer that never exposes the key to Hermes |

See also: `examples/example-agent-receipt.py`, `examples/js/agent-receipt-nft.js`, `skills/agentic-payment-flow.md`,
`knowledge/06-xrpl-nfts.md`, `knowledge/23-xrpl-nft-minting.md`, `references/agentic-payments.md`.
