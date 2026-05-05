# 60 — XRPL AccountSet Flags and Issuer Configuration

AccountSet is the transaction type used to configure account-level behavior on XRPL.
It is central to issuer setup, compliance tokens, NFT minting rights, domain identity, DEX precision, and deposit policy.

Use this file when you need signer-ready AccountSet JSON, a complete flag reference, or an issuer launch checklist.

## Quick CLI Usage

```bash
python3 -m scripts.xrpl_tools build-account-set --from r9cZA1mLK5R5Am25ArfXFmqgNwjZgnfk59 --set-flag 8
python3 -m scripts.xrpl_tools build-account-set --from r9cZA1mLK5R5Am25ArfXFmqgNwjZgnfk59 --domain example.com
python3 -m scripts.xrpl_tools build-account-set --from r9cZA1mLK5R5Am25ArfXFmqgNwjZgnfk59 --tick-size 5
python3 -m scripts.xrpl_tools build-account-set --from r9cZA1mLK5R5Am25ArfXFmqgNwjZgnfk59 --transfer-rate 1015000000
```

## Complete SetFlag / ClearFlag Reference

AccountSet flags are passed as small integer values in `SetFlag` or `ClearFlag`.
Ledger state flags are different bit masks; do not confuse the AccountSet flag number with the resulting account root flag.

### asfRequireDest = 1

- Purpose: Require destination tags for incoming payments.
- Set: `python3 -m scripts.xrpl_tools build-account-set --from rISSUER --set-flag 1`
- Clear: `python3 -m scripts.xrpl_tools build-account-set --from rISSUER --clear-flag 1`
- Signing: send the generated JSON through Xaman with `xaman-payload` or another signer.
- Production note: test on XRPL testnet before using the same setting on mainnet.

### asfRequireAuth = 2

- Purpose: Require authorization before holders can hold issued tokens.
- Set: `python3 -m scripts.xrpl_tools build-account-set --from rISSUER --set-flag 2`
- Clear: `python3 -m scripts.xrpl_tools build-account-set --from rISSUER --clear-flag 2`
- Signing: send the generated JSON through Xaman with `xaman-payload` or another signer.
- Production note: test on XRPL testnet before using the same setting on mainnet.

### asfDisallowXRP = 3

- Purpose: Discourage direct XRP payments to this account.
- Set: `python3 -m scripts.xrpl_tools build-account-set --from rISSUER --set-flag 3`
- Clear: `python3 -m scripts.xrpl_tools build-account-set --from rISSUER --clear-flag 3`
- Signing: send the generated JSON through Xaman with `xaman-payload` or another signer.
- Production note: test on XRPL testnet before using the same setting on mainnet.

### asfDisableMaster = 4

- Purpose: Disable the master key after setting a regular key or signer list.
- Set: `python3 -m scripts.xrpl_tools build-account-set --from rISSUER --set-flag 4`
- Clear: `python3 -m scripts.xrpl_tools build-account-set --from rISSUER --clear-flag 4`
- Signing: send the generated JSON through Xaman with `xaman-payload` or another signer.
- Production note: test on XRPL testnet before using the same setting on mainnet.

### asfAccountTxnID = 5

- Purpose: Track previous transaction ID on the account.
- Set: `python3 -m scripts.xrpl_tools build-account-set --from rISSUER --set-flag 5`
- Clear: `python3 -m scripts.xrpl_tools build-account-set --from rISSUER --clear-flag 5`
- Signing: send the generated JSON through Xaman with `xaman-payload` or another signer.
- Production note: test on XRPL testnet before using the same setting on mainnet.

### asfNoFreeze = 6

- Purpose: Permanently give up the ability to freeze trust lines.
- Set: `python3 -m scripts.xrpl_tools build-account-set --from rISSUER --set-flag 6`
- Clear: `python3 -m scripts.xrpl_tools build-account-set --from rISSUER --clear-flag 6`
- Signing: send the generated JSON through Xaman with `xaman-payload` or another signer.
- Production note: test on XRPL testnet before using the same setting on mainnet.

### asfGlobalFreeze = 7

- Purpose: Freeze all trust lines for issued assets.
- Set: `python3 -m scripts.xrpl_tools build-account-set --from rISSUER --set-flag 7`
- Clear: `python3 -m scripts.xrpl_tools build-account-set --from rISSUER --clear-flag 7`
- Signing: send the generated JSON through Xaman with `xaman-payload` or another signer.
- Production note: test on XRPL testnet before using the same setting on mainnet.

### asfDefaultRipple = 8

