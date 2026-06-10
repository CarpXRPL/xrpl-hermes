# RLUSD — Quick Reference

Condensed from `knowledge/58-rlusd-operations.md` — read that file before building.

## Identity
- Ripple-issued USD stablecoin on XRPL mainnet (also ERC-20 on Ethereum).
- Issuer: `rMxCKbEDwqr76QuheSUMdEGf4B9xJ8m5De` (domain `ripple.com`; verify on-ledger before use).
- Currency code: `524C555344000000000000000000000000000000`. "RLUSD" is 5 characters, so every transaction and API call must use the 160-bit hex form — explorers only *display* "RLUSD".

## Compliance model
- KYC-gated trust lines: the issuer controls who holds RLUSD; holders complete KYC off-chain before the trust line is honored.
- Clawback enabled: issuer can reclaim funds under regulatory order (`Clawback` transaction; safeguards checklist in the knowledge file).
- Travel Rule data goes in transaction memos for transfers above the FATF threshold.

## Common operations
| Task | Tool / pattern |
|---|---|
| Trust line for RLUSD | `build-trustset --currency 524C555344...0000 --issuer rMxCKb...` |
| Clawback from holder | `build-clawback` (issuer-signed; coordinate before touching exchange wallets) |
| Supply monitoring | issuer obligations via explorer APIs |
| Large-transfer alerts | WebSocket `subscribe` on the issuer account |

## Gotchas
- The 5-letter literal `"RLUSD"` fails xrpl-py validation and never matches ledger responses — always compare against the hex code.
- Issuer has `lsfDepositAuth` set; do not assume direct payments to the issuer account work.
- Jurisdiction notes and full workflows: `knowledge/58-rlusd-operations.md`.
