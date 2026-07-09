# NFT Community Product Flow

Use this playbook when the user wants an NFT mint site, collection launch, holder-gated Telegram/Discord, loyalty pass, or small marketplace flow.

## Product promise

A non-custodial NFT community product:

```text
collection plan → mint/signing UX → offer/buy flow → holder verification → gated experience/receipts
```

## Triggers

- "build an NFT project"
- "mint site"
- "holder-gated community"
- "NFT marketplace"
- "NFT loyalty pass"

## Target user

Artists, meme/community teams, loyalty projects, and builders adding ownership-gated features.

## XRPL primitives

- NFTokenMint
- NFTokenCreateOffer / AcceptOffer / CancelOffer / Burn
- NFTokenTaxon
- transfer fee / flags
- NFTokenPage owner reserves
- optional Arweave metadata permanence

## Read first

- `skills/build-xrpl-product-flow.md`
- `skills/wallet-signing-ux-product-flow.md`
- `skills/nft-operations-flow.md`
- `knowledge/06-xrpl-nfts.md`
- `knowledge/23-xrpl-nft-minting.md`
- `knowledge/39-xrpl-nft-ops.md`
- `knowledge/62-xrpl-nft-marketplace.md`
- `knowledge/47-xrpl-arweave-storage.md`

## Commands/tools

- `build-nft-mint`
- `nft-info NFT_ID`
- `nft-offers NFT_ID [sell|buy]`
- `build-nft-create-offer`
- `build-nft-accept-offer`
- `build-nft-cancel-offer`
- `build-nft-burn`
- `account_objects rHOLDER`
- `arweave-cost SIZE`

## MVP deliverable

1. Collection plan: taxon, metadata URI approach, transfer fee, flags, mint authority.
2. Mint page with decoded unsigned JSON and wallet handoff.
3. Offer/buy flow using NFT offers.
4. Holder verification by reading ledger ownership after wallet ownership proof.
5. Gate action: role, content, loyalty claim, or dashboard access.

## Testnet demo checklist

- Mint 3 NFTs on testnet.
- Create/accept one offer.
- Verify holder state from ledger.
- Show royalty/transfer-fee choices before mint.
- Burn/cancel flows are blocked behind explicit confirmation.

## Mainnet-safe checklist

- Royalty/transfer fee and flags are treated as mint-time choices.
- Metadata storage path is durable enough for the project's promise.
- Reserve costs for NFTokenPages are explained.
- Marketplace scope is kept narrow until mint/gate works.
- Gate never asks users to send funds to prove ownership.

## Common failure modes

- Regretting immutable royalty/burnable choices after mint.
- Assuming mutable metadata when URI/storage is permanent.
- Gate bot asks for a seed or payment instead of verifying ledger ownership.
- Jumping to brokered marketplace complexity too early.
