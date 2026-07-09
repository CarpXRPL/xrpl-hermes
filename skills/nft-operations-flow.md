# NFT Operations Flow

For: "mint an NFT", "sell/buy this NFT", "broker two offers", "burn it", "why won't
this offer accept?". Covers the full XLS-20 lifecycle with the five `build-nft-*`
builders (unsigned, signer-ready) and the two live lookups (`nft-info`, `nft-offers`).
The recurring trap: minting choices (flags, transfer fee, taxon) are **immutable per
token** — get them right before the first mint, not after.

Read first: `knowledge/06-xrpl-nfts.md` (model), `knowledge/23-xrpl-nft-minting.md`
(mint parameters), `knowledge/39-xrpl-nft-ops.md` (offer lifecycle),
`knowledge/62-xrpl-nft-marketplace.md` (brokered sales).

## Step 1 — Mint (unsigned)

```bash
python3 scripts/xrpl_tools.py build-nft-mint \
  --from rMINTER --taxon 1 --uri "ipfs://Qm.../metadata.json" \
  --transfer-fee 5000 --flags 9
```

Decisions to settle with the user before building — all frozen at mint:

| Parameter | Meaning | Notes |
|---|---|---|
| `--flags` | 1 = tfBurnable (issuer may burn later), 2 = tfOnlyXRP, 8 = tfTransferable — **sum** to combine (9 = burnable + transferable) | Default 8. Without tfTransferable the NFT can only move to/from the issuer |
| `--transfer-fee` | Issuer royalty on secondary sales, units of 0.001% — 5000 = 5%, max 50000 (50%) | Requires tfTransferable; collected only on issued-currency/XRP sale amounts |
| `--taxon` | Collection grouping number (0 if unused) | Public, used by marketplaces to group series |
| `--uri` | Metadata pointer, ≤ 256 bytes — auto-hex-encoded by the builder | Content is off-ledger; the ledger stores only the pointer |
| `--issuer` | Mint *on behalf of* rISSUER | Only works after the issuer set `NFTokenMinter` to rMINTER via `build-account-set --from rISSUER --nftoken-minter rMINTER` |

Reserve note: NFTs live in NFTokenPage objects — each page (up to 32 NFTs) costs one
owner-reserve increment on the holder.

After validation, get the NFTokenID from `tx-info HASH` (meta) — it's derived, not
chosen — then `nft-info NFT_ID` to confirm flags/fee/taxon landed as designed.

## Step 2 — Offers: sell, buy, or targeted transfer (unsigned)

Always look before building — `nft-info NFT_ID` (who owns it now? what royalty?) and
`nft-offers NFT_ID sell` / `buy` (what's already on the books?).

```bash
# Owner lists it for 25 XRP (amount in drops; sell = --flags 1, the default)
python3 scripts/xrpl_tools.py build-nft-create-offer \
  --from rOWNER --nftoken-id 000B...ID --amount 25000000 --flags 1

# Someone bids 20 XRP (buy = --flags 0, and --owner names the current holder)
python3 scripts/xrpl_tools.py build-nft-create-offer \
  --from rBIDDER --nftoken-id 000B...ID --amount 20000000 --flags 0 --owner rOWNER

# Free targeted transfer: 0-amount sell offer locked to one recipient
python3 scripts/xrpl_tools.py build-nft-create-offer \
  --from rOWNER --nftoken-id 000B...ID --amount 0 --flags 1 --destination rFRIEND
```

- Issued-currency pricing uses `CUR:rISSUER:VALUE` for `--amount` (e.g.
  `USD:rISSUER:100`); bare numbers are XRP **drops**.
- `--destination` restricts who may accept; `--expiration` (ripple-epoch seconds)
  auto-invalidates — expired offers still occupy reserve until cancelled.
- Each open offer is one owner-reserve object on its creator.

## Step 3 — Accept (direct or brokered, unsigned)

Verify the offer index still exists **immediately before** building — accepted/cancelled
offer indexes are the top source of `tecOBJECT_NOT_FOUND`:

```bash
python3 scripts/xrpl_tools.py nft-offers 000B...ID sell   # offer index + amount + destination

# Buyer accepts a sell offer outright
python3 scripts/xrpl_tools.py build-nft-accept-offer --from rBUYER --sell-offer OFFER_INDEX

# Broker mode: match a sell and a buy, taking the spread as --broker-fee
python3 scripts/xrpl_tools.py build-nft-accept-offer \
  --from rBROKER --sell-offer SELL_INDEX --buy-offer BUY_INDEX --broker-fee 1000000
```

Broker rules (`knowledge/62`): the sell amount + broker fee must fit inside the buy
amount, the buyer must actually hold the funds (`account rBUYER` / `trustlines` for
issued currency), and the issuer's transfer fee comes out of the proceeds. Confirm
before build (value transfer): network, offer indexes, who pays what, royalty cut.

## Step 4 — Cancel and burn (unsigned)

```bash
python3 scripts/xrpl_tools.py build-nft-cancel-offer --from rCREATOR --offers IDX1,IDX2
python3 scripts/xrpl_tools.py build-nft-burn --from rOWNER --nftoken-id 000B...ID
python3 scripts/xrpl_tools.py build-nft-burn --from rISSUER --nftoken-id 000B...ID --owner rHOLDER
```

- Cancel: offer creator (or the destination, or anyone once expired) reclaims the
  reserve. Takes a comma-separated list.
- Burn is **irreversible destruction** — confirm-before-build applies: state network,
  the NFT, current owner, and that it cannot be undone.
- The issuer-burn form (third command) only works if the token was minted with
  tfBurnable (`nft-info` → flags has 1) — otherwise refuse early instead of letting it
  fail on-ledger.

## Common mistakes

| Mistake | Fix |
|---|---|
| Minting with defaults, wanting royalties later | `--transfer-fee` is immutable per token — decide before Step 1; only a burn-and-remint changes it |
| `--flags 1` intended as "buy offer" on create-offer | 1 = **sell** here; buy = `--flags 0` **plus** `--owner rCURRENT_OWNER` |
| Amount `25` for 25 XRP | Bare create-offer amounts are drops — 25 XRP = `25000000` |
| Accepting a stale offer index | `nft-offers` first, always — indexes die on accept/cancel |
| Broker fee that doesn't fit the spread | buy ≥ sell + broker fee, or the accept fails |
| Expecting burn to refund the mint fee/reserve | Burning frees future page reserve only; nothing else comes back |
| Expired offers "cleaning themselves up" | They stop working but hold reserve until explicitly cancelled |

See also: `skills/failed-transaction-diagnosis-flow.md` (NFT rows in the Step 3 table),
`skills/agent-receipt-flow.md` (NFTs as on-chain provenance receipts),
`knowledge/62-xrpl-nft-marketplace.md` (marketplace patterns).
