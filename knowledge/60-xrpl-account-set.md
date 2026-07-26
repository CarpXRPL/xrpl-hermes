# XRPL AccountSet

`build-account-set` produces unsigned `AccountSet` JSON for account and issuer configuration.

```bash
xrpl-hermes build-account-set --from rACCOUNT --set-flag 8
xrpl-hermes build-account-set --from rACCOUNT --domain example.com
xrpl-hermes build-account-set --from rACCOUNT --tick-size 5
xrpl-hermes build-account-set --from rACCOUNT --transfer-rate 1015000000
```

## Common flags

| Value | Flag | Effect |
|---:|---|---|
| 1 | `asfRequireDest` | Require destination tags for incoming payments |
| 2 | `asfRequireAuth` | Require issuer authorization on trust lines |
| 3 | `asfDisallowXRP` | Signal that direct XRP payments are not desired |
| 4 | `asfDisableMaster` | Disable the master key after another signing method is configured |
| 5 | `asfAccountTxnID` | Track the previous transaction ID |
| 6 | `asfNoFreeze` | Permanently give up individual/global freeze capability |
| 7 | `asfGlobalFreeze` | Freeze issued balances globally |
| 8 | `asfDefaultRipple` | Enable rippling by default on issuer trust lines |
| 9 | `asfDepositAuth` | Require authorization for incoming payments |
| 10 | `asfAuthorizedNFTokenMinter` | Enable the configured delegated NFT minter |
| 11–14 | incoming-object controls | Reject Checks, NFT offers, payment channels, or trust lines |
| 15 | `asfAllowTrustLineLocking` | Allow trust-line locking when active on the network |
| 16 | `asfAllowTrustLineClawback` | Enable clawback for future trust lines |

Set a flag with `--set-flag N` and clear a reversible flag with `--clear-flag N`.

## Other fields

- `--domain`: plain text is converted to uppercase hex.
- `--transfer-rate`: `0` clears the field; otherwise `1000000000` through `2000000000`.
- `--tick-size`: `3` through `15` significant digits.
- `--nftoken-minter`: delegated NFT minter account.
- `--email-hash`: legacy email hash field.
- `--message-key`: public messaging key.

## Issuer sequence

1. Separate the issuer from day-to-day operational accounts.
2. Set and verify the domain.
3. Decide whether holders require authorization.
4. Decide freeze and clawback policy before issuing trust lines.
5. Set `asfDefaultRipple` when the issuer should participate in pathfinding.
6. Review the unsigned JSON and authorize it externally.
7. Verify the resulting account flags with `account` against a validated ledger.

`asfNoFreeze` and master-key changes can be irreversible or lock an account when sequenced incorrectly. Test the exact account setup on Testnet first.