- Purpose: Enable rippling by default on issuer trust lines.
- Set: `python3 -m scripts.xrpl_tools build-account-set --from rISSUER --set-flag 8`
- Clear: `python3 -m scripts.xrpl_tools build-account-set --from rISSUER --clear-flag 8`
- Signing: send the generated JSON through Xaman with `xaman-payload` or another signer.
- Production note: test on XRPL testnet before using the same setting on mainnet.

### asfDepositAuth = 9

- Purpose: Require deposit authorization for incoming payments.
- Set: `python3 -m scripts.xrpl_tools build-account-set --from rISSUER --set-flag 9`
- Clear: `python3 -m scripts.xrpl_tools build-account-set --from rISSUER --clear-flag 9`
- Signing: send the generated JSON through Xaman with `xaman-payload` or another signer.
- Production note: test on XRPL testnet before using the same setting on mainnet.

### asfAuthorizedNFTokenMinter = 10

- Purpose: Allow the configured NFTokenMinter to mint on behalf of this account.
- Set: `python3 -m scripts.xrpl_tools build-account-set --from rISSUER --set-flag 10`
- Clear: `python3 -m scripts.xrpl_tools build-account-set --from rISSUER --clear-flag 10`
- Signing: send the generated JSON through Xaman with `xaman-payload` or another signer.
- Production note: test on XRPL testnet before using the same setting on mainnet.

### asfDisallowIncomingCheck = 11

- Purpose: Block incoming CheckCreate objects.
- Set: `python3 -m scripts.xrpl_tools build-account-set --from rISSUER --set-flag 11`
- Clear: `python3 -m scripts.xrpl_tools build-account-set --from rISSUER --clear-flag 11`
- Signing: send the generated JSON through Xaman with `xaman-payload` or another signer.
- Production note: test on XRPL testnet before using the same setting on mainnet.

### asfDisallowIncomingNFTokenOffer = 12

- Purpose: Block incoming NFT offers.
- Set: `python3 -m scripts.xrpl_tools build-account-set --from rISSUER --set-flag 12`
- Clear: `python3 -m scripts.xrpl_tools build-account-set --from rISSUER --clear-flag 12`
- Signing: send the generated JSON through Xaman with `xaman-payload` or another signer.
- Production note: test on XRPL testnet before using the same setting on mainnet.

### asfDisallowIncomingPayChan = 13

- Purpose: Block incoming payment channels.
- Set: `python3 -m scripts.xrpl_tools build-account-set --from rISSUER --set-flag 13`
- Clear: `python3 -m scripts.xrpl_tools build-account-set --from rISSUER --clear-flag 13`
- Signing: send the generated JSON through Xaman with `xaman-payload` or another signer.
- Production note: test on XRPL testnet before using the same setting on mainnet.

### asfDisallowIncomingTrustline = 14

- Purpose: Block incoming trust lines.
- Set: `python3 -m scripts.xrpl_tools build-account-set --from rISSUER --set-flag 14`
- Clear: `python3 -m scripts.xrpl_tools build-account-set --from rISSUER --clear-flag 14`
- Signing: send the generated JSON through Xaman with `xaman-payload` or another signer.
- Production note: test on XRPL testnet before using the same setting on mainnet.

### asfAllowTrustLineLocking = 15

- Purpose: Allow trust line locking where supported by amendments.
- Set: `python3 -m scripts.xrpl_tools build-account-set --from rISSUER --set-flag 15`
- Clear: `python3 -m scripts.xrpl_tools build-account-set --from rISSUER --clear-flag 15`
- Signing: send the generated JSON through Xaman with `xaman-payload` or another signer.
- Production note: test on XRPL testnet before using the same setting on mainnet.

### asfAllowTrustLineClawback = 16

- Purpose: Enable clawback for issued trust-line assets.
- Set: `python3 -m scripts.xrpl_tools build-account-set --from rISSUER --set-flag 16`
- Clear: `python3 -m scripts.xrpl_tools build-account-set --from rISSUER --clear-flag 16`
- Signing: send the generated JSON through Xaman with `xaman-payload` or another signer.
- Production note: test on XRPL testnet before using the same setting on mainnet.

### asfAllowTrustLineFreeze = 17

- Purpose: Reserve value in newer amendment discussions; verify network support before use.
- Set: `python3 -m scripts.xrpl_tools build-account-set --from rISSUER --set-flag 17`
- Clear: `python3 -m scripts.xrpl_tools build-account-set --from rISSUER --clear-flag 17`
- Signing: send the generated JSON through Xaman with `xaman-payload` or another signer.
- Production note: test on XRPL testnet before using the same setting on mainnet.

## Issuer Setup Checklist

