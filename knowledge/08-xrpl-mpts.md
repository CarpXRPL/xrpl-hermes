# XRPL Multi-Purpose Tokens (MPTokens)

XRPL-Hermes currently ships two unsigned MPT builders:

```bash
xrpl-hermes build-mpt-issuance-create \
  --from rISSUER \
  --asset-scale 6 \
  --maximum-amount 1000000000000 \
  --transfer-fee 100 \
  --flags 0x20

xrpl-hermes build-mpt-authorize \
  --from rACCOUNT \
  --mpt-issuance-id 48_HEX_CHARACTERS
```

The builders check `MPTokensV1` against public XRPL Mainnet feature state and return unsigned JSON. Query the amendment directly when diagnosing status:

```bash
xrpl-hermes amendment MPTokensV1
```

## Issuance creation

`build-mpt-issuance-create` accepts:

- `--asset-scale 0..255`
- `--maximum-amount 1..9223372036854775807`
- `--transfer-fee 0..50000`
- `--flags N`

A transfer fee automatically enables the required transferable flag in the produced intent. Review supply, scale, transferability, locking, freezing, clawback, and authorization policy before external signing; several issuance choices cannot be casually changed after creation.

## Authorization

`build-mpt-authorize` accepts a 48-character hexadecimal issuance ID. The account can authorize itself; issuer-side holder authorization uses `--holder rHOLDER`. Flag `1` requests unauthorization where valid.

## Amount handling

Store and compare raw integer amounts separately from displayed units. `AssetScale` controls display conversion; it does not change the underlying integer.

```text
display amount = raw amount / 10^AssetScale
```

Never infer scale from a symbol or UI label. Read the issuance object from validated ledger state.

## Shipped boundary

XRPL-Hermes does not currently ship MPT issuance-set, destroy, transfer, or balance-query commands. Protocol support for those transaction/object types is not the same as an implemented product capability.

## Safe sequence

1. Use `amendment MPTokensV1` for Mainnet; verify any other target network through its own current endpoint.
2. Build and review unsigned issuance or authorization JSON.
3. Authorize with the user-controlled wallet.
4. Verify `validated: true` with `tx-info`.
5. Read the resulting issuance/holder object through a validated ledger API before updating application state.