1. Create and fund an issuer account and a separate operational account.
2. Set the issuer domain so explorers and wallets can link the issuer to a public identity.
3. Set `asfDefaultRipple=8` on the issuer so issued-token payments can route through trust lines.
4. Decide whether the token is open or permissioned; set `asfRequireAuth=2` for KYC or regulated assets.
5. Decide whether clawback is required; set `asfAllowTrustLineClawback=16` before issuing any trust lines if the token needs recovery rights.

## Safe Issuer Sequence

```bash
ISSUER=r9cZA1mLK5R5Am25ArfXFmqgNwjZgnfk59
python3 -m scripts.xrpl_tools build-account-set --from $ISSUER --domain issuer.example
python3 -m scripts.xrpl_tools build-account-set --from $ISSUER --set-flag 8
python3 -m scripts.xrpl_tools build-account-set --from $ISSUER --set-flag 2
python3 -m scripts.xrpl_tools build-account-set --from $ISSUER --set-flag 16
python3 -m scripts.xrpl_tools build-account-set --from $ISSUER --tick-size 5
```

## Tick Size

TickSize controls significant digits for offers involving issued currencies. Valid values are 3 through 15. Smaller values make order books coarser; larger values allow finer price precision.

Example:

```bash
python3 -m scripts.xrpl_tools build-account-set --from r9cZA1mLK5R5Am25ArfXFmqgNwjZgnfk59 --tick-size 5
```

## Transfer Rate

TransferRate is encoded from 1000000000 for 0 percent to 2000000000 for 100 percent. A 1.5 percent transfer fee is 1015000000.

Example:

```bash
python3 -m scripts.xrpl_tools build-account-set --from r9cZA1mLK5R5Am25ArfXFmqgNwjZgnfk59 --transfer-rate 1015000000
```

## Domain Hex Encoding

The CLI accepts a plain domain such as `example.com` and hex-encodes it to uppercase automatically. XRPL stores `Domain` as hex bytes.

Example:

```bash
python3 -m scripts.xrpl_tools build-account-set --from r9cZA1mLK5R5Am25ArfXFmqgNwjZgnfk59 --domain example.com
```

## EmailHash

EmailHash is legacy MD5 email metadata. Prefer domain verification and public TOML metadata for modern projects.

Example:

```bash
python3 -m scripts.xrpl_tools build-account-set --from rACCOUNT --message-key 03ABCD...
```

## MessageKey

MessageKey stores a public key for encrypted messages. Only set it when your wallet or application actually uses it.

Example:

```bash
python3 -m scripts.xrpl_tools build-account-set --from rACCOUNT --message-key 03ABCD...
```

## NFTokenMinter

NFTokenMinter works with `asfAuthorizedNFTokenMinter=10` so another account can mint NFTs on behalf of the issuer.

Example:

```bash
python3 -m scripts.xrpl_tools build-account-set --from rISSUER --nftoken-minter rMINTER
python3 -m scripts.xrpl_tools build-account-set --from rISSUER --set-flag 10
```

## Real Testnet Address Examples

These are syntactically valid XRPL-style addresses used in examples. Verify funding and ownership before signing.

| Role | Address |
|---|---|
| Issuer | `r9cZA1mLK5R5Am25ArfXFmqgNwjZgnfk59` |
| Holder | `rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe` |
| Operational wallet | `rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh` |

### Operational Note 1

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 2

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 3

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 4

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 5

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 6

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 7

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 8

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 9

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 10

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 11

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 12

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 13

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 14

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 15

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 16

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 17

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 18

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 19

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 20

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 21

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 22

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 23

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 24

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 25

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 26

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 27

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 28

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 29

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 30

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 31

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 32

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 33

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 34

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 35

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 36

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 37

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 38

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 39

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 40

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 41

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 42

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 43

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 44

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 45

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 46

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 47

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 48

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 49

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 50

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 51

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 52

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 53

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 54

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 55

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 56

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 57

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 58

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 59

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 60

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 61

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 62

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 63

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 64

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 65

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 66

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 67

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 68

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 69

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 70

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 71

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 72

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 73

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 74

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 75

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 76

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 77

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 78

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 79

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 80

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 81

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 82

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 83

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 84

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

### Operational Note 85

- Build AccountSet JSON offline and inspect every field before signing.
- Submit only after the account has enough XRP for base reserve, owner reserve, and transaction fee.
- For issuer accounts, document why each flag was enabled and whether it can be cleared later.

## Related Files

- [21-token-model](knowledge/21-xrpl-token-model.md)
- [22-token-issuance](knowledge/22-xrpl-token-issuance.md)
- [07-clawback](knowledge/07-xrpl-clawback.md)
